import ctypes
from typing import Self

import numpy as np
import polars as pl
from pyautd3.native_methods.utils import _validate_ptr

from pyautd3_emulator.instant import Instant, InstantRecordOption
from pyautd3_emulator.native_methods.autd3capi_emulator import NativeMethods as Emu
from pyautd3_emulator.native_methods.autd3capi_emulator import RecordPtr
from pyautd3_emulator.range import RangeXYZ
from pyautd3_emulator.rms import Rms, RmsRecordOption


class Record:
    _ptr: RecordPtr

    def __init__(self: Self, ptr: RecordPtr) -> None:
        self._ptr = ptr

    def __del__(self: Self) -> None:
        self._dispose()

    def _dispose(self: Self) -> None:
        if self._ptr.value is not None:  # pragma: no cover
            Emu().emulator_record_free(self._ptr)
            self._ptr.value = None

    def phase(self: Self) -> pl.DataFrame:
        cols = int(Emu().emulator_record_drive_cols(self._ptr))
        rows = int(Emu().emulator_record_drive_rows(self._ptr))
        time = np.zeros(cols, dtype=np.uint64)
        v = np.zeros([cols, rows], dtype=np.uint8)
        Emu().emulator_record_phase(
            self._ptr,
            time.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)),  # type: ignore[arg-type]
            ctypes.cast(
                (ctypes.POINTER(ctypes.c_uint8) * cols)(
                    *(ctypes.cast(r, ctypes.POINTER(ctypes.c_uint8)) for r in np.ctypeslib.as_ctypes(v)),  # type: ignore[arg-type]
                ),
                ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
            ),
        )
        return pl.DataFrame({s.name: s for s in (pl.Series(name=f"phase@{time[i]}[ns]", values=v[i]) for i in range(cols))})

    def pulse_width(self: Self) -> pl.DataFrame:
        cols = int(Emu().emulator_record_drive_cols(self._ptr))
        rows = int(Emu().emulator_record_drive_rows(self._ptr))
        time = np.zeros(cols, dtype=np.uint64)
        v = np.zeros([cols, rows], dtype=np.uint16)
        Emu().emulator_record_pulse_width(
            self._ptr,
            time.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)),  # type: ignore[arg-type]
            ctypes.cast(
                (ctypes.POINTER(ctypes.c_uint16) * cols)(
                    *(ctypes.cast(r, ctypes.POINTER(ctypes.c_uint16)) for r in np.ctypeslib.as_ctypes(v)),  # type: ignore[arg-type]
                ),
                ctypes.POINTER(ctypes.POINTER(ctypes.c_uint16)),
            ),
        )
        return pl.DataFrame({s.name: s for s in (pl.Series(name=f"pulse_width@{time[i]}[ns]", values=v[i]) for i in range(cols))})

    def output_voltage(self: Self) -> pl.DataFrame:
        cols = int(Emu().emulator_record_output_cols(self._ptr))
        rows = int(Emu().emulator_record_drive_rows(self._ptr))
        v = np.zeros([cols, rows], dtype=np.float32)
        Emu().emulator_record_output_voltage(
            self._ptr,
            ctypes.cast(
                (ctypes.POINTER(ctypes.c_float) * cols)(
                    *(ctypes.cast(r, ctypes.POINTER(ctypes.c_float)) for r in np.ctypeslib.as_ctypes(v)),  # type: ignore[arg-type]
                ),
                ctypes.POINTER(ctypes.POINTER(ctypes.c_float)),
            ),
        )
        return pl.DataFrame({s.name: s for s in (pl.Series(name=f"voltage[V]@{i}[25us/512]", values=v[i]) for i in range(cols))})

    def output_ultrasound(self: Self) -> pl.DataFrame:
        cols = int(Emu().emulator_record_output_cols(self._ptr))
        rows = int(Emu().emulator_record_drive_rows(self._ptr))
        v = np.zeros([cols, rows], dtype=np.float32)
        Emu().emulator_record_output_ultrasound(
            self._ptr,
            ctypes.cast(
                (ctypes.POINTER(ctypes.c_float) * cols)(
                    *(ctypes.cast(r, ctypes.POINTER(ctypes.c_float)) for r in np.ctypeslib.as_ctypes(v)),  # type: ignore[arg-type]
                ),
                ctypes.POINTER(ctypes.POINTER(ctypes.c_float)),
            ),
        )
        return pl.DataFrame({s.name: s for s in (pl.Series(name=f"p[a.u.]@{i}[25us/512]", values=v[i]) for i in range(cols))})

    def sound_field(self: Self, range_: RangeXYZ, option: InstantRecordOption | RmsRecordOption) -> Instant | Rms:
        match option:
            case InstantRecordOption():
                return Instant(
                    _validate_ptr(
                        Emu().emulator_sound_field_instant(self._ptr, range_._inner, option._inner),
                    ),
                )
            case RmsRecordOption():  # pragma: no cover
                return Rms(
                    _validate_ptr(
                        Emu().emulator_sound_field_rms(self._ptr, range_._inner, option._inner),
                    ),
                )
