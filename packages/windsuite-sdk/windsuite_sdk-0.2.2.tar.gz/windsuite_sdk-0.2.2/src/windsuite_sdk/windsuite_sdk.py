"""
Represnts the full windsuite object,
This will contain the other user SDKs.


"""

from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Callable
from typing import Protocol

import socketio  # type: ignore[missing stub]
from loguru import logger
from pydantic import ValidationError

from .fan_controller import FanController, Indexed80mmModule, Indexed240mmModule
from .models.windprobe_models import WindProbeData
from .models.windtrack_models import TrackingDataDict


class CallbackWindtrack(Protocol):
    """
    This represents a callback function that the user will provide to handle windtrack data.

    It will be called each time a new windtrack data is received, given the data as argument.

    Args:
        data (TrackingDataDict): A dictionary of tracking data, with the object name as key and the TrackingData as value.

    """

    def __call__(self, data: TrackingDataDict) -> None: ...


class CallbackWindprobe(Protocol):
    """
    This represents a callback function that the user will provide to handle windprobe data.

    It will be called each time a new windprobe data is received, given the data as argument.

    Args:
        data (WindProbeData): The windprobe data received.

    """

    def __call__(self, data: WindProbeData) -> None: ...


class WindsuiteSDK:
    def __init__(
        self,
        base_url: str,
        port_rest_api: int = 8000,
        port_socketio_api: int = 8001,
        machine_size: tuple[int, int],
    ) -> None:
        self.port_rest_api = port_rest_api
        self.port_socketio_api = port_socketio_api
        self.rest_base_url = base_url.rstrip("/") + f":{self.port_rest_api}" + "/api"
        self.socketio_base_url = base_url.rstrip("/") + f":{self.port_socketio_api}"
        self.machine_size = machine_size

        self.__callback_windtrack: CallbackWindtrack | None = None
        self.__callback_windprobe: CallbackWindprobe | None = None
        # self.__callback_all_modules: CallbackModuleData | None = None

        self.fan_controller = FanController(base_url=self.rest_base_url, machine_size=self.machine_size)

        self.stop_event = threading.Event()
        self.__running_threads: list[threading.Thread] = []

    def start_socketio_thread(self) -> None:
        """
        Starts the __socketio_client_routine in a background thread, handling event loop issues.
        """

        def run_socketio() -> None:
            try:
                # ! NOT SUPPORTED ON WINDOWS
                # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
                loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop=loop)
                loop.run_until_complete(future=self.__socketio_client_routine())
            except RuntimeError as e:
                logger.info(f"SocketIO thread exception: {e}")

        t = threading.Thread(target=run_socketio, daemon=True)
        t.name = "socketio_client_thread"
        self.__running_threads.append(t)
        t.start()

    def stop_everything(self) -> None:
        """
        Stops the socketio client and sets the stop event.
        """
        self.stop_event.set()
        for thread in self.__running_threads:
            if thread.is_alive():
                thread.join()

    def create_80mm_module_to_set(
        self,
        index_xy: tuple[int, int],
        pwms_downstream_layer: list[float] | float,
        pwms_upstream_layer: list[float] | float,
    ) -> Indexed80mmModule:
        """
        If a single float is provided for a layer, it will be expanded to all fans in that layer.

        Otherwise, the len HAS to be fans_per_layer.
        """
        return self.fan_controller.create_80mm_module_to_set(
            index_xy=index_xy,
            pwms_downstream_layer=pwms_downstream_layer,
            pwms_upstream_layer=pwms_upstream_layer,
        )

    def create_240mm_module_to_set(
        self,
        index_xy: tuple[int, int],
        pwm: float,
    ) -> Indexed240mmModule:
        return self.fan_controller.create_240mm_module_to_set(
            index_xy=index_xy,
            pwm=pwm,
        )

    def set_fans(self, list_indexed_modules: list[Indexed80mmModule | Indexed240mmModule]) -> None:
        return self.fan_controller.set_fans(list_indexed_modules=list_indexed_modules)

    async def __socketio_client_routine(self) -> None:
        """
        Create a SocketIO client to connect to the Windsuite API.

        Contains the routes that receive from the different events

        This is started in a thread and will run until the stop_event is set
        """
        sio = socketio.AsyncClient()

        @sio.event  # type: ignore[UnknownMemberType], Rationale : type hints of socketio are not strict enough
        async def connect() -> None:  # type: ignore[reportUnusedFunction], Rationale: Event callback, not called directly
            logger.info("Connected to SocketIO server.")

        @sio.event  # type: ignore[UnknownMemberType], Rationale : type hints of socketio are not strict enough
        async def disconnect() -> None:  # type: ignore[reportUnusedFunction], Rationale: Event callback, not called directly
            logger.info("Disconnected from SocketIO server.")

        @sio.event  # type: ignore[UnknownMemberType], Rationale : type hints of socketio are not strict enough
        async def probe_data(data: str) -> None:  # type: ignore[reportUnusedFunction], Rationale: Event callback, not called directly
            # logger.info(f"Received message: {data}")
            try:
                windprobe_data = WindProbeData.model_validate(data)
                if self.__callback_windprobe:
                    self.__callback_windprobe(windprobe_data)
            except ValidationError as e:
                logger.error(f"Validation error: {e}")

        @sio.event  # type: ignore[UnknownMemberType], Rationale : type hints of socketio are not strict enough
        async def tracking_data(data: dict) -> None:  # type: ignore[reportUnusedFunction], Rationale: Event callback, not called directly
            # print(f"Received windtrack data: {data}")
            try:
                windtrack_dict = TrackingDataDict.model_validate(data)
                if self.__callback_windtrack:
                    self.__callback_windtrack(windtrack_dict)
            except ValidationError as e:
                print(f"Validation error: {e}")

        # @sio.event  # type: ignore[UnknownMemberType], Rationale : type hints of socketio are not strict enough
        # async def all_modules(data: str) -> None:  # type: ignore[reportUnusedFunction], Rationale: Event callback, not called directly
        #    # print(f"Received module data: {data}")

        #    if self.__callback_all_modules:
        #        self.__callback_all_modules(data)

        try:
            await sio.connect(  # type: ignore[UnknownMemberType], Rationale : type hints of socketio are not strict enough
                self.socketio_base_url,
                transports=["websocket"],
            )
        except socketio.exceptions.ConnectionError as e:  # type: ignore[UnknownMemberType], Rationale : type hints of socketio are not strict enough
            print(
                f"Socket IO connection error: {e},\nHINT :\n\t- Verify that the server is running\n\t- The URL is correct and\n\t- You're on the same network as the server"
            )
            self.stop_event.set()
            return

        # Wait for stop_event in a non-blocking way and disconnect sio when set
        while not self.stop_event.is_set():  # noqa: ASYNC110, Rationale: honestly, seems to be the best way to do this
            await asyncio.sleep(0.1)
        await sio.disconnect()

    def register_tracking_callback(
        self,
        callback: CallbackWindtrack,
    ) -> None:
        """
        Register a callback for windtrack data.

        Args:
            callback (Callable[[TrackingData], None]): The function to call when windtrack data is received.

        """
        if not callable(callback):
            raise TypeError("Callback must be a callable function.")

        self.__callback_windtrack = callback

    def register_windprobe_callback(
        self,
        callback: CallbackWindprobe,
    ) -> None:
        """
        Register a callback for windprobe data.

        Args:
            callback (CallbackWindprobe): The function to call when windprobe data is received.

        """
        if not callable(callback):
            raise TypeError("Callback must be a callable function.")

        self.__callback_windprobe = callback

    def main_loop_manager(
        self,
        main_function: Callable[..., None],
        loop_frequency_hz: float,
    ) -> None:
        """
        Utility function that will call the given function at the given frequency until stop flag is set.

        This is given to users of the SDK, so they don't have to implement their own loop.

        This has the advantage of being cleanly stoppable with Ctrl+C and will stop all the SDK background stuff properly

        ! Don't use delays or blocking calls in the main_function, as this will block the loop.

        Args:
            main_function (callable): The function to run in the loop.
            loop_frequency_hz (float): Frequency in Hz to run the main_function.

        """
        try:
            period = 1.0 / loop_frequency_hz
            remaining = period

            while not self.stop_event.wait(timeout=remaining):
                start_ns = time.monotonic_ns()

                main_function()

                elapsed_ns = time.monotonic_ns() - start_ns
                remaining = max(0, period - (elapsed_ns / 1e9))

        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self.stop_everything()


if __name__ == "__main__":
    pass
