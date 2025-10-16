from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import AsyncIterator

from remotivelabs.broker import BrokerClient, Frame, NamespaceName
from typing_extensions import Self

from remotivelabs.topology.namespaces.generic import GenericNamespace
from remotivelabs.topology.namespaces.input_handlers import InputHandler
from remotivelabs.topology.namespaces.namespace import Namespace


class NamespaceClient:
    """
    A NamespaceClient is used to interact with one or more namespaces on RemotiveBroker.

    It manages lifecycle operations for namespaces (e.g., `CanNamespace`, `SomeIPNamespace`) and handles inputs.
    """

    _broker_client: BrokerClient
    _sub_task: asyncio.Task | None
    _namespaces: dict[NamespaceName, Namespace]
    _input_handlers: dict[NamespaceName, list[InputHandler]]

    def __init__(
        self,
        broker_client: BrokerClient,
        namespaces: list[Namespace] | None = None,
        input_handlers: list[tuple[NamespaceName, InputHandler]] | None = None,
    ):
        """
        Initialize the NamespaceClient instance.

        Args:
            broker_client: The client used for communication with the broker.
            namespaces: list of Namespace instances (`CanNamespace`, `SomeIPNamespace`, etc.).
            input_handlers: Optional list of (namespace, handler list) pairs to receive
                                            callbacks on inputs.
                                            It is advised to create these using the namespace's
                                            `create_input_handler` method.

        Note:
            Start the instance using a context manager:
                ```python
                async with NamespaceClient(...) as client:
                    ...
                    await client.run_forever()
                ```
            Or use the start/stop methods directly:
                ```python
                client = NamespaceClient(...)
                await client.start()
                # ...
                await client.stop()
                ```
        """
        self._broker_client = broker_client
        self._namespaces = {ns.name: ns for ns in namespaces or []}
        self._input_handlers: dict[NamespaceName, list[InputHandler]] = defaultdict(list)
        for k, v in input_handlers or []:
            self._input_handlers[k].append(v)

        self._sub_task = None

    def is_running(self) -> bool:
        """Has the NamespaceClient been started?"""
        return self._sub_task is not None

    async def start(self) -> None:
        """
        Start the NamespaceClient, open all namespaces, and initialize input handlers.
        This is an idempotent operation - calling it multiple times has no additional effect.
        """
        if self.is_running():
            return

        for namespace in self._namespaces.values():
            await namespace.open()

        sub = await self._subscribe_with_handler()
        self._sub_task = asyncio.create_task(self._run_loop(sub))
        await self._broker_client.restbus.start(*(ns.name for ns in self._namespaces.values() if isinstance(ns, GenericNamespace)))

    async def stop(self) -> None:
        """
        Stop the NamespaceClient, close all namespaces, and clean up resources.
        This is an idempotent operation - calling it multiple times has no additional effect.
        """
        if self._sub_task is None:
            return

        self._sub_task.cancel()
        for namespace in self._namespaces.values():
            await namespace.close()

        self._sub_task = None

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.stop()

    async def run_forever(self) -> None:
        """Run the NamespaceClient indefinitely, processing inputs."""
        if self._sub_task is None:
            raise RuntimeError("Must be started before calling run_forever")

        await self._sub_task

    async def _run_loop(self, sub: AsyncIterator[Frame] | None) -> None:
        if sub is None:
            return

        async for frame in sub:
            handlers = self._input_handlers[frame.namespace]
            for handler in handlers:
                if (resp := await handler.handle(frame)) is not None:
                    await self._broker_client.publish(resp)

    async def _subscribe_with_handler(self) -> AsyncIterator[Frame] | None:
        for namespace_name, handlers in self._input_handlers.items():
            frames = await self._broker_client.list_frame_infos(namespace_name)
            for handler in handlers:
                for frame_info in frames:
                    handler.add(frame_info)
                if len(handler.subscriptions()) == 0:
                    raise ValueError(f"Input handler {handler} did not yield any subscriptions on namespace '{namespace_name}'")

        subs = []
        for namespace_name, handlers in self._input_handlers.items():
            for handler in handlers:
                subs.append((namespace_name, handler.subscriptions()))

        if not subs:
            return None

        return await self._broker_client.subscribe_frames(
            *subs,
            on_change=False,
            initial_empty=True,
        )

    async def reset_restbuses(self) -> None:
        """Reset all restbus data for all namespaces."""
        for namespace in self._namespaces.values():
            if isinstance(namespace, GenericNamespace):
                await namespace.restbus.reset()
