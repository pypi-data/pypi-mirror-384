import logging
import math
import warnings
from numbers import Number
from typing import Iterable, Literal, Sequence

logger: logging.Logger = logging.getLogger(__name__)

import cartopy.crs as ccrs  # type: ignore
import cartopy.feature as cfeature  # type: ignore
import cartopy.io.img_tiles as cimgt  # type: ignore
import matplotlib as mpl
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import pandas as pd
import seaborn as sns
import xarray as xr
from cartopy.crs import Projection
from cartopy.feature.nightshade import Nightshade  # type: ignore
from cartopy.mpl.feature_artist import FeatureArtist  # type: ignore
from cartopy.mpl.geoaxes import _ViewClippedPathPatch  # type: ignore
from cartopy.mpl.geoaxes import GeoAxes
from cartopy.mpl.gridliner import Gridliner  # type: ignore
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection
from matplotlib.colorbar import Colorbar
from matplotlib.colors import Colormap, LogNorm, Normalize
from matplotlib.figure import Figure, SubFigure
from matplotlib.image import AxesImage
from matplotlib.offsetbox import AnchoredOffsetbox, AnchoredText
from matplotlib.patches import Rectangle
from matplotlib.text import Text
from numpy.typing import ArrayLike, NDArray
from owslib.wms import WebMapService  # type: ignore

from ...utils import GroundSite, all_in, get_ground_site
from ...utils.constants import *
from ...utils.constants import (
    DEFAULT_COLORBAR_WIDTH,
    FIGURE_MAP_HEIGHT,
    FIGURE_MAP_WIDTH,
)
from ...utils.geo import get_coord_between, get_coords, haversine
from ...utils.geo.bbox import compute_bbox, pad_bbox
from ...utils.geo.coordinates import (
    get_central_coords,
    get_central_latitude,
    get_central_longitude,
)
from ...utils.np_array_utils import (
    circular_nanmean,
    flatten_array,
    isascending,
    ismonotonic,
    normalize,
    wrap_to_interval,
)
from ...utils.overpass import get_overpass_info
from ...utils.time import (
    TimedeltaLike,
    TimeRangeLike,
    TimestampLike,
    time_to_iso,
    to_timedelta,
    to_timestamp,
    to_timestamps,
    validate_time_range,
)
from ...utils.typing import ValueRangeLike, validate_numeric_pair
from ...utils.xarray_utils import filter_radius, filter_time
from ..color import Cmap, Color, ColorLike, get_cmap
from ..save import save_plot
from ..text import add_shade_to_text
from ._ensure_updated_msi_rgb_if_required import ensure_updated_msi_rgb_if_required
from .annotation import (
    add_text,
    add_text_overpass_info,
    add_title_earthcare_frame,
    add_title_earthcare_time,
    format_var_label,
)
from .colorbar import add_colorbar
from .defaults import get_default_cmap, get_default_norm, get_default_rolling_mean


def _get_central_coords_from_projection(
    proj: ccrs.Projection,
) -> tuple[float | None, float | None]:
    """Returns the central latitude and longitude of a Cartopy projection."""
    params = proj.proj4_params
    return params.get("lat_0", None), params.get("lon_0", None)


def add_gray_stock_img(
    ax: GeoAxes,
    cmap: Cmap | str = "gray",
    alpha: float = 0.3,
    vmin: float = 0.0,
    vmax: float = 1.0,
) -> AxesImage:
    img = ax.stock_img()  # type:ignore

    def rgb2gray(rgb):
        return np.dot(rgb[..., :3], [0.2989, 0.5870, 0.1140])

    new_img = rgb2gray(img.get_array())
    new_img = normalize(new_img)
    img.set_visible(False)
    cmap_gray = get_cmap(cmap)
    newcmp = cmap_gray

    origin: Literal["upper", "lower"] | None = "lower"
    # if isinstance(ax.projection, ccrs.PlateCarree):
    #     origin = "upper"

    return ax.imshow(
        new_img,
        origin=origin,
        extent=img.get_extent(),
        transform=ax.projection,  # type:ignore
        cmap=newcmp,
        alpha=alpha,
        vmin=vmin,
        vmax=vmax,
    )


def get_osm_lod(a: ArrayLike, b: ArrayLike) -> int:
    lod = 2
    distance_km = haversine(a, b, units="km")
    if distance_km < 25:
        lod = 12
    elif distance_km < 50:
        lod = 11
    elif distance_km < 100:
        lod = 10
    elif distance_km < 200:
        lod = 9
    elif distance_km < 300:
        lod = 8
    elif distance_km < 500:
        lod = 7
    elif distance_km < 750:
        lod = 6
    elif distance_km < 1250:
        lod = 5
    elif distance_km < 2000:
        lod = 4
    elif distance_km < 5500:
        lod = 3

    logger.debug(f"distance_km={distance_km}, lod={lod}")

    return int(lod)


def get_arrow_style(linewidth):
    return f"simple,head_width={0.3+(linewidth*0.15)},head_length={0.3+(linewidth*0.3)},tail_width=0"


def set_view(
    ax: Axes,
    proj: Projection,
    lats: ArrayLike,
    lons: ArrayLike,
    pad: float = 0.05,
    pad_xmin: float | None = None,
    pad_xmax: float | None = None,
    pad_ymin: float | None = None,
    pad_ymax: float | None = None,
) -> Axes:
    lons = flatten_array(lons)
    lons = np.array([np.nanmin(lons), np.nanmax(lons)])
    lats = flatten_array(lats)
    lats = np.array([np.nanmin(lats), np.nanmax(lats)])

    if pad_xmin is None:
        pad_xmin = pad
    if pad_xmax is None:
        pad_xmax = pad
    if pad_ymin is None:
        pad_ymin = pad
    if pad_ymax is None:
        pad_ymax = pad

    xypoints = proj.transform_points(ccrs.PlateCarree(), lons, lats)
    x = xypoints[:, 0]
    y = xypoints[:, 1]

    xmin = x.min()
    xmax = x.max()
    xd = np.abs(xmax - xmin)
    ymin = y.min()
    ymax = y.max()
    yd = np.abs(ymax - ymin)
    xlim = (xmin - xd * pad_xmin, xmax + xd * pad_xmax)
    ylim = (ymin - yd * pad_ymin, ymax + yd * pad_ymax)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)

    return ax


def _validate_figsize(figsize: tuple[float, float]) -> tuple[float, float]:
    if not isinstance(figsize, Iterable):
        raise TypeError(
            f"invalid type of figsize '{type(figsize).__name__}'. expected tuple of 2 numbers."
        )
    else:
        if len(figsize) != 2:
            raise ValueError(
                f"invalid figsize '{figsize}'. expected tuple of 2 numbers."
            )
        elif not isinstance(figsize[0], Number) or not isinstance(figsize[1], Number):
            raise TypeError(
                f"invalid type of figsize '{type(figsize).__name__}[{type(figsize[0]).__name__}, {type(figsize[1]).__name__}]'. expected tuple of 2 numbers."
            )
        return (figsize[0], figsize[1])


def _ensure_figure_and_main_axis(
    ax: Axes | None, figsize: tuple[float, float] | None = None, dpi: int | None = None
) -> tuple[Figure, Axes]:
    fig: Figure
    if isinstance(ax, Axes):
        fig = ax.get_figure()  # type: ignore
        if not isinstance(fig, (Figure, SubFigure)):
            raise ValueError(f"Invalid Figure")
    else:
        fig = plt.figure(figsize=figsize, dpi=dpi)
        ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
    return fig, ax


def _validate_projection(
    projection: Literal["platecarree", "perspective", "orthographic"] | ccrs.Projection,
) -> tuple[type, float | None, float | None]:
    projection_type: type = ccrs.Projection
    central_latitude: float | None = None
    central_longitude: float | None = None
    if isinstance(projection, ccrs.Projection):
        projection_type = type(projection)
        central_coords = _get_central_coords_from_projection(projection)
        central_longitude = central_coords[0]
        central_latitude = central_coords[1]
    elif isinstance(projection, str):
        if projection.lower() == "platecarree":
            projection_type = ccrs.PlateCarree
        elif projection.lower() == "perspective":
            projection_type = ccrs.NearsidePerspective
        elif projection.lower() == "orthographic":
            projection_type = ccrs.Orthographic
        elif projection.lower() == "oblique_mercator":
            projection_type = ccrs.ObliqueMercator
        elif projection.lower() == "stereographic":
            projection_type = ccrs.Stereographic
        else:
            raise TypeError(
                f'Invalid projection: "{projection}"". Expected "platecarree", "perspective", "orthographic" or a instance of cartopy.crs.Projection'
            )

    return (projection_type, central_latitude, central_longitude)


def _validate_pad(pad: float | Iterable) -> list:
    if isinstance(pad, (float, int)):
        return [float(pad), float(pad), float(pad), float(pad)]
    elif isinstance(pad, Iterable):
        pad = list(pad)
        if len(pad) == 4:
            return [pad[0], pad[1], pad[2], pad[3]]
        else:
            raise ValueError(
                f"pad has too few elements ({len(pad)}). expected 4 elements: [pad_xmin, pad_xmax, pad_ymin, pad_ymax] or a single 'float' number"
            )
    raise TypeError(
        f"invalid type for pad '{type(pad).__name__}'. valid types are 'float' and 'list'."
    )


class MapFigure:
    """Figure object for displaying EarthCARE satellite track and/or imager swaths on a global map.

    This class sets up a georeferenced map canvas using a range of cartographic projections and visual styles.
    It serves as the basis for plotting 2D swath data (e.g., from MSI) or simple satellite tracks, optionally
    with info labels, backgrounds, and other styling options.

    Args:
        ax (Axes | None, optional): Existing matplotlib axes to plot on; if not provided, new axes will be created. Defaults to None.
        figsize (tuple[float, float], optional): Figure size in inches. Defaults to (FIGURE_MAP_WIDTH, FIGURE_MAP_HEIGHT).
        dpi (int | None, optional): Resolution of the figure in dots per inch. Defaults to None.
        title (str | None, optional): Title to display on the map. Defaults to None.
        style (str, optional): Base map style to use; options include "none", "stock_img", "gray", "osm", "satellite", "mtg", "msg". Defaults to "gray".
        projection (str | Projection, optional): Map projection to use; options include "platecarree", "perspective", "orthographic", or a custom `cartopy.crs.Projection`. Defaults to `ccrs.Orthographic()`.
        central_latitude (float | None, optional): Latitude at the center of the projection. Defaults to None.
        central_longitude (float | None, optional): Longitude at the center of the projection. Defaults to None.
        grid_color (ColorLike | None, optional): Color of grid lines. Defaults to None.
        border_color (ColorLike | None, optional): Color of border box around the map. Defaults to None.
        coastline_color (ColorLike | None, optional): Color of coastlines. Defaults to None.
        show_grid (bool, optional): Whether to show latitude/longitude grid lines. Defaults to True.
        show_top_labels (bool, optional): Whether to show tick labels on the top axis. Defaults to True.
        show_bottom_labels (bool, optional): Whether to show tick labels on the bottom axis. Defaults to True.
        show_right_labels (bool, optional): Whether to show tick labels on the right axis. Defaults to True.
        show_left_labels (bool, optional): Whether to show tick labels on the left axis. Defaults to True.
        show_text_time (bool, optional): Whether to display a datetime info text above the plot. Defaults to True.
        show_text_frame (bool, optional): Whether to display a EarthCARE frame info text above the plot. Defaults to True.
        show_text_overpass (bool, optional): Whether to display ground site overpass info in the plot. Defaults to True.
        show_night_shade (bool, optional): Whether to overlay the nighttime shading based on `timestamp`. Defaults to True.
        timestamp (TimestampLike | None, optional): Time reference used for nightshade overlay. Defaults to None.
        extent (Iterable | None, optional): Map extent given as [lon_min, lon_max, lat_min, lat_max]; overrides auto zoom. Defaults to None.
        lod (int, optional): Level of detail for coastlines and grid elements; higher values reduce complexity. Defaults to 2.
        coastlines_resolution (str, optional): Resolution of coastlines to display; options are "10m", "50m", or "110m". Defaults to "110m".
        azimuth (float, optional): Rotation of the `cartopy.crs.ObliqueMercator` projection, in degrees (if used). Defaults to 0.
        pad (float | list[float], optional): Padding applied when selecting a map extent. Defaults to 0.05.
        background_alpha (float, optional): Transparency level of the background map style. Defaults to 1.0.
    """

    def __init__(
        self,
        ax: Axes | None = None,
        figsize: tuple[float, float] = (FIGURE_MAP_WIDTH, FIGURE_MAP_HEIGHT),
        dpi: int | None = None,
        title: str | None = None,
        style: (
            str
            | Literal[
                "none",
                "stock_img",
                "gray",
                "osm",
                "satellite",
                "mtg",
                "msg",
                "blue_marble",
            ]
        ) = "gray",
        projection: (
            Literal["platecarree", "perspective", "orthographic"] | ccrs.Projection
        ) = ccrs.Orthographic(),
        central_latitude: float | ArrayLike | None = None,
        central_longitude: float | ArrayLike | None = None,
        grid_color: ColorLike | None = None,
        border_color: ColorLike | None = None,
        coastline_color: ColorLike | None = None,
        show_grid: bool = True,
        show_grid_labels: bool = True,
        show_geo_labels: bool = True,
        show_top_labels: bool = True,
        show_bottom_labels: bool = True,
        show_right_labels: bool = True,
        show_left_labels: bool = True,
        show_text_time: bool = True,
        show_text_frame: bool = True,
        show_text_overpass: bool = True,
        show_night_shade: bool = True,
        timestamp: TimestampLike | None = None,
        extent: Iterable | None = None,
        lod: int = 2,
        coastlines_resolution: Literal["10m", "50m", "110m"] = "110m",
        azimuth: float = 0,
        pad: float | list[float] = 0.05,
        background_alpha: float = 1.0,
        colorbar_tick_scale: float | None = None,
        fig_height_scale: float = 1.0,
        fig_width_scale: float = 1.0,
    ):
        figsize = (figsize[0] * fig_width_scale, figsize[1] * fig_height_scale)
        self.figsize = _validate_figsize(figsize)
        self.fig, self.ax = _ensure_figure_and_main_axis(ax, figsize=figsize, dpi=dpi)

        self.dpi = dpi
        self.title = title
        self.style = style
        self.grid_color = Color.from_optional(grid_color)
        self.border_color = Color.from_optional(border_color)
        self.coastline_color = Color.from_optional(coastline_color)
        self.show_grid = show_grid
        self.show_grid_labels = show_grid_labels
        self.show_geo_labels = show_grid_labels and show_geo_labels
        self.show_top_labels = show_grid_labels and show_top_labels
        self.show_bottom_labels = show_grid_labels and show_bottom_labels
        self.show_right_labels = show_grid_labels and show_right_labels
        self.show_left_labels = show_grid_labels and show_left_labels
        if (
            not self.show_top_labels
            and not self.show_bottom_labels
            and not self.show_right_labels
            and not self.show_left_labels
        ):
            self.show_grid_labels = False
        self.show_text_time = show_text_time
        self.show_text_frame = show_text_frame
        self.show_text_overpass = show_text_overpass
        if timestamp is not None:
            timestamp = to_timestamp(timestamp)
        self.timestamp = timestamp
        self.extent: list | None = None
        if isinstance(extent, Iterable):
            self.extent = list(extent)

        if central_latitude is not None and central_longitude is not None:
            central_latitude, central_longitude = get_central_coords(
                central_latitude, central_longitude
            )
        else:
            if central_latitude is not None:
                central_latitude = get_central_latitude(central_latitude)
            if central_longitude is not None:
                central_longitude = get_central_longitude(central_longitude)
        self.projection_type, clat, clon = _validate_projection(projection)
        self.central_latitude: float | None = central_latitude
        self.central_longitude: float | None = central_longitude
        if central_latitude is None:
            self.central_latitude = clat
        if central_longitude is None:
            self.central_longitude = clon

        self.lod = lod
        self.coastlines_resolution = coastlines_resolution
        self.azimuth = azimuth
        self.colorbar: Colorbar | None = None
        self.colorbar_tick_scale: float | None = colorbar_tick_scale
        self.pad = _validate_pad(pad)
        self.background_alpha = background_alpha

        self.grid_lines: Gridliner | None = None

        self.show_night_shade = show_night_shade

        self._init_axes()

    def set_view(
        self, lats: ArrayLike, lons: ArrayLike, pad: float | Iterable | None = None
    ) -> Axes:
        if isinstance(pad, (float | int | Iterable)):
            self.pad = _validate_pad(pad)
        self.ax = set_view(
            self.ax,
            self.projection,
            lats,
            lons,
            pad_xmin=self.pad[0],
            pad_xmax=self.pad[1],
            pad_ymin=self.pad[2],
            pad_ymax=self.pad[3],
        )
        return self.ax

    def set_extent(
        self, extent: list | None = None, pad: float | Iterable | None = None
    ) -> "MapFigure":
        if isinstance(extent, Iterable):
            self.extent = extent
            self.set_view(
                lons=np.array(self.extent[0:2]),
                lats=np.array(self.extent[2:4]),
                pad=pad,
            )
        return self

    def _init_axes(self) -> None:
        if self.projection_type == ccrs.PlateCarree:
            self.projection = self.projection_type(self.central_longitude)
        elif self.projection_type == ccrs.NearsidePerspective:
            self.projection = self.projection_type(
                central_longitude=self.central_longitude,
                central_latitude=self.central_latitude,
            )
        elif self.projection_type == ccrs.Orthographic:
            self.projection = self.projection_type(
                central_longitude=self.central_longitude,
                central_latitude=self.central_latitude,
            )
        elif self.projection_type == ccrs.ObliqueMercator:
            if self.central_longitude is None:
                self.central_longitude = 0
            if self.central_latitude is None:
                self.central_latitude = 0
            self.projection = self.projection_type(
                central_longitude=self.central_longitude,
                central_latitude=self.central_latitude,
                azimuth=self.azimuth,
            )
        elif self.projection_type == ccrs.Stereographic:
            self.projection = self.projection_type(
                central_longitude=self.central_longitude,
                central_latitude=self.central_latitude,
            )
        else:
            self.projection = self.projection_type()
        self.transform = ccrs.Geodetic()  # ccrs.PlateCarree()

        # making sure axis projection is setup correctly
        if not isinstance(self.ax, Axes):
            self.fig, self.ax = plt.subplots(
                subplot_kw={"projection": self.projection}, figsize=self.figsize
            )
        elif not (
            hasattr(self.ax, "projection")
            and type(self.ax.projection) == type(self.projection)
        ):
            tmp = self.ax.get_figure()
            if not isinstance(tmp, (Figure, SubFigure)):
                raise ValueError(f"Invalid Figure")
            self.fig = tmp  # type: ignore
            self.ax = self.ax

            pos = self.ax.get_position()
            self.ax.remove()
            self.ax = self.fig.add_subplot(pos, projection=self.projection)  # type: ignore

        # self.ax.set_facecolor("white")
        # self.ax.set_facecolor("none")

        if self.title:
            self.fig.suptitle(self.title)

        self.ax.axis("equal")

        # Earth image
        grid_color = Color("#000000")
        coastline_color = Color("#000000")

        if not isinstance(self.style, str):
            raise TypeError(
                f"style has wrong type '{type(self.style).__name__}'. Expected 'str'"
            )
        if self.style == "none":
            pass
        elif self.style == "stock_img":
            img = self.ax.stock_img()  # type: ignore
            grid_color = Color("#3f4d53")
            coastline_color = Color("#537585")
        elif self.style == "gray":
            img = add_gray_stock_img(self.ax)
            grid_color = Color("#6d6d6db3")
            coastline_color = Color("#C0C0C0")
        elif self.style == "osm":
            request = cimgt.OSM()
            img = self.ax.add_image(
                request,
                self.lod,
                interpolation="spline36",
                regrid_shape=2000,
            )  # type: ignore
            grid_color = Color("#6d6d6db3")
            coastline_color = Color("#C0C0C0")
        elif self.style == "satellite":
            request = cimgt.QuadtreeTiles()
            img = self.ax.add_image(
                request,
                self.lod,
                interpolation="spline36",
                regrid_shape=2000,
            )  # type: ignore
            grid_color = Color("#C0C0C099")
            coastline_color = Color("#C0C0C099")
        elif self.style == "blue_marble":

            wms = WebMapService(
                "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?",
                version="1.1.1",
            )
            layer = "BlueMarble_ShadedRelief_Bathymetry"
            self.ax.add_wms(wms, layer)  # type: ignore
            grid_color = Color("#C7C7C799")
            coastline_color = Color("ec:lightblue")

            width, height = 1024, 512
            white_overlay = np.ones((height, width, 4))
            white_overlay[..., 3] = 0.2

            self.ax.imshow(
                white_overlay,
                origin="upper",
                transform=ccrs.PlateCarree(),
            )
        else:
            if not isinstance(self.timestamp, pd.Timestamp):
                msg = f"Missing timestamp for {self.style.upper()} data request for 'https://view.eumetsat.int' (timestamp={self.timestamp})"
                warnings.warn(msg)
            else:
                if self.style == "mtg":
                    if self.timestamp < to_timestamp("2024-09-23T02:00"):
                        self.style = "msg"
                        msg = (
                            f"Switching to MSG since MTG is only available from 2024-09-23 02:00 UTC onwards"
                            f"(timestamp given: {time_to_iso(self.timestamp, format='%Y-%m-%d %H:%M:%S')})"
                        )
                        warnings.warn(msg)
                img = add_gray_stock_img(self.ax)
                grid_color = Color("#3f4d53")
                coastline_color = Color("white").blend(0.5)  # Color("#3f4d53")

                date_str = (
                    pd.Timestamp(self.timestamp, tz="UTC")
                    .round("h")
                    .isoformat()
                    .replace("+00:00", "Z")
                )
                # Connect to NASA GIBS
                url = "https://view.eumetsat.int/geoserver/ows"

                wms = WebMapService(url)
                if self.style == "mtg":
                    layer = "mtg_fd:rgb_geocolour"  # "mtg_fd:ir105_hrfi" #"mumi:worldcloudmap_ir108" #"MODIS_Terra_SurfaceReflectance_Bands143"
                elif self.style == "msg":
                    layer = "msg_fes:rgb_naturalenhncd"
                elif self.style == "nasa":
                    wms = WebMapService(
                        "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?",
                        version="1.1.1",
                    )
                    layer = "MODIS_Terra_CorrectedReflectance_TrueColor"
                elif "nasa:" in self.style:
                    self.style = self.style.replace("nasa:", "")
                    layer = self.style
                    wms = WebMapService(
                        "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?",
                        version="1.1.1",
                    )
                else:
                    layer = self.style
                    # raise NotImplementedError()
                wms_kwargs = {
                    "time": date_str,
                }

                self.ax.add_wms(wms, layer, wms_kwargs=wms_kwargs)  # type: ignore

        # Overlay white transparent layer
        if self.background_alpha < 1.0:
            width, height = 1024, 512
            white_overlay = np.ones((height, width, 4))
            white_overlay[..., 3] = 1 - self.background_alpha

            self.ax.imshow(
                white_overlay,
                origin="upper",
                transform=ccrs.PlateCarree(),
            )
        # else:
        #     raise ValueError(
        #         f'invalid style "{self.style}". Valid styles are: "gray", "osm", "satellite"'
        #     )

        # Grid lines
        _grid_color = self.grid_color
        if _grid_color is None:
            _grid_color = grid_color

        _border_color = self.border_color
        if _border_color is None:
            _border_color = _grid_color

        _coastline_color = self.coastline_color
        if _coastline_color is None:
            _coastline_color = coastline_color

        if self.show_grid:
            self.grid_lines = self.ax.gridlines(draw_labels=True, color=_grid_color, linewidth=0.5, linestyle="dashed")  # type: ignore
            self.grid_lines.geo_labels = self.show_geo_labels
            self.grid_lines.top_labels = self.show_top_labels
            self.grid_lines.bottom_labels = self.show_bottom_labels
            self.grid_lines.right_labels = self.show_right_labels
            self.grid_lines.left_labels = self.show_left_labels
        # self.ax.coastlines(  # type: ignore
        #     color=coastlines_color, resolution=self.coastlines_resolution
        # )  # type: ignore
        self.ax.add_feature(cfeature.COASTLINE.with_scale(self.coastlines_resolution), edgecolor=_coastline_color)  # type: ignore
        # self.ax.add_feature(  # type: ignore
        #     cfeature.BORDERS,
        #     linewidth=0.5,
        #     linestyle="solid",
        #     edgecolor=_coastline_color,
        # )  # type: ignore
        self.ax.spines["geo"].set_edgecolor(_border_color)

        # Night shade
        if self.timestamp is not None:
            self.timestamp = to_timestamp(self.timestamp)
            if self.show_night_shade:
                night_shade_alpha = 0.15
                night_shade_color = Color("#000000")
                self.ax.add_feature(  # type: ignore
                    Nightshade(
                        self.timestamp,
                        alpha=night_shade_alpha,
                        color=night_shade_color,
                        linewidth=0,
                    )
                )  # type: ignore

    def plot_track(
        self,
        latitude: NDArray,
        longitude: NDArray,
        marker: str | None = None,
        markersize: float | int | None = None,
        linestyle: str | None = None,
        linewidth: float | int = 2,
        color: Color | ColorLike | None = None,
        alpha: float | None = 1.0,
        highlight_first: bool = True,
        highlight_first_color: Color | None = None,
        highlight_last: bool = True,
        highlight_last_color: Color | None = None,
        zorder: float = 4,
        z: NDArray | None = None,
        cmap: Cmap | str = "viridis",
        value_range: ValueRangeLike | None = None,
        log_scale: bool | None = None,
        norm: Normalize | None = None,
        show_border: bool = False,
        border_linewidth: float = 1,
        border_color="black",
        colorbar: bool = True,
        colorbar_position: str | Literal["left", "right", "top", "bottom"] = "bottom",
        colorbar_alignment: str | Literal["left", "center", "right"] = "center",
        colorbar_width: float = DEFAULT_COLORBAR_WIDTH,
        colorbar_spacing: float = 0.3,
        colorbar_length_ratio: float | str = "100%",
        colorbar_label_outside: bool = True,
        colorbar_ticks_outside: bool = True,
        colorbar_ticks_both: bool = False,
        label: str = "",
        units: str = "",
        line_overlap: int = 20,
    ) -> "MapFigure":
        latitude = np.asarray(latitude)
        longitude = np.asarray(longitude)

        if z is not None:
            z = np.asarray(z)
            line_overlap = min(line_overlap, int(len(z) * 0.01))
            cmap, value_range, norm = self._init_cmap(
                cmap, value_range, log_scale, norm
            )

            coords = np.column_stack([longitude, latitude])
            segments = [s for s in np.stack([coords[:-1], coords[1:]], axis=1)]
            coords_borders = np.array(
                [coords[0]]
                + [
                    get_coord_between(s[0][::-1], s[1][::-1])[::-1] for s in segments
                ]  # Reverse lon/lat to lat/lon for get_coord_between and back again
                + [coords[-1]] * (line_overlap + 1)
            )
            segments = [
                s for s in np.stack([coords_borders[:-1], coords_borders[1:]], axis=1)
            ]

            def _stack_points(points, line_overlap):
                n_stacks = line_overlap + 2
                return np.stack(
                    [
                        points[i : len(points) - (n_stacks - 1) + i]
                        for i in range(n_stacks)
                    ],
                    axis=1,
                )

            segments = [
                s for s in _stack_points(coords_borders, line_overlap=line_overlap)
            ]
            z_segments = z

            if show_border:
                _l_border = self.ax.plot(
                    coords[:, 0],
                    coords[:, 1],
                    linestyle="solid",
                    linewidth=linewidth + border_linewidth * 2,
                    transform=self.transform,
                    zorder=zorder,
                    color=border_color,
                    solid_capstyle="butt",
                )

            _lc = LineCollection(
                segments,
                cmap=cmap,
                norm=norm,
                linewidth=linewidth,
                transform=self.transform,
                zorder=zorder,
                antialiased=True,
            )
            _lc.set_array(z_segments)
            self.ax.add_collection(_lc)

            if colorbar and not self.colorbar:
                cb_kwargs = dict(
                    label=format_var_label(label, units),
                    position=colorbar_position,
                    alignment=colorbar_alignment,
                    width=colorbar_width,
                    spacing=colorbar_spacing,
                    length_ratio=colorbar_length_ratio,
                    label_outside=colorbar_label_outside,
                    ticks_outside=colorbar_ticks_outside,
                    ticks_both=colorbar_ticks_both,
                )
                self.colorbar = add_colorbar(
                    fig=self.fig,
                    ax=self.ax,
                    data=_lc,
                    cmap=cmap,
                    **cb_kwargs,  # type: ignore
                )
                self.set_colorbar_tick_scale(multiplier=self.colorbar_tick_scale)

            return self

        color = Color.from_optional(color)
        highlight_first_color = Color.from_optional(highlight_first_color)
        highlight_last_color = Color.from_optional(highlight_last_color)

        p = self.ax.plot(
            longitude,
            latitude,
            marker=marker,
            markersize=markersize,
            linestyle=linestyle,
            linewidth=linewidth,
            zorder=zorder,
            transform=self.transform,
            color=color,
            alpha=alpha,
            markeredgewidth=linewidth,
        )
        color = p[0].get_color()  # type: ignore
        if highlight_first_color is None:
            highlight_first_color = color
        if highlight_last_color is None:
            highlight_last_color = color

        if highlight_first:
            self.ax.plot(
                [longitude[0]],
                [latitude[0]],
                marker="o",
                markersize=markersize,
                linestyle="none",
                zorder=zorder if zorder is not None else 4,
                transform=self.transform,
                color=highlight_first_color,
                alpha=alpha,
            )

        if highlight_last:
            tmp_i = 0
            for i in range(len(longitude)):
                if (longitude[-1], latitude[-1]) != (
                    longitude[-2 - i],
                    latitude[-2 - i],
                ):
                    tmp_i = -2 - i
                    break
            arrow_style = get_arrow_style(linewidth)
            self.ax.annotate(
                "",
                xy=(longitude[-1], latitude[-1]),
                xytext=(longitude[tmp_i], latitude[tmp_i]),
                transform=self.transform,
                clip_on=True,
                annotation_clip=True,
                arrowprops=dict(
                    arrowstyle=arrow_style,
                    color=highlight_last_color,
                    lw=linewidth,
                    shrinkA=0,
                    shrinkB=0,
                    alpha=alpha,
                    connectionstyle="arc3,rad=0",
                    mutation_scale=10,
                ),
                zorder=zorder,
            )
        return self

    def plot_text(
        self,
        latitude: int | float,
        longitude: int | float,
        text: str,
        color: Color | ColorLike | None = "black",
        text_side: Literal["left", "right"] = "left",
        zorder: int | float = 8,
        padding: str = "  ",
        rotation: int = 0,
    ) -> "MapFigure":
        if isinstance(text_side, str):
            if text_side == "left":
                horizontalalignment = "right"
                text = f"{text}{padding}"
            elif text_side == "right":
                horizontalalignment = "left"
                text = f"{padding}{text}"
            else:
                raise ValueError(
                    f'got invalid text_side "{text_side}". expected "left" or "right".'
                )
        else:
            raise TypeError(
                f"""invalid type '{type(text_side).__name__}' for text_side. expected type 'str': "left" or "right"."""
            )

        t = self.ax.text(
            longitude,
            latitude,
            text,
            color=color,
            verticalalignment="center",
            horizontalalignment=horizontalalignment,
            transform=self.transform,
            zorder=zorder,
            clip_on=True,
            rotation=rotation,
            rotation_mode="anchor",
        )
        t = add_shade_to_text(t)
        return self

    def plot_point(
        self,
        latitude: int | float,
        longitude: int | float,
        marker: str | None = "D",
        markersize: int | float = 5,
        color: Color | ColorLike | None = "black",
        alpha: float = 1.0,
        edgecolor: Color | ColorLike | None = "white",
        edgealpha: float = 0.8,
        zorder: int | float = 4,
        text: str | None = None,
        text_color: Color | ColorLike | None = "black",
        text_side: Literal["left", "right"] = "right",
        text_zorder: int | float = 8,
        text_padding: str = "  ",
    ) -> "MapFigure":
        _color = Color.from_optional(color, alpha=alpha)
        _edgecolor = Color.from_optional(edgecolor, alpha=edgealpha)
        self.ax.plot(
            [longitude],
            [latitude],
            marker=marker,
            markersize=markersize,
            linestyle="none",
            transform=self.transform,
            color=_color,
            zorder=zorder,
            markerfacecolor=_color,
            markeredgecolor=_edgecolor,
        )
        if isinstance(text, str):
            self.plot_text(
                latitude=latitude,
                longitude=longitude,
                text=text,
                color=text_color,
                text_side=text_side,
                zorder=text_zorder,
                padding=text_padding,
            )
        return self

    def plot_radius(
        self,
        latitude: int | float,
        longitude: int | float,
        radius_km: int | float,
        color: Color | ColorLike | None = "#000000",
        face_color: Color | ColorLike | None = "#FFFFFF00",
        edge_color: Color | ColorLike | None = None,
        text_color: Color | ColorLike | None = None,
        point_color: Color | ColorLike | None = None,
        edge_alpha: float = 0.8,
        text: str | None = None,
        text_side: Literal["left", "right"] = "right",
        marker: str | None = "D",
        zorder: int | float = 4,
        text_zorder: int | float = 8,
    ) -> "MapFigure":
        _color: Color | None = Color.from_optional(color)
        _face_color = Color.from_optional(face_color) or Color("#FFFFFF00")
        _edge_color = Color.from_optional(edge_color) or _color
        _text_color = Color.from_optional(text_color) or Color("#000000")
        _point_color = Color.from_optional(point_color) or _color
        if isinstance(_edge_color, Color):
            _edge_color = _edge_color.set_alpha(edge_alpha)

        # Draw circle
        # TODO: workaround to avoid annoying warnings, need to change this later!
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message="Approximating coordinate system*"
            )
            self.ax.tissot(  # type: ignore
                rad_km=radius_km,
                lons=longitude,
                lats=latitude,
                n_samples=128,
                facecolor=_face_color,
                edgecolor=_edge_color,
                zorder=zorder,
            )  # type: ignore

        # Draw center point
        self.plot_point(
            longitude=longitude,
            latitude=latitude,
            marker=marker,
            markersize=5,
            color=_point_color,
            zorder=zorder,
            text=text,
            text_color=_text_color,
            text_side=text_side,
            text_zorder=text_zorder,
            text_padding="  ",
        )

        return self

    def _plot_overpass(
        self,
        lat_selection: NDArray,
        lon_selection: NDArray,
        lat_total: NDArray,
        lon_total: NDArray,
        site: GroundSite,
        radius_km: int | float,
        site_color: Color | ColorLike | None = "black",
        radius_color: Color | ColorLike | None = None,
        color_selection: Color | ColorLike | None = "ec:earthcare",
        linewidth_selection: float = 3,
        linestyle_selection: str | None = "solid",
        color_total: Color | ColorLike | None = "ec:blue",
        linewidth_total: float = 2.5,
        linestyle_total: str | None = "solid",
        site_text_side: Literal["left", "right"] = "right",
        timestamp: pd.Timestamp | None = None,
        view: Literal["global", "data", "overpass"] = "overpass",
        show_highlights: bool = True,
    ) -> "MapFigure":
        if radius_color is None:
            if self.style in ["satellite", "blue_marble"]:
                radius_color = "white"
            elif self.style in ["gray"]:
                radius_color = "black"

        lat_selection = np.asarray(lat_selection)
        lon_selection = np.asarray(lon_selection)
        lat_total = np.asarray(lat_total)
        lon_total = np.asarray(lon_total)

        site_lat = site.latitude
        site_lon = site.longitude
        site_alt = site.altitude
        site_name = site.name

        self.central_latitude = site_lat
        self.central_longitude = site_lon

        if view == "overpass":
            self.lod = get_osm_lod(
                (lat_selection[0], lon_selection[0]),
                (lat_selection[-1], lon_selection[-1]),
            )
            self.coastlines_resolution = "10m"
        elif view == "data":
            self.lod = get_osm_lod(
                (lat_total[0], lon_total[0]), (lat_total[-1], lon_total[-1])
            )
            self.coastlines_resolution = "50m"
        else:
            self.lod = 2
            self.coastlines_resolution = "110m"

        if timestamp is not None:
            self.timestamp = to_timestamp(timestamp)

        pos = self.ax.get_position()
        self.fig.delaxes(self.ax)
        self.ax = self.fig.add_axes(pos)  # type: ignore
        self._init_axes()

        # FIXME: workaround to avoid annoying warnings, need to change this later!
        warnings.filterwarnings("ignore", message="Approximating coordinate system*")
        self.plot_radius(
            latitude=site_lat,
            longitude=site_lon,
            radius_km=radius_km,
            text=site_name,
            text_side=site_text_side,
            color=radius_color,
            point_color=site_color,
            text_color=site_color,
        )

        highlight_last = False if view == "overpass" else True
        self.plot_track(
            latitude=lat_total,
            longitude=lon_total,
            linewidth=linewidth_total,
            linestyle=linestyle_total,
            highlight_first=show_highlights and False,
            highlight_last=show_highlights and highlight_last,
            color=color_total,
        )
        highlight_first = True if view == "overpass" else False
        highlight_last = True if view == "overpass" else False
        self.plot_track(
            latitude=lat_selection,
            longitude=lon_selection,
            linewidth=linewidth_selection,
            linestyle=linestyle_selection,
            highlight_first=show_highlights and highlight_first,
            highlight_last=show_highlights and highlight_last,
            color=color_selection,
        )

        self.ax.axis("equal")
        # if view == "overpass":
        #     extent = compute_bbox(np.vstack((lat_selection, lon_selection)).T)
        # else:
        #     extent = compute_bbox(np.vstack((lat_total, lon_total)).T)

        if view == "global":
            self.ax.set_global()  # type: ignore
        elif view == "overpass":
            zoom_radius_meters = radius_km * 1e3 * 1.3
            if isinstance(self.projection, ccrs.PlateCarree):
                self.set_view(lats=lat_selection, lons=lon_selection)
            else:
                self.ax.set_xlim(-zoom_radius_meters, zoom_radius_meters)
                self.ax.set_ylim(-zoom_radius_meters, zoom_radius_meters)
        elif view == "data":
            _lats = lat_total
            is_polar_track: bool = not ismonotonic(lat_total)
            if is_polar_track:
                _lats = np.nanmin(_lats)
            if isinstance(self.projection, ccrs.PlateCarree) or not is_polar_track:
                self.set_view(lats=_lats, lons=lon_total)
            else:
                _dist = haversine(
                    (self.central_latitude, self.central_longitude),
                    (lat_total[0], lon_total[0]),
                    units="m",
                )

                _dist2 = haversine(
                    (self.central_latitude, self.central_longitude),
                    (lat_total[-1], lon_total[-1]),
                    units="m",
                )
                _ratio = np.max([(_dist / np.max([_dist2, 1.0])) * 0.5, 1.0])
                print(f"{_ratio=}")

                self.ax.set_xlim(-_dist / _ratio, _dist / _ratio)
                if lat_total[0] < lat_total[1]:
                    self.ax.set_ylim(-_dist / _ratio, _dist)
                else:
                    self.ax.set_ylim(-_dist, _dist / _ratio)

            # zoom_radius_meters = (
            #     haversine(
            #         (lat_total[0], lon_total[0]),
            #         (lat_total[-1], lon_total[-1]),
            #         units="m",
            #     )
            #     * 1.3
            # ) / 2
            # if isinstance(self.projection, ccrs.PlateCarree):
            #     self.set_view(lats=lat_total, lons=lon_total)
            # else:
            #     self.ax.set_xlim(-zoom_radius_meters, zoom_radius_meters)
            #     self.ax.set_ylim(-zoom_radius_meters, zoom_radius_meters)

            # _diameter = haversine(
            #     (lat_total[0], lon_total[0]),
            #     (lat_total[-1], lon_total[-1]),
            #     units="m",
            # )
            # _radius = _diameter / 2
            # zoom_radius_meters = _radius * 1e3 * 1.3
            # if isinstance(self.projection, ccrs.PlateCarree):
            #     self.set_view(lats=lat_total, lons=lon_total)
            # else:
            #     self.ax.set_xlim(-zoom_radius_meters, zoom_radius_meters)
            #     self.ax.set_ylim(-zoom_radius_meters, zoom_radius_meters)

        return self

    def ecplot(
        self,
        ds: xr.Dataset,
        var: str | None = None,
        *,
        lat_var: str = TRACK_LAT_VAR,
        lon_var: str = TRACK_LON_VAR,
        swath_lat_var: str = SWATH_LAT_VAR,
        swath_lon_var: str = SWATH_LON_VAR,
        time_var: str = TIME_VAR,
        along_track_dim: str = ALONG_TRACK_DIM,
        across_track_dim: str = ACROSS_TRACK_DIM,
        site: str | GroundSite | None = None,
        radius_km: float = 100.0,
        time_range: TimeRangeLike | None = None,
        view: Literal["global", "data", "overpass"] = "global",
        zoom_tmin: TimestampLike | None = None,
        zoom_tmax: TimestampLike | None = None,
        color: ColorLike | None = "ec:earthcare",
        linewidth: float = 3,
        linestyle: str | None = "solid",
        color2: ColorLike | None = "ec:blue",
        linewidth2: float | None = None,
        linestyle2: str | None = None,
        cmap: str | Cmap | None = None,
        zoom_radius_km: float | None = None,
        extent: list[float] | None = None,
        central_latitude: float | None = None,
        central_longitude: float | None = None,
        value_range: ValueRangeLike | Literal["default"] | None = "default",
        log_scale: bool | None = None,
        norm: Normalize | None = None,
        colorbar: bool = True,
        pad: float | list[float] | None = None,
        show_text_time: bool | None = None,
        show_text_frame: bool | None = None,
        show_text_overpass: bool | None = None,
        colorbar_position: str | Literal["left", "right", "top", "bottom"] = "bottom",
        colorbar_alignment: str | Literal["left", "center", "right"] = "center",
        colorbar_width: float = DEFAULT_COLORBAR_WIDTH,
        colorbar_spacing: float = 0.3,
        colorbar_length_ratio: float | str = "100%",
        colorbar_label_outside: bool = True,
        colorbar_ticks_outside: bool = True,
        colorbar_ticks_both: bool = False,
        selection_max_time_margin: (
            TimedeltaLike | Sequence[TimedeltaLike] | None
        ) = None,
    ) -> "MapFigure":
        """
        Plot the EarthCARE satellite track on a map, optionally showing a 2D swath variable if `var` is provided.

        This method collects all required data from an EarthCARE `xarray.Dataset`.
        If `var` is given, the corresponding swath variable is plotted on the map using a
        color scale. Otherwise, the satellite ground track is plotted as a colored line.
        If `time_range` or `site` is given, the selected track section within the selected time range or in proximity to ground sites are highlighted.

        Args:
            ds (xr.Dataset): The EarthCARE dataset from which data will be plotted.
            var (str | None, optional): Name of a 2D swath variable to plot. If None, only the satellite ground track is shown. Defaults to None.
            lat_var (str, optional): Name of the latitude variable for the along-track data. Defaults to TRACK_LAT_VAR.
            lon_var (str, optional): Name of the longitude variable for the along-track data. Defaults to TRACK_LON_VAR.
            swath_lat_var (str, optional): Name of the latitude variable for the swath. Defaults to SWATH_LAT_VAR.
            swath_lon_var (str, optional): Name of the longitude variable for the swath. Defaults to SWATH_LON_VAR.
            time_var (str, optional): Name of the time variable. Defaults to TIME_VAR.
            along_track_dim (str, optional): Dimension name representing the along-track direction. Defaults to ALONG_TRACK_DIM.
            across_track_dim (str, optional): Dimension name representing the across-track direction. Defaults to ACROSS_TRACK_DIM.
            site (str | GroundSite | None, optional): Highlights data within `radius_km` of a ground site (given either as a `GroundSite` object or name string); ignored if not set. Defaults to None.
            radius_km (float, optional): Radius around the ground site to highlight data from; ignored if `site` not set. Defaults to 100.0.
            time_range (TimeRangeLike | None, optional): Time range to highlight as selection area; ignored if `site` is set. Defaults to None.
            view (Literal["global", "data", "overpass"], optional): Map extent mode: "global" for full world, "data" for tight bounds, or "overpass" to zoom around `site` or time range. Defaults to "global".
            zoom_tmin (TimestampLike | None, optional): Optional lower time bound used for zooming map around track. Defaults to None.
            zoom_tmax (TimestampLike | None, optional): Optional upper time bound used for zooming map around track. Defaults to None.
            color (ColorLike | None, optional): Color used for selected section of the track or entire track if no selection. Defaults to "ec:earthcare".
            linewidth (float, optional): Line width for selected track section. Defaults to 3.
            linestyle (str | None, optional): Line style for selected track section. Defaults to "solid".
            color2 (ColorLike | None, optional): Color used for unselected sections of the track. Defaults to "ec:blue".
            linewidth2 (float, optional): Line width for unselected sections. Defaults to None.
            linestyle2 (str | None, optional): Line style for unselected sections. Defaults to None.
            cmap (str | Cmap | None, optional): Colormap to use when plotting a swath variable. Defaults to None.
            zoom_radius_km (float | None, optional): If set, overrides map extent derived from `view` to use a fixed radius around the site or selection. Defaults to None.
            extent (list[float] | None, optional): Map extent in the form [lon_min, lon_max, lat_min, lat_max]. If given, overrides map extent derived from `view`. Defaults to None.
            central_latitude (float | None, optional): Central latitude used for the map projection. Defaults to None.
            central_longitude (float | None, optional): Central longitude used for the map projection. Defaults to None.
            value_range (ValueRangeLike | None, optional): Min and max range for the variable values; ignored if `var` is None. Defaults to None.
            log_scale (bool | None, optional): Whether to apply a logarithmic color scale to the variable. Defaults to None.
            norm (Normalize | None, optional): Matplotlib norm to use for color scaling. Defaults to None.
            colorbar (bool, optional): Whether to display a colorbar for the variable. Defaults to True.
            pad (float | list[float] | None, optional): Padding around the map extent; ignored if `extent` is given. Defaults to None.
            show_text_time (bool | None, optional): Whether to display the UTC time start and end of the selected track. Defaults to None.
            show_text_frame (bool | None, optional): Whether to display EarthCARE frame information. Defaults to None.
            show_text_overpass (bool | None, optional): Whether to display overpass site name and related info. Defaults to None.

        Returns:
            MapFigure: The figure object containing the map with track or swath.

        Example:
            ```python
            import earthcarekit as eck

            filepath = "path/to/mydata/ECA_EXAE_ATL_NOM_1B_20250606T132535Z_20250606T150730Z_05813D.h5"
            with eck.read_product(filepath) as ds:
                mf = eck.MapFigure()
                mf = mf.ecplot(ds)
            ```
        """
        if pad is not None:
            self.pad = _validate_pad(pad)
        if show_text_time is not None:
            self.show_text_time = show_text_time
        if show_text_frame is not None:
            self.show_text_frame = show_text_frame
        if show_text_overpass is not None:
            self.show_text_overpass = show_text_overpass

        _lat_var: str = lat_var
        _lon_var: str = lon_var

        _linewidth: float = linewidth
        _linewidth2: float
        if isinstance(linewidth2, (float, int)):
            _linewidth2 = float(linewidth2)
        else:
            _linewidth2 = linewidth * 0.7

        if isinstance(var, str):
            ds = ensure_updated_msi_rgb_if_required(
                ds, var, time_range, time_var=time_var
            )
            _linewidth = linewidth * 0.5
            linestyle = "dashed"
            _linewidth2 = linewidth * 0.2
            if all_in(
                (along_track_dim, across_track_dim), [str(d) for d in ds[var].dims]
            ):
                _lat_var = swath_lat_var
                _lon_var = swath_lon_var

        _site: GroundSite | None = None
        if isinstance(site, GroundSite):
            _site = site
        elif isinstance(site, str):
            _site = get_ground_site(site)

        coords_whole_flight = get_coords(ds, lat_var=lat_var, lon_var=lon_var)

        if time_range is not None:
            if zoom_tmin is None and time_range[0] is not None:
                zoom_tmin = to_timestamp(time_range[0])
            if zoom_tmax is None and time_range[1] is not None:
                zoom_tmax = to_timestamp(time_range[1])
        if zoom_tmin or zoom_tmax:
            ds_zoomed_in = filter_time(ds, time_range=[zoom_tmin, zoom_tmax])
            coords_zoomed_in = get_coords(
                ds_zoomed_in, lat_var=_lat_var, lon_var=_lon_var, flatten=True
            )
            coords_zoomed_in_track = get_coords(
                ds_zoomed_in, lat_var=lat_var, lon_var=lon_var
            )
        else:
            coords_zoomed_in = coords_whole_flight
            coords_zoomed_in_track = get_coords(ds, lat_var=lat_var, lon_var=lon_var)

        is_polar_track: bool = False

        if isinstance(_site, GroundSite):
            ds_overpass = filter_radius(
                ds,
                radius_km=radius_km,
                site=_site,
                lat_var=lat_var,
                lon_var=lon_var,
                along_track_dim=along_track_dim,
            )
            info_overpass = get_overpass_info(
                ds_overpass,
                site_radius_km=radius_km,
                site=_site,
                time_var=time_var,
                lat_var=lat_var,
                lon_var=lon_var,
                along_track_dim=along_track_dim,
            )

            _coords_whole_flight = coords_whole_flight.copy()
            _selection_max_time_margin: tuple[pd.Timedelta, pd.Timedelta] | None = None

            if selection_max_time_margin is not None:
                if isinstance(selection_max_time_margin, str):
                    _selection_max_time_margin = (
                        to_timedelta(selection_max_time_margin),
                        to_timedelta(selection_max_time_margin),
                    )
                elif isinstance(selection_max_time_margin, (Sequence, np.ndarray)):
                    _selection_max_time_margin = (
                        to_timedelta(selection_max_time_margin[0]),
                        to_timedelta(selection_max_time_margin[1]),
                    )
                else:
                    raise ValueError(
                        f"invalid selection_max_time_margin: {selection_max_time_margin}"
                    )

                _ds = filter_time(
                    ds=ds,
                    time_range=(
                        to_timestamp(ds_overpass[time_var].values[0])
                        - _selection_max_time_margin[0],
                        to_timestamp(ds_overpass[time_var].values[1])
                        + _selection_max_time_margin[1],
                    ),
                    time_var=time_var,
                )
                _coords_whole_flight = get_coords(_ds, lat_var=lat_var, lon_var=lon_var)

            coords_overpass = get_coords(ds_overpass, lat_var=lat_var, lon_var=lon_var)
            _ = self._plot_overpass(
                lat_selection=coords_overpass[:, 0],
                lon_selection=coords_overpass[:, 1],
                lat_total=_coords_whole_flight[:, 0],
                lon_total=_coords_whole_flight[:, 1],
                site=_site,
                radius_km=radius_km,
                view=view,
                timestamp=info_overpass.closest_time,
                color_selection=color,
                linewidth_selection=_linewidth,
                linestyle_selection=linestyle,
                color_total=color2,
                linewidth_total=_linewidth2,
                linestyle_total=linestyle2,
                show_highlights=view == "overpass"
                or not isinstance(_selection_max_time_margin, tuple),
                radius_color=None,
            )

            if isinstance(_selection_max_time_margin, tuple):
                self.plot_track(
                    latitude=coords_whole_flight[:, 0],
                    longitude=coords_whole_flight[:, 1],
                    color="white",
                    linestyle="solid",
                    linewidth=2,
                    highlight_first=False,
                    highlight_last=True,
                    zorder=3,
                )

            if view == "overpass":
                if self.show_text_overpass:
                    add_text_overpass_info(self.ax, info_overpass)
            if self.show_text_time:
                add_title_earthcare_time(
                    self.ax, tmin=info_overpass.start_time, tmax=info_overpass.end_time
                )
        else:
            if isinstance(central_latitude, (int, float)):
                self.central_latitude = central_latitude
            else:
                self.central_latitude = np.nanmean(coords_zoomed_in_track[:, 0])
            if isinstance(central_longitude, (int, float)):
                self.central_longitude = central_longitude
            else:
                if not ismonotonic(coords_whole_flight[:, 0]):
                    is_polar_track = True
                    self.central_longitude = coords_whole_flight[-1, 1]
                else:
                    self.central_longitude = circular_nanmean(coords_whole_flight[:, 1])
            logger.debug(
                f"Set central coords to (lat={self.central_latitude}, lon={self.central_longitude})"
            )

            time = ds[time_var].values
            timestamp = time[len(time) // 2]
            self.timestamp = to_timestamp(timestamp)
            if view == "overpass":
                self.lod = get_osm_lod(coords_zoomed_in[0], coords_zoomed_in[-1])
                if extent is None:
                    extent = compute_bbox(coords_zoomed_in)
                    self.extent = extent
            pos = self.ax.get_position()
            self.fig.delaxes(self.ax)
            self.ax = self.fig.add_axes(pos)  # type: ignore
            self._init_axes()
            if time_range is not None:
                _highlight_last = view in ["global", "data"]
                _ = self.plot_track(
                    latitude=coords_whole_flight[:, 0],
                    longitude=coords_whole_flight[:, 1],
                    linewidth=_linewidth2,
                    linestyle=linestyle,
                    highlight_first=False,
                    highlight_last=_highlight_last,
                    color=color2,
                )

                _highlight_last = view == "overpass"
                _ = self.plot_track(
                    latitude=coords_zoomed_in_track[:, 0],
                    longitude=coords_zoomed_in_track[:, 1],
                    linewidth=_linewidth,
                    linestyle=linestyle,
                    highlight_first=False,
                    highlight_last=_highlight_last,
                    color=color,
                )
            else:
                _ = self.plot_track(
                    latitude=coords_whole_flight[:, 0],
                    longitude=coords_whole_flight[:, 1],
                    linewidth=_linewidth,
                    linestyle=linestyle,
                    highlight_first=False,
                    highlight_last=True,
                    color=color,
                )
            self.ax.axis("equal")
            if view == "global":
                self.ax.set_global()  # type: ignore
            elif view == "data":
                _lats = coords_whole_flight[:, 0]
                if is_polar_track:
                    _lats = np.nanmin(_lats)
                if isinstance(self.projection, ccrs.PlateCarree) or not is_polar_track:
                    self.set_view(lats=_lats, lons=coords_whole_flight[:, 1])
                else:
                    _dist = haversine(
                        (self.central_latitude, self.central_longitude),  # type: ignore
                        coords_whole_flight[0],
                        units="m",
                    )
                    self.ax.set_xlim(-_dist / 2, _dist / 2)
                    if coords_whole_flight[0, 0] < coords_whole_flight[1, 0]:
                        self.ax.set_ylim(-_dist / 2, _dist)
                    else:
                        self.ax.set_ylim(-_dist, _dist / 2)
            else:
                _lats = coords_zoomed_in[:, 0]
                if is_polar_track:
                    _lats = np.nanmin(_lats)
                if isinstance(self.projection, ccrs.PlateCarree) or not is_polar_track:
                    self.set_view(lats=_lats, lons=coords_zoomed_in[:, 1])
                else:
                    _dist = haversine(
                        (self.central_latitude, self.central_longitude),  # type: ignore
                        coords_zoomed_in[0],
                        units="m",
                    )
                    self.ax.set_xlim(-_dist / 2, _dist / 2)
                    if coords_zoomed_in[0, 0] < coords_zoomed_in[1, 0]:
                        self.ax.set_ylim(-_dist / 2, _dist)
                    else:
                        self.ax.set_ylim(-_dist, _dist / 2)
                # _lats = coords_zoomed_in[:, 0]
                # if is_polar_track:
                #     _lats = np.nanmin(_lats)
                # self.set_view(lats=_lats, lons=coords_zoomed_in[:, 1])

            if self.show_text_time:
                add_title_earthcare_time(self.ax, ds=ds, tmin=zoom_tmin, tmax=zoom_tmax)

        if isinstance(var, str):
            if cmap is None:
                cmap = get_default_cmap(var, ds)
            if isinstance(value_range, str) and value_range == "default":
                value_range = None
                if log_scale is None and norm is None:
                    norm = get_default_norm(var, file_type=ds)
            lats = ds[swath_lat_var].values
            lons = ds[swath_lon_var].values
            values = ds[var].values
            label = getattr(ds[var], "long_name", "")
            units = getattr(ds[var], "units", "")
            _ = self.plot_swath(
                lats,
                lons,
                values,
                cmap=cmap,
                label=label,
                units=units,
                value_range=value_range,
                log_scale=log_scale,
                norm=norm,
                colorbar=colorbar,
                colorbar_position=colorbar_position,
                colorbar_alignment=colorbar_alignment,
                colorbar_width=colorbar_width,
                colorbar_spacing=colorbar_spacing,
                colorbar_length_ratio=colorbar_length_ratio,
                colorbar_label_outside=colorbar_label_outside,
                colorbar_ticks_outside=colorbar_ticks_outside,
                colorbar_ticks_both=colorbar_ticks_both,
            )

        # if view == "data":
        #     self.set_view(lats=lats, lons=lons)

        # if zoom_tmin or zoom_tmax:
        #     extent = compute_bbox(coords_zoomed_in)
        #     self.ax.set_extent(extent, crs=ccrs.PlateCarree())  # type: ignore
        if self.show_text_frame:
            add_title_earthcare_frame(self.ax, ds=ds)

        self.zoom(extent=extent, radius_km=zoom_radius_km)

        return self

    def _init_cmap(
        self,
        cmap: str | Cmap | None = None,
        value_range: ValueRangeLike | None = None,
        log_scale: bool | None = None,
        norm: Normalize | None = None,
    ) -> tuple[Cmap, tuple, Normalize]:
        cmap = get_cmap(cmap)

        if isinstance(value_range, Iterable):
            if len(value_range) != 2:
                raise ValueError(
                    f"invalid `value_range`: {value_range}, expecting (vmin, vmax)"
                )
        else:
            value_range = (None, None)

        if isinstance(cmap, Cmap) and cmap.categorical == True:
            norm = cmap.norm
        elif isinstance(norm, Normalize):
            if log_scale == True and not isinstance(norm, LogNorm):
                norm = LogNorm(norm.vmin, norm.vmax)
            elif log_scale == False and isinstance(norm, LogNorm):
                norm = Normalize(norm.vmin, norm.vmax)
            if value_range[0] is not None:
                norm.vmin = value_range[0]  # type: ignore # FIXME
            if value_range[1] is not None:
                norm.vmax = value_range[1]  # type: ignore # FIXME
        else:
            if log_scale == True:
                norm = LogNorm(value_range[0], value_range[1])  # type: ignore # FIXME
            else:
                norm = Normalize(value_range[0], value_range[1])  # type: ignore # FIXME

        assert isinstance(norm, Normalize)
        value_range = (norm.vmin, norm.vmax)

        return (cmap, value_range, norm)

    def plot_swath(
        self,
        lats: NDArray,
        lons: NDArray,
        values: NDArray,
        label: str = "",
        units: str = "",
        cmap: str | Cmap | None = None,
        value_range: ValueRangeLike | None = None,
        log_scale: bool | None = None,
        norm: Normalize | None = None,
        colorbar: bool = True,
        colorbar_position: str | Literal["left", "right", "top", "bottom"] = "bottom",
        colorbar_alignment: str | Literal["left", "center", "right"] = "center",
        colorbar_width: float = DEFAULT_COLORBAR_WIDTH,
        colorbar_spacing: float = 0.3,
        colorbar_length_ratio: float | str = "100%",
        colorbar_label_outside: bool = True,
        colorbar_ticks_outside: bool = True,
        colorbar_ticks_both: bool = False,
        show_swath_border: bool = True,
    ) -> "MapFigure":
        cmap, value_range, norm = self._init_cmap(cmap, value_range, log_scale, norm)

        if len(values.shape) == 3 and values.shape[2] == 3:
            mesh = self.ax.pcolormesh(
                lons.T,
                lats.T,
                values,
                shading="auto",
                transform=ccrs.PlateCarree(),
                rasterized=True,
            )
        else:
            mesh = self.ax.pcolormesh(
                lons,
                lats,
                values,
                cmap=cmap,
                norm=norm,
                shading="auto",
                transform=ccrs.PlateCarree(),
                rasterized=True,
            )
            if colorbar:
                cb_kwargs = dict(
                    label=format_var_label(label, units),
                    position=colorbar_position,
                    alignment=colorbar_alignment,
                    width=colorbar_width,
                    spacing=colorbar_spacing,
                    length_ratio=colorbar_length_ratio,
                    label_outside=colorbar_label_outside,
                    ticks_outside=colorbar_ticks_outside,
                    ticks_both=colorbar_ticks_both,
                )
                self.colorbar = add_colorbar(
                    fig=self.fig,
                    ax=self.ax,
                    data=mesh,
                    cmap=cmap,
                    **cb_kwargs,  # type: ignore
                )
                self.set_colorbar_tick_scale(multiplier=self.colorbar_tick_scale)
        if show_swath_border:
            edgecolor = Color("white").set_alpha(0.5)
            _ = self.plot_track(
                lats[:, 0],
                lons[:, 0],
                highlight_first=False,
                highlight_last=False,
                color=edgecolor,
                linewidth=1,
            )
            _ = self.plot_track(
                lats[:, -1],
                lons[:, -1],
                highlight_first=False,
                highlight_last=False,
                color=edgecolor,
                linewidth=1,
            )
            _ = self.plot_track(
                lats[0, :],
                lons[0, :],
                highlight_first=False,
                highlight_last=False,
                color=edgecolor,
                linewidth=1,
            )
            _ = self.plot_track(
                lats[-1, :],
                lons[-1, :],
                highlight_first=False,
                highlight_last=False,
                color=edgecolor,
                linewidth=1,
            )

        return self

    def zoom(
        self, extent: ArrayLike | None = None, radius_km: float | None = None
    ) -> "MapFigure":
        radius_meters: float = 0

        if extent is not None:
            extent = np.asarray(extent)
            if extent.shape[0] != 4:
                ValueError(
                    f"'extent' has wrong size ({extent.shape[0]}), expecting size of 4 (min_lon, max_lon, min_lat, max_lat)"
                )
            lon_extent_km = haversine([extent[2], extent[0]], [extent[2], extent[1]])
            lat_extent_km = haversine([extent[2], extent[0]], [extent[3], extent[0]])
            radius_meters = np.max([lon_extent_km, lat_extent_km]) * 1e3

        if isinstance(radius_km, (int, float)):
            radius_meters = radius_km * 1e3

        if isinstance(self.projection, ccrs.PlateCarree) and extent is not None:
            self.ax.set_extent(extent, crs=ccrs.PlateCarree())  # type: ignore
        elif (
            not isinstance(self.projection, ccrs.PlateCarree) and radius_km is not None
        ):
            self.ax.set_xlim(-radius_meters, radius_meters)
            self.ax.set_ylim(-radius_meters, radius_meters)

        return self

    def to_texture(
        self, remove_images: bool = True, remove_features: bool = True
    ) -> "MapFigure":
        """Convert the figure to a texture by removing all axis ticks, labels, annotations, and text."""
        # Remove anchored text and other artist text objects
        for artist in reversed(self.ax.artists):
            if isinstance(artist, (Text, AnchoredOffsetbox)):
                artist.remove()

        # Completely remove axis ticks and labels
        self.ax.axis("off")

        # Remove white frame around figure
        self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

        # Remove ticks, tick labels, and gridlines
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.xaxis.set_ticklabels([])
        self.ax.yaxis.set_ticklabels([])
        self.ax.grid(False)

        # Remove outline box around map
        self.ax.spines["geo"].set_visible(False)

        # Make the map fill the whole figure
        self.ax.set_position((0.0, 0.0, 1.0, 1.0))

        if self.colorbar:
            self.colorbar.remove()

        if self.grid_lines:
            self.grid_lines.remove()

        if remove_images:
            for img in self.ax.get_images():
                img.remove()

        if remove_features:
            for c in self.ax.get_children():
                if isinstance(c, FeatureArtist):
                    c.remove()

        # for c in self.ax.get_children():
        #     if isinstance(c, _ViewClippedPathPatch):
        #         c.set_alpha(0)

        for c in self.fig.get_children():
            if isinstance(c, Rectangle):
                c.set_alpha(0)

        self.ax.set_facecolor("none")

        return self

    def set_colorbar_tick_scale(
        self,
        multiplier: float | None = None,
        fontsize: float | str | None = None,
    ) -> "MapFigure":
        _cb = self.colorbar
        cb: Colorbar
        if isinstance(_cb, Colorbar):
            cb = _cb
        else:
            return self

        if fontsize is not None:
            cb.ax.tick_params(labelsize=fontsize)
            return self

        if multiplier is not None:
            tls = cb.ax.yaxis.get_ticklabels()
            if len(tls) == 0:
                tls = cb.ax.xaxis.get_ticklabels()
            if len(tls) == 0:
                return self
            _fontsize = tls[0].get_fontsize()
            if isinstance(_fontsize, str):
                from matplotlib import font_manager

                fp = font_manager.FontProperties(size=_fontsize)
                _fontsize = fp.get_size_in_points()
            cb.ax.tick_params(labelsize=_fontsize * multiplier)
        return self

    def show(self) -> None:
        import IPython
        import matplotlib.pyplot as plt
        from IPython.display import display

        if IPython.get_ipython() is not None:
            display(self.fig)
        else:
            plt.show()

    def save(
        self,
        filename: str = "",
        filepath: str | None = None,
        ds: xr.Dataset | None = None,
        ds_filepath: str | None = None,
        dpi: float | Literal["figure"] = "figure",
        orbit_and_frame: str | None = None,
        utc_timestamp: TimestampLike | None = None,
        use_utc_creation_timestamp: bool = False,
        site_name: str | None = None,
        hmax: int | float | None = None,
        radius: int | float | None = None,
        extra: str | None = None,
        transparent_outside: bool = False,
        verbose: bool = True,
        print_prefix: str = "",
        create_dirs: bool = False,
        transparent_background: bool = False,
        resolution: str | None = None,
        **kwargs,
    ) -> None:
        """
        Save a figure as an image or vector graphic to a file and optionally format the file name in a structured way using EarthCARE metadata.

        Args:
            figure (Figure | HasFigure): A figure object (`matplotlib.figure.Figure`) or objects exposing a `.fig` attribute containing a figure (e.g., `CurtainFigure`).
            filename (str, optional): The base name of the file. Can be extended based on other metadata provided. Defaults to empty string.
            filepath (str | None, optional): The path where the image is saved. Can be extended based on other metadata provided. Defaults to None.
            ds (xr.Dataset | None, optional): A EarthCARE dataset from which metadata will be taken. Defaults to None.
            ds_filepath (str | None, optional): A path to a EarthCARE product from which metadata will be taken. Defaults to None.
            pad (float, optional): Extra padding (i.e., empty space) around the image in inches. Defaults to 0.1.
            dpi (float | 'figure', optional): The resolution in dots per inch. If 'figure', use the figure's dpi value. Defaults to None.
            orbit_and_frame (str | None, optional): Metadata used in the formatting of the file name. Defaults to None.
            utc_timestamp (TimestampLike | None, optional): Metadata used in the formatting of the file name. Defaults to None.
            use_utc_creation_timestamp (bool, optional): Whether the time of image creation should be included in the file name. Defaults to False.
            site_name (str | None, optional): Metadata used in the formatting of the file name. Defaults to None.
            hmax (int | float | None, optional): Metadata used in the formatting of the file name. Defaults to None.
            radius (int | float | None, optional): Metadata used in the formatting of the file name. Defaults to None.
            resolution (str | None, optional): Metadata used in the formatting of the file name. Defaults to None.
            extra (str | None, optional): A custom string to be included in the file name. Defaults to None.
            transparent_outside (bool, optional): Whether the area outside figures should be transparent. Defaults to False.
            verbose (bool, optional): Whether the progress of image creation should be printed to the console. Defaults to True.
            print_prefix (str, optional): A prefix string to all console messages. Defaults to "".
            create_dirs (bool, optional): Whether images should be saved in a folder structure based on provided metadata. Defaults to False.
            transparent_background (bool, optional): Whether the background inside and outside of figures should be transparent. Defaults to False.
            **kwargs (dict[str, Any]): Keyword arguments passed to wrapped function call of `matplotlib.pyplot.savefig`.
        """
        save_plot(
            fig=self.fig,
            filename=filename,
            filepath=filepath,
            ds=ds,
            ds_filepath=ds_filepath,
            dpi=dpi,
            orbit_and_frame=orbit_and_frame,
            utc_timestamp=utc_timestamp,
            use_utc_creation_timestamp=use_utc_creation_timestamp,
            site_name=site_name,
            hmax=hmax,
            radius=radius,
            extra=extra,
            transparent_outside=transparent_outside,
            verbose=verbose,
            print_prefix=print_prefix,
            create_dirs=create_dirs,
            transparent_background=transparent_background,
            resolution=resolution,
            **kwargs,
        )
