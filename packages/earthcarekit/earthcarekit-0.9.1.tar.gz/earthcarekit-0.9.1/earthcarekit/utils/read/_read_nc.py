import logging

import xarray as xr


def demote_coordinate_dimension(
    ds: xr.Dataset,
    var: str,
    new_dim_name: str,
) -> xr.Dataset:
    """Converts a coordinate to a variable and renames the related dimension."""
    if var in ds.coords:
        values = ds.coords[var].values
        _tmp_var = "tmp_var____"
        ds = ds.assign({_tmp_var: (var, values)})
        ds[_tmp_var] = ds[_tmp_var].assign_attrs(ds[var].attrs)
        ds = ds.drop_vars([var])
        ds = ds.rename({var: new_dim_name})
        ds = ds.rename_vars({_tmp_var: var})
    return ds


def _read_nc(
    filepath: str,
    modify: bool = True,
    **kwargs,
) -> xr.Dataset:
    """Returns an `xarray.Dataset` from a NetCDF file path.

    Args:
        filepath (str): Path to a NetCDF file.
        modify (bool): If True, default modifications to the opened dataset will be applied
            (e.g., converting heights in Polly data from height a.g.l. to height above mean sea level).
        **kwargs: Key-word arguments passed to `xarray.open_dataset()`.

    Returns:
        xarray.Dataset: The resulting dataset.

    Note:
        this function is basically a wrapper for the `xarray.open_dataset()` function.
    """

    logger = logging.getLogger()

    ds = xr.open_dataset(filepath, **kwargs)

    if modify:
        ds = demote_coordinate_dimension(ds, "time", "temporal")
        ds = demote_coordinate_dimension(ds, "height", "vertical")

        for var in ds.variables:
            units_attr: str | None = None
            if hasattr(ds[var], "units"):
                units_attr = "units"
            elif hasattr(ds[var], "unit"):
                units_attr = "unit"

            if isinstance(units_attr, str):
                units = ds[var].attrs[units_attr].lower()
                if "seconds" in units and "since" in units and "1970-01-01" in units:
                    ds[var].values = ds[var].values.astype("datetime64[s]")
                    ds[var].attrs[units_attr] = ""

        if (
            "altitude" in ds
            and "height" in ds
            and ds["altitude"].values.size == 1
            and ds["height"].values.size > 1
        ):
            logger.info(f"Convert height above ground level to height above ellipsoid.")
            ds["height_above_ground"] = ds["height"].copy()
            ds["height"].values = (
                ds["height_above_ground"].values + ds["altitude"].values
            )
            ds["height"] = ds["height"].assign_attrs(
                long_name="Height above mean sea level"
            )

    return ds


def read_nc(
    input: str | xr.Dataset,
    modify: bool = True,
    in_memory: bool = False,
    **kwargs,
) -> xr.Dataset:
    """Returns an `xarray.Dataset` from a Dataset or NetCDF file path, optionally loaded into memory.

    Args:
        input (xarray.Dataset or str): Path to a NetCDF file. If a already opened `xarray.Dataset` object is passed, it is returned as is.
        modify (bool): If True, default modifications to the opened dataset will be applied
            (e.g., converting heights in Polly data from height a.g.l. to height above mean sea level).
        in_memory (bool, optional): If True, ensures the dataset is fully loaded into memory. Defaults to False.
        **kwargs: Key-word arguments passed to `xarray.open_dataset()`.

    Returns:
        xarray.Dataset: The resulting dataset.

    Raises:
        TypeError: If input is not a Dataset or string.
    """
    ds: xr.Dataset
    if isinstance(input, xr.Dataset):
        ds = input
    elif isinstance(input, str):
        if in_memory:
            with _read_nc(input, modify=modify, **kwargs) as ds:
                ds = ds.load()
        else:
            ds = _read_nc(input, modify=modify, **kwargs)
    else:
        raise TypeError(
            f"Invalid input type! Expecting a opened NetCDF dataset (xarray.Dataset) or a path to a NetCDF file."
        )
    return ds
