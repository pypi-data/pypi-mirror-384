import numpy as np
import xarray as xr
from xarray import Dataset


def pad_dataset(ds: Dataset, target_sizes: dict, int_fill: int = -9999) -> Dataset:
    """Pad a dataset to match target sizes along all relevant dimensions."""
    padded_vars = {}
    for name, var in ds.data_vars.items():
        pad_width = []
        for dim in var.dims:
            current = ds.sizes.get(dim, 0)
            target = target_sizes.get(dim, current)
            pad = (0, target - current) if target > current else (0, 0)
            pad_width.append(pad)

        if not pad_width:
            continue  # Skip scalar variables

        fill_value: int | float
        if np.issubdtype(var.dtype, np.integer):
            if np.iinfo(var.dtype).min <= int_fill:
                fill_value = int_fill
            else:
                fill_value = np.iinfo(var.dtype).min
        else:
            fill_value = np.nan

        padded_values = np.pad(var.values, pad_width, constant_values=fill_value)
        padded_vars[name] = xr.DataArray(padded_values, dims=var.dims, attrs=var.attrs)

    return Dataset(padded_vars, attrs=ds.attrs)


def concat_datasets(ds1: Dataset, ds2: Dataset, dim: str) -> Dataset:
    """Concatenate two `xarray.Dataset` objects along a specified dimension, padding other dimensions to match.

    Pads all non-concatenation dimensions in both datasets to the maximum size among them
    (if they differ) before concatenating. Integer variables are padded with -9999 or data
    type-specific minimum value (e.g., -128 for int8), non-interger variables are padded with NaN.

    Args:
        ds1 (Dataset): The first dataset to concatenate.
        ds2 (Dataset): The second dataset to concatenate.
        dim (str): The name of the dimension to concatenate along.

    Returns:
        Dataset: A new dataset resulting from the concatenation.
    """

    def get_scalars(ds: xr.Dataset) -> list:
        scalars = [k for k, v in ds.data_vars.items() if v.ndim == 0]
        return scalars

    ds1_scalars = get_scalars(ds1)
    ds2_scalars = get_scalars(ds2)
    scalar_vars: list = list(set(ds1_scalars + ds2_scalars))

    scalar_data: dict = {v: [] for v in scalar_vars}
    for v in scalar_vars:
        if v in ds1:
            scalar_data[v].extend(np.atleast_1d(ds1[v].values))
        if v in ds2:
            scalar_data[v].extend(np.atleast_1d(ds2[v].values))

    max_dim_sizes = {
        d: max(ds1.sizes.get(d, 0), ds2.sizes.get(d, 0))
        for d in set(ds1.dims).union(ds2.dims)
        if d != dim
    }

    ds1_padded = pad_dataset(ds1, max_dim_sizes)
    ds2_padded = pad_dataset(ds2, max_dim_sizes)

    ds_combined = xr.concat([ds1_padded, ds2_padded], dim=dim)

    if "concat_dim" in ds_combined.dims:
        ds_combined = ds_combined.drop_dims("concat_dim", errors="ignore")

    for v in scalar_vars:
        da = xr.DataArray(scalar_data[v], dims=["concat_dim"])
        ds_combined[v] = da

    source1 = ds1.encoding.get("source")
    source2 = ds2.encoding.get("source")
    sources = [s for s in [source1, source2] if isinstance(s, str)]

    if len(sources) > 0:
        ds_combined.encoding["sources"] = sources

    return ds_combined
