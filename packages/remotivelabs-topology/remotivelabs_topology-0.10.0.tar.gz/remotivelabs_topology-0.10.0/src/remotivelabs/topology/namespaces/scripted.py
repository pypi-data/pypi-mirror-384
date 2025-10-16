from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import AsyncIterator, Union

from remotivelabs.broker import (
    BrokerClient,
    Frame,
    FrameInfo,
    FrameSubscription,
    NamespaceName,
    Signal,
    SignalInfo,
    SignalName,
)
from typing_extensions import Self

from remotivelabs.topology.namespaces.filters import AllFramesFilter, FrameFilter, ReceiverFilter, SenderFilter, SignalFilter
from remotivelabs.topology.namespaces.input_handlers import FrameHandler, InputHandler
from remotivelabs.topology.namespaces.namespace import Namespace


class ScriptedNamespace(
    Namespace[Union[SenderFilter, ReceiverFilter, FrameFilter, AllFramesFilter, SignalFilter], Callable[[Frame], Awaitable[None]]]
):
    """
    ScriptedNamespace provides access to frames that have been transformed by scripts in the broker.
    """

    def __init__(
        self,
        name: NamespaceName,
        broker_client: BrokerClient,
        decode_named_values: bool = False,
    ):
        """
        Initialize the scripted namespace client.

        Args:
            name: The namespace name to operate in.
            broker_client: The client used to communicate with the broker.
            decode_named_values: True will decode named values to str.

        Note:
            Use together with a `BehavioralModel` or start the instance using a context manager:
            ```python
            async with ScriptedNamespace(...) as broker_client:
                ...
            ```
        """
        super().__init__(name=name, broker_client=broker_client)
        self._decode_named_values = decode_named_values

    async def open(self) -> Self:
        """
        Open the namespace.
        This is an idempotent operation - calling it multiple times has no additional effect.

        Returns:
            The namespace

        Raises:
            ValueError: If the namespace is not of type 'scripted'.
        """
        if self._opened:
            return self

        ns = await self._broker_client.get_namespace(self.name)
        if ns is None or ns.type != "scripted":
            raise ValueError(f"Namespace '{self.name}' is missing or not of type 'scripted'")

        return await super().open()

    async def close(self) -> None:
        """
        Will close the namespace.
        This is an idempotent operation - calling it multiple times has no additional effect.
        """
        await super().close()

    async def list_frame_infos(self) -> list[FrameInfo]:
        """Return all available frame infos in the namespace."""
        return await self._broker_client.list_frame_infos(self.name)

    async def get_frame_info(self, name: str) -> FrameInfo | None:
        """Return information about a specific frame by name."""
        return await self._broker_client.get_frame_info(name, namespace=self.name)

    async def list_signal_infos(self) -> list[SignalInfo]:
        """Return all available signal infos in the namespace."""
        return await self._broker_client.list_signal_infos(self.name)

    async def get_signal_info(self, name: SignalName) -> SignalInfo | None:
        """Return information about a specific signal by name."""
        return await self._broker_client.get_signal_info(name, namespace=self.name)

    async def subscribe(self, *name: SignalName, on_change: bool = False) -> AsyncIterator[list[Signal]]:
        """
        Subscribe to a list of signals.

        Args:
            *signals:
                One or more signals to subscribe to.
            on_change: Whether to receive updates only on change.

        Note: does not support decoding enums

        Returns:
            An asynchronous iterator of lists of Signal objects.
        """
        return await self._broker_client.subscribe((self.name, list(name)), on_change=on_change)

    async def subscribe_frames(
        self,
        *frames: FrameSubscription,
        on_change: bool = False,
        initial_empty: bool = False,
        decode_named_values: bool = False,
    ) -> AsyncIterator[Frame]:
        """
        Subscribe to a Frames.

        Args:
            *frames: One or more frames to subscribe to.
            on_change: Whether to receive updates only on change.
            initial_empty: True will wait until the broker has sent an initial message
            decode_named_values: True will decode named values to str.

        Returns:
            An asynchronous iterator with Frames.
        """
        return await self._broker_client.subscribe_frames(
            (self.name, list(frames)), on_change=on_change, initial_empty=initial_empty, decode_named_values=decode_named_values
        )

    def create_input_handler(
        self,
        filters: Sequence[Union[SenderFilter, ReceiverFilter, FrameFilter, AllFramesFilter, SignalFilter]],
        callback: Callable[[Frame], Awaitable[None]],
    ) -> tuple[NamespaceName, InputHandler]:
        """
        Creates a list of input handlers for the given namespace to be used with a `BehavioralModel`.

        Each handler defines a filter and a corresponding async callback for processing matching frames.

        Args:
            - filters: A sequence of filter objects to select relevant frames or signals.
            - callback: An async callback function that receives and processes a Frame.
        """
        return (self.name, FrameHandler(filters=filters, cb=callback, decode_named_values=self._decode_named_values))
