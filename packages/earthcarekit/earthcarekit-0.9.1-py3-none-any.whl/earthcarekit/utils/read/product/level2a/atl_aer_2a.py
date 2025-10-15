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
    ELEVATION_VAR,
    EXT_LABEL,
    LR_LABEL,
    TROPOPAUSE_VAR,
    rename_common_dims_and_vars,
    rename_var_info,
)
from ..file_info import FileAgency
from ..header_group import add_header_and_meta_data
from ..science_group import read_science_data


def read_product_aaer(
    filepath: str,
    modify: bool = DEFAULT_READ_EC_PRODUCT_MODIFY,
    header: bool = DEFAULT_READ_EC_PRODUCT_HEADER,
    meta: bool = DEFAULT_READ_EC_PRODUCT_META,
    **kwargs,
) -> xr.Dataset:
    """Opens ATL_AER_2A file as a `xarray.Dataset`."""
    ds = read_science_data(
        filepath,
        agency=FileAgency.ESA,
        **kwargs,
    )

    if not modify:
        return ds

    ds = rename_common_dims_and_vars(
        ds,
        along_track_dim="along_track",
        vertical_dim="JSG_height",
        track_lat_var="latitude",
        track_lon_var="longitude",
        height_var="height",
        time_var="time",
        tropopause_var="tropopause_height",
        elevation_var="elevation",
    )

    ds = rename_var_info(
        ds,
        f"particle_backscatter_coefficient_355nm",
        name=BSC_LABEL,
        long_name=BSC_LABEL,
    )
    ds = rename_var_info(
        ds,
        f"particle_extinction_coefficient_355nm",
        name=EXT_LABEL,
        long_name=EXT_LABEL,
    )
    ds = rename_var_info(ds, f"lidar_ratio_355nm", name=LR_LABEL, long_name=LR_LABEL)
    ds = rename_var_info(
        ds,
        f"particle_linear_depol_ratio_355nm",
        name=DEPOL_LABEL,
        long_name=DEPOL_LABEL,
        units="-",
    )

    ds = add_header_and_meta_data(filepath=filepath, ds=ds, header=header, meta=meta)

    return ds
