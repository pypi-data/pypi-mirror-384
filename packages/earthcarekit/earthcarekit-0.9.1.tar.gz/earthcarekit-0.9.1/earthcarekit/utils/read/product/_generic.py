import os

import numpy as np
from xarray import Dataset

from ...constants import (
    DEFAULT_READ_EC_PRODUCT_HEADER,
    DEFAULT_READ_EC_PRODUCT_META,
    DEFAULT_READ_EC_PRODUCT_MODIFY,
)
from ...xarray_utils import merge_datasets
from ._trim_to_frame import trim_to_latitude_frame_bounds
from .auxiliary import read_product_xmet
from .file_info import FileType
from .header_group import add_header_and_meta_data
from .level1 import read_product_anom, read_product_cnom, read_product_mrgr
from .level2a import (
    read_product_aaer,
    read_product_aald,
    read_product_acla,
    read_product_acth,
    read_product_aebd,
    read_product_afm,
    read_product_aice,
    read_product_atc,
    read_product_ccd,
    read_product_ccld,
    read_product_cclp,
    read_product_ceco,
    read_product_cfmr,
    read_product_ctc,
    read_product_mcm,
    read_product_mcop,
)
from .level2b import (
    read_product_acmcap,
    read_product_actc,
    read_product_amacd,
    read_product_amcth,
)


def _read_auxiliary_product(
    filepath: str,
    file_type: FileType,
    modify: bool,
    header: bool,
    meta: bool,
) -> Dataset | None:
    args: list = [filepath, modify, header, meta]
    match file_type:
        case FileType.AUX_MET_1D:
            return read_product_xmet(*args)
        case _:
            return None


def _read_level1_product(
    filepath: str,
    file_type: FileType,
    modify: bool,
    header: bool,
    meta: bool,
    **kwargs,
) -> Dataset | None:
    args: list = [filepath, modify, header, meta]
    match file_type:
        case FileType.ATL_NOM_1B:
            return read_product_anom(*args, **kwargs)
        case FileType.MSI_RGR_1C:
            return read_product_mrgr(*args, **kwargs)
        case FileType.CPR_NOM_1B:
            return read_product_cnom(*args, **kwargs)
        case _:
            return None


def _read_level2a_product(
    filepath: str,
    file_type: FileType,
    modify: bool,
    header: bool,
    meta: bool,
    **kwargs,
) -> Dataset | None:
    args: list = [filepath, modify, header, meta]
    match file_type:
        case FileType.ATL_AER_2A:
            return read_product_aaer(*args, **kwargs)
        case FileType.ATL_EBD_2A:
            return read_product_aebd(*args, **kwargs)
        case FileType.ATL_TC__2A:
            return read_product_atc(*args, **kwargs)
        case FileType.ATL_CLA_2A:
            return read_product_acla(*args, **kwargs)
        case FileType.ATL_CTH_2A:
            return read_product_acth(*args, **kwargs)
        case FileType.ATL_ALD_2A:
            return read_product_aald(*args, **kwargs)
        case FileType.ATL_ICE_2A:
            return read_product_aice(*args, **kwargs)
        case FileType.ATL_FM__2A:
            return read_product_afm(*args, **kwargs)
        case FileType.MSI_CM__2A:
            return read_product_mcm(*args, **kwargs)
        case FileType.MSI_COP_2A:
            return read_product_mcop(*args, **kwargs)
        case FileType.CPR_TC__2A:
            return read_product_ctc(*args, **kwargs)
        case FileType.CPR_CLD_2A:
            return read_product_ccld(*args, **kwargs)
        case FileType.CPR_FMR_2A:
            return read_product_cfmr(*args, **kwargs)
        case FileType.CPR_CD__2A:
            return read_product_ccd(*args, **kwargs)
        case FileType.CPR_CLP_2A:
            return read_product_cclp(*args, **kwargs)
        case FileType.CPR_ECO_2A:
            return read_product_ceco(*args, **kwargs)
        case _:
            return None


def _read_level2b_product(
    filepath: str,
    file_type: FileType,
    modify: bool,
    header: bool,
    meta: bool,
    **kwargs,
) -> Dataset | None:
    args: list = [filepath, modify, header, meta]
    match file_type:
        case FileType.AM__ACD_2B:
            return read_product_amacd(*args, **kwargs)
        case FileType.AM__CTH_2B:
            return read_product_amcth(*args, **kwargs)
        case FileType.AC__TC__2B:
            return read_product_actc(*args, **kwargs)
        case FileType.ACM_CAP_2B:
            return read_product_acmcap(*args, **kwargs)
        case _:
            return None


def _read_product(
    filepath: str,
    trim_to_frame: bool = True,
    modify: bool = DEFAULT_READ_EC_PRODUCT_MODIFY,
    header: bool = DEFAULT_READ_EC_PRODUCT_HEADER,
    meta: bool = DEFAULT_READ_EC_PRODUCT_META,
    **kwargs,
) -> Dataset:
    """Loads an EarthCARE product file as an `xarray.Dataset`.

    Args:
        filepath (str): Path to the product file.
        trim_to_frame (bool, optional): Whether to trim the dataset to latitude frame bounds. Defaults to True.
        modify (bool): If True, default modifications to the opened dataset will be applied
            (e.g., renaming dimension corresponding to height to "vertical"). Defaults to True.
        header (bool): If True, all header data will be included in the dataframe. Defaults to False.
        meta (bool): If True, select meta data from header (like orbit number and frame ID) will be included in the dataframe. Defaults to True.

    Returns:
        xarray.Dataset: Loaded (and optionally trimmed) dataset.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No product found under path: {filepath}")

    file_type = FileType.from_input(filepath)

    args: list = [
        filepath,
        file_type,
        modify,
        False,  # header will be read later
        False,  # meta data will be read later
    ]

    ds = _read_level1_product(*args, **kwargs)
    if not isinstance(ds, Dataset):
        ds = _read_level2a_product(*args, **kwargs)
    if not isinstance(ds, Dataset):
        ds = _read_level2b_product(*args, **kwargs)
    if not isinstance(ds, Dataset):
        trim_to_frame = False
        ds = _read_auxiliary_product(*args, **kwargs)
    if not isinstance(ds, Dataset):
        raise NotImplementedError(f"Product '{file_type}' not yet supported.")

    if modify and trim_to_frame:
        ds = trim_to_latitude_frame_bounds(ds)

    ds = add_header_and_meta_data(filepath, ds, header, meta)

    return ds


def read_product(
    input: str | Dataset,
    trim_to_frame: bool = True,
    modify: bool = DEFAULT_READ_EC_PRODUCT_MODIFY,
    header: bool = DEFAULT_READ_EC_PRODUCT_HEADER,
    meta: bool = DEFAULT_READ_EC_PRODUCT_META,
    in_memory: bool = False,
    **kwargs,
) -> Dataset:
    """Returns an `xarray.Dataset` from a Dataset or EarthCARE file path, optionally loaded into memory.

    Args:
        input (str or xarray.Dataset): Path to a EarthCARE file. If a `xarray.Dataset` is given it will be returned as is.
        trim_to_frame (bool, optional): Whether to trim the dataset to latitude frame bounds. Defaults to True.
        modify (bool): If True, default modifications to the opened dataset will be applied
            (e.g., renaming dimension corresponding to height to "vertical"). Defaults to True.
        header (bool): If True, all header data will be included in the dataframe. Defaults to False.
        meta (bool): If True, select meta data from header (like orbit number and frame ID) will be included in the dataframe. Defaults to True.
        in_memory (bool, optional): If True, ensures the dataset is fully loaded into memory. Defaults to False.

    Returns:
        xarray.Dataset: The resulting dataset.

    Raises:
        TypeError: If input is not a Dataset or string.
    """
    ds: Dataset
    if isinstance(input, Dataset):
        ds = input
    elif isinstance(input, str):
        if in_memory:
            with _read_product(
                filepath=input,
                trim_to_frame=trim_to_frame,
                modify=modify,
                header=header,
                meta=meta,
                **kwargs,
            ) as ds:
                ds = ds.load()
        else:
            ds = _read_product(
                filepath=input,
                trim_to_frame=trim_to_frame,
                modify=modify,
                header=header,
                meta=meta,
                **kwargs,
            )
    else:
        raise TypeError(
            f"Invalid input type! Expecting a opened EarthCARE dataset (xarray.Dataset) or a path to a EarthCARE product."
        )
    return ds
