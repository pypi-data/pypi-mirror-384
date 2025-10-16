from typing import Self

from pyautd3 import Controller, SenderOption
from pyautd3.driver.link import Link
from pyautd3.native_methods.autd3capi_driver import ControllerPtr, GeometryPtr, LinkPtr
from pyautd3.native_methods.utils import _validate_status
from pyautd3.utils import Duration

from pyautd3_emulator.native_methods.autd3capi_emulator import NativeMethods as Emu


class RecorderLink(Link):
    def __init__(self: Self) -> None:
        super().__init__()

    def _resolve(self: Self) -> LinkPtr:
        err = "Not implemented"  # pragma: no cover
        raise NotImplementedError(err)  # pragma: no cover

    def tick(self: Self, tick: Duration) -> None:
        _validate_status(
            Emu().emulator_tick_ns(self._ptr, tick._inner),
        )


class Recorder(Controller[RecorderLink]):
    def __init__(self: Self, geometry: GeometryPtr, ptr: ControllerPtr) -> None:
        super().__init__(geometry, ptr, RecorderLink(), SenderOption())

    def tick(self: Self, tick: Duration) -> None:
        self._link.tick(tick)
