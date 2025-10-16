import ctypes
from typing import Self

import numpy as np
import polars as pl
from pyautd3.native_methods.utils import _validate_status
from pyautd3.utils import Duration

from pyautd3_emulator.native_methods.autd3capi_emulator import NativeMethods as Emu
from pyautd3_emulator.native_methods.autd3capi_emulator import RmsPtr
from pyautd3_emulator.native_methods.autd3capi_emulator import RmsRecordOption as RmsRecordOption_


class RmsRecordOption:
    _inner: RmsRecordOption_

    def __init__(
        self: Self,
        *,
        sound_speed: float = 340e3,
    ) -> None:
        self._inner = RmsRecordOption_(
            sound_speed,
        )


class Rms:
    _ptr: RmsPtr

    def __init__(self: Self, ptr: RmsPtr) -> None:
        self._ptr = ptr

    def __del__(self: Self) -> None:
        self._dispose()

    def _dispose(self: Self) -> None:
        if self._ptr.value is not None:  # pragma: no cover
            Emu().emulator_sound_field_rms_free(self._ptr)
            self._ptr.value = None

    def skip(self: Self, duration: Duration) -> Self:
        _validate_status(Emu().emulator_sound_field_rms_skip(self._ptr, duration._inner))
        return self

    def observe_points(self: Self) -> pl.DataFrame:
        points_len = int(Emu().emulator_sound_field_rms_points_len(self._ptr))
        x = np.zeros(points_len, dtype=np.float32)
        y = np.zeros(points_len, dtype=np.float32)
        z = np.zeros(points_len, dtype=np.float32)
        Emu().emulator_sound_field_rms_get_x(self._ptr, x.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))  # type: ignore[arg-type]
        Emu().emulator_sound_field_rms_get_y(self._ptr, y.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))  # type: ignore[arg-type]
        Emu().emulator_sound_field_rms_get_z(self._ptr, z.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))  # type: ignore[arg-type]
        return pl.DataFrame(
            {
                "x[mm]": x,
                "y[mm]": y,
                "z[mm]": z,
            },
        )

    def next(self: Self, duration: Duration) -> pl.DataFrame:
        n = int(Emu().emulator_sound_field_rms_time_len(self._ptr, duration._inner))
        points_len = int(Emu().emulator_sound_field_rms_points_len(self._ptr))
        time = np.zeros(n, dtype=np.uint64)

        v = np.zeros([n, points_len], dtype=np.float32)
        _validate_status(
            Emu().emulator_sound_field_rms_next(
                self._ptr,
                duration._inner,
                time.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)),  # type: ignore[arg-type]
                ctypes.cast(
                    (ctypes.POINTER(ctypes.c_float) * n)(
                        *(ctypes.cast(r, ctypes.POINTER(ctypes.c_float)) for r in np.ctypeslib.as_ctypes(v)),  # type: ignore[arg-type]
                    ),
                    ctypes.POINTER(ctypes.POINTER(ctypes.c_float)),
                ),  # type: ignore[arg-type]
            ),
        )
        return pl.DataFrame(
            {s.name: s for s in (pl.Series(name=f"rms[Pa]@{time[i]}[ns]", values=v[i]) for i in range(n))},
        )
