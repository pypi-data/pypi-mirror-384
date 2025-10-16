from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from remotivelabs.broker import BrokerClient, NamespaceName
from typing_extensions import Self

from remotivelabs.topology.control.handler import Handler, Router
from remotivelabs.topology.control.request import ControlRequest
from remotivelabs.topology.control.response import ControlResponse
from remotivelabs.topology.control.server import ControlServer
from remotivelabs.topology.namespaces.input_handlers import InputHandler
from remotivelabs.topology.namespaces.namespace import Namespace
from remotivelabs.topology.namespaces.namespace_client import NamespaceClient
from remotivelabs.topology.version import __version__

_logger = logging.getLogger(__name__)


@dataclass
class PingRequest(ControlRequest):
    """
    Control request to check if the `BehavioralModel` is alive and responsive.

    Use `remotivelabs.topology.control.ControlClient` to send control requests.
    """

    type: str = "ping_v1"


@dataclass
class RebootRequest(ControlRequest):
    """
    Control request to reset all namespace restbus to default values.

    Use `remotivelabs.topology.control.ControlClient` to send control requests.
    """

    type: str = "reboot_v1"


@dataclass
class BehavioralModelStartError(Exception):
    """Raised when a behavioral model fails to start."""

    name: str

    def __str__(self) -> str:
        return f"Behavioral model '{self.name}' failed to start."


class BehavioralModel:
    """
    A BehavioralModel is used to emulate some behavior instead of a real ECU.

    It manages lifecycle operations for namespaces (e.g., `CanNamespace`, `SomeIPNamespace`), handles inputs,
    routes control requests, and provides a unified interface for testing setups.
    """

    _control_router: Router

    _control_server: ControlServer
    _control_server_task: asyncio.Task | None
    _namespace_client: NamespaceClient
    _name: str

    def __init__(
        self,
        name: str,
        broker_client: BrokerClient,
        namespaces: list[Namespace] | None = None,
        input_handlers: list[tuple[NamespaceName, InputHandler]] | None = None,
        control_handlers: list[tuple[str, Handler]] | None = None,
    ):
        """
        Initialize the BehavioralModel instance.

        Args:
            name: Identifier for the ECU stub instance, then name which receives control messages.
            broker_client: The client used for communication with the broker.
            namespaces: list of Namespace instances (`CanNamespace`, `SomeIPNamespace`, etc.).
            input_handlers: Optional list of (namespace, handler list) pairs to receive
                                            callbacks on inputs.
                                            It is advised to create these using the namespace's
                                            `create_input_handler` method.
            control_handlers: Optional list of (command, handler) pairs for routing control messages.

        Note:
            Start the instance using a context manager:
                ```python
                async with BehavioralModel(...) as bm:
                    ...
                    await bm.run_forever()
                ```
            Or use the start/stop methods directly:
                ```python
                bm = BehavioralModel(...)
                await bm.start()
                # ...
                await bm.stop()
                ```
        """
        self._namespace_client = NamespaceClient(broker_client, namespaces, input_handlers)
        self._name = name

        router = Router(
            fallback_handler=Router(
                [
                    (str(PingRequest.type), self._ping_v1),
                    (str(RebootRequest.type), self._reboot_v1),
                ]
            )
        )
        router.add_routes(control_handlers or [])
        self._control_server = ControlServer(name=name, broker_client=broker_client, handler=router)
        self._control_server_task = None

        _logger.info(f"BehavioralModel {self._name} using broker at {broker_client.url}")

    def is_running(self) -> bool:
        """Has the BehavioralModel been started?"""
        return self._namespace_client.is_running()

    async def start(self) -> None:
        """
        Start the behavioral model, open all namespaces, and initialize input handlers.
        This is an idempotent operation - calling it multiple times has no additional effect.
        """
        if self.is_running():
            return

        try:
            ready_event = asyncio.get_running_loop().create_future()
            self._control_server_task = asyncio.create_task(self._control_server.serve_forever(ready_event))
            await ready_event

            await self._namespace_client.start()
            _logger.debug(f"BehavioralModel '{self._name}' opened using: {__version__}")
        except Exception as e:
            if self._control_server_task is not None and self._control_server_task.done():
                self._control_server_task.cancel()
            raise BehavioralModelStartError(name=self._name) from e

    async def stop(self) -> None:
        """
        Stop the behavioral model, close all namespaces, and clean up resources.
        This is an idempotent operation - calling it multiple times has no additional effect.
        """
        if not self.is_running():
            return

        await self._namespace_client.stop()

        if self._control_server_task is not None:
            self._control_server_task.cancel()

        self._control_server_task = None
        _logger.debug(f"BehavioralModel '{self._name}' closed")

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.stop()

    async def run_forever(self) -> None:
        """Run the BehavioralModel indefinitely, processing inputs and control requests."""
        if not self.is_running() or self._control_server_task is None:
            raise RuntimeError("BehavioralModel must be started before calling run_forever")

        _logger.debug(f"BehavioralModel '{self._name}' running")
        await asyncio.gather(self._namespace_client.run_forever(), self._control_server_task)

    async def reset_restbuses(self) -> None:
        """Reset all restbus data for all namespaces."""
        await self._namespace_client.reset_restbuses()

    # Control request handlers
    async def _ping_v1(self, request: ControlRequest) -> ControlResponse:  # noqa: ARG002
        return ControlResponse(status="ok", data=None)

    async def _reboot_v1(self, request: ControlRequest) -> ControlResponse:  # noqa: ARG002
        await self.reset_restbuses()
        return ControlResponse(status="ok", data=None)
