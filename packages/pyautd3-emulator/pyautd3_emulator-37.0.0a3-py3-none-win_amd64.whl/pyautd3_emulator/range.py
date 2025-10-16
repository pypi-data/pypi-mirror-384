from typing import Self

from pyautd3_emulator.native_methods.autd3capi_emulator import RangeXYZ as RangeXYZ_


class RangeXYZ:
    _inner: RangeXYZ_

    def __init__(
        self: Self,
        *,
        x: tuple[float, float],
        y: tuple[float, float],
        z: tuple[float, float],
        resolution: float,
    ) -> None:
        self._inner = RangeXYZ_(
            x_start=x[0],
            x_end=x[1],
            y_start=y[0],
            y_end=y[1],
            z_start=z[0],
            z_end=z[1],
            resolution=resolution,
        )
