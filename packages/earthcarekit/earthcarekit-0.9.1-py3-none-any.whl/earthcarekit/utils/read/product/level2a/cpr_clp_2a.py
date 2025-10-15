import xarray as xr

from ....constants import (
    DEFAULT_READ_EC_PRODUCT_HEADER,
    DEFAULT_READ_EC_PRODUCT_META,
    DEFAULT_READ_EC_PRODUCT_MODIFY,
)
from ....xarray_utils import merge_datasets
from .._rename_dataset_content import (
    BSC_LABEL,
    DEPOL_LABEL,
    EXT_LABEL,
    LR_LABEL,
    rename_common_dims_and_vars,
    rename_var_info,
)
from ..file_info import FileAgency
from ..header_group import add_header_and_meta_data
from ..science_group import read_science_data


def read_product_cclp(
    filepath: str,
    modify: bool = DEFAULT_READ_EC_PRODUCT_MODIFY,
    header: bool = DEFAULT_READ_EC_PRODUCT_HEADER,
    meta: bool = DEFAULT_READ_EC_PRODUCT_META,
    **kwargs,
) -> xr.Dataset:
    """Opens CPR_CLP_2A file as a `xarray.Dataset`."""
    ds = read_science_data(
        filepath,
        agency=FileAgency.JAXA,
        **kwargs,
    )

    if not modify:
        return ds

    # Combine same dimensions
    ds = ds.squeeze()  # Removes dimensions of size 1
    ds = ds.rename({"phony_dim_7": "phony_dim_4"})
    ds = ds.rename({"phony_dim_6": "phony_dim_3"})

    # Rename content
    ds = rename_common_dims_and_vars(
        ds,
        along_track_dim="phony_dim_3",
        vertical_dim="phony_dim_4",
        track_lat_var="latitude",
        track_lon_var="longitude",
        height_var="height",
        time_var="time",
        elevation_var="surface_elevation",
        temperature_var="GRID_temperature_1km",
    )

    ds = add_header_and_meta_data(filepath=filepath, ds=ds, header=header, meta=meta)

    return ds
