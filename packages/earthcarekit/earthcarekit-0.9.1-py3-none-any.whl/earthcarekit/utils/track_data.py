import warnings
from dataclasses import asdict, dataclass
from typing import Iterable, Literal, Tuple, TypeAlias

import numpy as np
import pandas as pd
import xarray as xr
from numpy.typing import ArrayLike, NDArray

from .constants import ACROSS_TRACK_DISTANCE, FROM_TRACK_DISTANCE
from .rolling_mean import rolling_mean_2d
from .swath_data.across_track_distance import add_across_track_distance
from .time import TimeRangeLike, TimestampLike, to_timestamps, validate_time_range


@dataclass
class SwathData:
    values: NDArray
    latitude: NDArray
    longitude: NDArray
    nadir_index: int
    time: NDArray | None = None
    color: str | None = None
    label: str | None = None
    units: str | None = None
    platform: str | None = None

    def __post_init__(self):

        self.latitude = np.atleast_2d(self.latitude)
        self.longitude = np.atleast_2d(self.longitude)
        if isinstance(self.time, Iterable):
            self.time = pd.to_datetime(np.asarray(self.time)).to_numpy()

        if len(self.values.shape) == 2:
            if self.values.shape[0] != self.latitude.shape[0]:
                raise ValueError(
                    f"along_track dimension must match for `values` {self.values.shape} and `latitude` {self.latitude.shape}"
                )
            if self.values.shape[0] != self.longitude.shape[0]:
                raise ValueError(
                    f"along_track dimension must match for `values` {self.values.shape} and `longitude` {self.longitude.shape}"
                )
            value_dims = ("along_track", "cross_track")
        elif len(self.values.shape) == 3:
            if self.values.shape[1] != self.latitude.shape[0]:
                raise ValueError(
                    f"along_track dimension must match for `values` {self.values.shape} and `latitude` {self.latitude.shape}"
                )
            if self.values.shape[1] != self.longitude.shape[0]:
                raise ValueError(
                    f"along_track dimension must match for `values` {self.values.shape} and `longitude` {self.longitude.shape}"
                )
            value_dims = ("cross_track", "along_track", "rbg")
        else:
            raise ValueError(
                f"`values` but have 2 or 3 dims, but got {self.values.shape}"
            )

        if self.latitude.shape != self.longitude.shape:
            raise ValueError(
                f"`latitude` {self.latitude.shape} and `longitude` {self.longitude.shape} must have same shape"
            )

        ds = xr.Dataset(
            data_vars={
                "values": (value_dims, self.values),
                "time": (("along_track"), self.time),
                "latitude": (("along_track", "cross_track"), self.latitude),
                "longitude": (("along_track", "cross_track"), self.longitude),
            }
        )
        ds = add_across_track_distance(ds, self.nadir_index, "latitude", "longitude")
        self.across_track_distance = ds[ACROSS_TRACK_DISTANCE].values
        self.from_track_distance = ds[FROM_TRACK_DISTANCE].values

    @property
    def shape(self):
        return self.values.shape

    def select_time_range(
        self,
        time_range: TimeRangeLike | None,
    ) -> "SwathData":
        """Retruns only data within the specified `time_range`."""
        if not isinstance(self.time, np.ndarray):
            raise ValueError(
                f"{SwathData.__name__}.{self.select_time_range.__name__}() missing `time` data"
            )
        if time_range is None:
            return self

        time_range = validate_time_range(time_range)

        times = to_timestamps(self.time)
        mask = np.logical_and(time_range[0] <= times, times <= time_range[1])

        sel_values = self.values[mask]
        sel_time = self.time[mask]
        sel_latitude = self.latitude[mask]
        sel_longitude = self.longitude[mask]

        return SwathData(
            values=sel_values,
            time=sel_time,
            latitude=sel_latitude,
            longitude=sel_longitude,
            nadir_index=self.nadir_index,
            color=self.color,
            label=self.label,
            units=self.units,
            platform=self.platform,
        )
