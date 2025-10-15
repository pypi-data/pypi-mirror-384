from logging import Logger
from typing import Literal, Sequence

import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ....utils.constants import CM_AS_INCH, TIME_VAR
from ....utils.read.product.level1.atl_nom_1b import get_depol_profile
from ....utils.time import TimedeltaLike, TimeRangeLike
from ....utils.typing import DistanceRangeLike
from ....utils.xarray_utils import filter_radius, filter_time
from ...figure import (
    CurtainFigure,
    ECKFigure,
    FigureType,
    MapFigure,
    create_multi_figure_layout,
)
from .._cli import print_progress
from .._quicklook_results import QuicklookFigure
from ..set_default_height_range import set_none_height_range_to_default


def ecquicklook_atc(
    ds: xr.Dataset,
    vars: list[str] | None = None,
    show_maps: bool = True,
    show_zoom: bool = False,
    show_profile: bool = False,
    site: str | None = None,
    radius_km: float = 100.0,
    time_range: TimeRangeLike | None = None,
    height_range: DistanceRangeLike | None = (0, 30e3),
    ds_tropopause: xr.Dataset | None = None,
    ds_elevation: xr.Dataset | None = None,
    ds_temperature: xr.Dataset | None = None,
    logger: Logger | None = None,
    log_msg_prefix: str = "",
    selection_max_time_margin: TimedeltaLike | Sequence[TimedeltaLike] | None = None,
    mode: Literal["fast", "exact"] = "fast",
) -> QuicklookFigure:
    _stime: str = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    height_range = set_none_height_range_to_default(height_range, 0, 30e3)

    if ds_elevation is None:
        ds_elevation = ds

    if vars is None:
        vars = [
            "simple_classification",
            "classification_low_resolution",
            "classification_medium_resolution",
            "classification",
        ]

    wspaces: list[float] = []

    if show_maps:
        map_rows = [FigureType.MAP_1_ROW, FigureType.MAP_1_ROW]
        wspaces.append(3.5 * CM_AS_INCH)
    else:
        map_rows = None

    main_rows = [FigureType.CURTAIN for _ in vars]

    if show_zoom:
        zoom_rows = [FigureType.CURTAIN_ZOOMED for _ in vars]
        wspaces.append(6.5 * CM_AS_INCH)
    else:
        zoom_rows = None

    profile_rows = None

    if logger:
        print_progress(f"layout", log_msg_prefix=log_msg_prefix, logger=logger)

    output = create_multi_figure_layout(
        map_rows=map_rows,
        rows=main_rows,
        zoom_rows=zoom_rows,
        profile_rows=profile_rows,
        wspace=wspaces,
    )
    fig = output.fig
    axs_map = output.axs_map
    axs_main = output.axs
    axs_zoom = output.axs_zoom
    axs_profile = output.axs_profile

    map_figs: list[ECKFigure] = []
    main_figs: list[ECKFigure] = []
    zoom_figs: list[ECKFigure] = []

    if show_maps:
        if logger:
            print_progress(f"map globe", log_msg_prefix=log_msg_prefix, logger=logger)
        mf = MapFigure(ax=axs_map[0])
        mf = mf.ecplot(
            ds,
            site=site,
            radius_km=radius_km,
            time_range=time_range,
            selection_max_time_margin=selection_max_time_margin,
        )
        map_figs.append(mf)

        if logger:
            print_progress(f"map zoomed", log_msg_prefix=log_msg_prefix, logger=logger)
        mf = MapFigure(
            ax=axs_map[1],
            style="blue_marble",
            coastlines_resolution="50m",
            show_night_shade=False,
            show_right_labels=False,
            show_top_labels=False,
        )
        mf = mf.ecplot(
            ds,
            site=site,
            radius_km=radius_km,
            time_range=time_range,
            view="overpass",
            selection_max_time_margin=selection_max_time_margin,
        )
        map_figs.append(mf)

    for i, var in enumerate(vars):
        if logger:
            print_progress(
                f"curtain: {var=}", log_msg_prefix=log_msg_prefix, logger=logger
            )
        cf = CurtainFigure(ax=axs_main[i], mode=mode)
        cf = cf.ecplot(
            ds,
            var,
            site=site,
            radius_km=radius_km,
            selection_time_range=time_range,
            height_range=height_range,
            selection_max_time_margin=selection_max_time_margin,
        )
        if ds_tropopause:
            if logger:
                print_progress(
                    f"tropopause", log_msg_prefix=log_msg_prefix, logger=logger
                )
            cf = cf.ecplot_tropopause(ds_tropopause)
        if ds_temperature:
            if logger:
                print_progress(
                    f"temperature", log_msg_prefix=log_msg_prefix, logger=logger
                )
            cf = cf.ecplot_temperature(ds_temperature)

        main_figs.append(cf)

    if show_zoom or show_profile:
        _ds = ds.copy()
        if site:
            _ds = filter_radius(_ds, radius_km=radius_km, site=site)
        elif time_range:
            _ds = filter_time(_ds, time_range)

        if show_zoom:
            _time_range = _ds[TIME_VAR].values[[0, -1]]
            for i, var in enumerate(vars):
                if logger:
                    print_progress(
                        f"{log_msg_prefix}curtain zoomed: {var=} ...",
                        log_msg_prefix=log_msg_prefix,
                        logger=logger,
                    )
                cf = CurtainFigure(
                    ax=axs_zoom[i],
                    num_ticks=4,
                    show_height_left=False,
                    show_height_right=True,
                    mode=mode,
                )
                cf = cf.ecplot(
                    ds,
                    var,
                    colorbar=False,
                    time_range=_time_range,
                    height_range=height_range,
                )
                if ds_tropopause:
                    if logger:
                        print_progress(
                            f"tropopause zoomed",
                            log_msg_prefix=log_msg_prefix,
                            logger=logger,
                        )
                    cf = cf.ecplot_tropopause(ds_tropopause)
                if ds_temperature:
                    if logger:
                        print_progress(
                            f"temperature zoomed",
                            log_msg_prefix=log_msg_prefix,
                            logger=logger,
                        )
                    cf = cf.ecplot_temperature(ds_temperature)

                zoom_figs.append(cf)

    subfigs: list[list[ECKFigure]] = [map_figs, main_figs, zoom_figs]

    _etime: str = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    _dtime: str = str(pd.Timestamp(_etime) - pd.Timestamp(_stime)).split()[-1]
    if logger:
        print_progress(
            f"Plot created (time taken {_dtime}).",
            is_last=True,
            log_msg_prefix=log_msg_prefix,
            logger=logger,
        )

    return QuicklookFigure(fig, subfigs)
