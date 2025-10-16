import ctypes
from collections.abc import Callable, Iterable
from types import TracebackType
from typing import Self

import numpy as np
import polars as pl
from pyautd3.driver.autd3_device import AUTD3
from pyautd3.driver.geometry.geometry import Geometry
from pyautd3.ethercat.dc_sys_time import DcSysTime
from pyautd3.native_methods.autd3 import DcSysTime as _DcSysTime
from pyautd3.native_methods.autd3capi import ControllerPtr
from pyautd3.native_methods.autd3capi import NativeMethods as Base
from pyautd3.native_methods.structs import Point3, Quaternion
from pyautd3.native_methods.utils import _validate_ptr

from pyautd3_emulator.native_methods.autd3capi_emulator import EmulatorPtr
from pyautd3_emulator.native_methods.autd3capi_emulator import NativeMethods as Emu
from pyautd3_emulator.record import Record
from pyautd3_emulator.recorder import Recorder


class Emulator(Geometry):
    _ptr: EmulatorPtr

    def __init__(self: Self, devices: Iterable[AUTD3]) -> None:
        devices = list(devices)
        pos = np.fromiter((np.void(Point3(d.pos)) for d in devices), dtype=Point3)  # type: ignore[type-var,call-overload]
        rot = np.fromiter((np.void(Quaternion(d.rot)) for d in devices), dtype=Quaternion)  # type: ignore[type-var,call-overload]
        self._ptr = Emu().emulator(
            pos.ctypes.data_as(ctypes.POINTER(Point3)),  # type: ignore[arg-type]
            rot.ctypes.data_as(ctypes.POINTER(Quaternion)),  # type: ignore[arg-type]
            len(devices),
        )
        super().__init__(Emu().emulator_geometry(self._ptr))

    @property
    def geometry(self: Self) -> Geometry:
        return self

    def transducer_table(self: Self) -> pl.DataFrame:
        n = int(Emu().emulator_transducer_table_rows(self._ptr))
        dev_indices = np.zeros(n, dtype=np.uint16)
        tr_indices = np.zeros(n, dtype=np.uint8)
        x = np.zeros(n, dtype=np.float32)
        y = np.zeros(n, dtype=np.float32)
        z = np.zeros(n, dtype=np.float32)
        nx = np.zeros(n, dtype=np.float32)
        ny = np.zeros(n, dtype=np.float32)
        nz = np.zeros(n, dtype=np.float32)
        Emu().emulator_transducer_table(
            self._ptr,
            dev_indices.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),  # type: ignore[arg-type]
            tr_indices.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),  # type: ignore[arg-type]
            x.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),  # type: ignore[arg-type]
            y.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),  # type: ignore[arg-type]
            z.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),  # type: ignore[arg-type]
            nx.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),  # type: ignore[arg-type]
            ny.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),  # type: ignore[arg-type]
            nz.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),  # type: ignore[arg-type]
        )
        return pl.DataFrame(
            {
                "dev_idx": dev_indices,
                "tr_idx": tr_indices,
                "x[mm]": x,
                "y[mm]": y,
                "z[mm]": z,
                "nx": nx,
                "ny": ny,
                "nz": nz,
            },
        )

    def record(self: Self, f: Callable[[Recorder], None]) -> Record:
        return self.record_from(DcSysTime.__private_new__(_DcSysTime(0)), f)

    def record_from(self: Self, start_time: DcSysTime, f: Callable[[Recorder], None]) -> Record:
        def f_native(ptr: ControllerPtr) -> None:
            geometry = Base().geometry(ptr)
            cnt = Recorder(geometry, ptr)
            f(cnt)
            cnt._disposed = True

        f_native_ = ctypes.CFUNCTYPE(None, ControllerPtr)(f_native)

        return Record(
            _validate_ptr(
                Emu().emulator_record_from(self._ptr, start_time._inner, f_native_),  # type: ignore[arg-type]
            ),
        )

    def __del__(self: Self) -> None:
        self._dispose()

    def _dispose(self: Self) -> None:
        if self._ptr.value is not None:
            Emu().emulator_free(self._ptr)
            self._ptr.value = None

    def __enter__(self: Self) -> Self:
        return self

    def __exit__(
        self: Self,
        _exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        self._dispose()
