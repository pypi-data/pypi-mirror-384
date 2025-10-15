import math
from typing import SupportsFloat

import numpy as np
from numpy.typing import NDArray

from ..constants import SEMI_MAJOR_AXIS_METERS, SEMI_MINOR_AXIS_METERS


def geo_to_ecef(
    lat: SupportsFloat,
    lon: SupportsFloat,
    alt: SupportsFloat | None = None,
    target_radius: float = 1.0,
    perfect_sphere: bool = True,
    semi_major: float = SEMI_MAJOR_AXIS_METERS,
    semi_minor: float = SEMI_MINOR_AXIS_METERS,
) -> tuple[float, float, float]:
    """
    Converts geodetic coordinates (i.e. latitude, longitude and altitude above ellipsoid)
    to Earth-centered, Earth-fixed (ECEF) coordinates (i.e. x, y and z in cartesian coordinates).

    Args:
        lat (float): Latitude angle north (positive) and south (negative) of the equator in degrees.
        lon (float): Longitude angle east (positive) and west (negative) of the prime meridian in degrees.
        alt (float, optional): Height above above the Earth ellipsoid in meters.
        target_radius (float, optional): Target mean radius of the Earth ellipsoid in the new cartesian coordinate system. Defaults to 1.
        semi_major (float, optional): Semi-major axis of the Earth ellipsoid in meters. Defaults to 6378137 (WGS 84).
        semi_minor (float, optional): Semi-minor axis of the Earth ellipsoid in meters. Defaults to 6356752.314245 (WGS 84).

    Returns:
        coords (tuple[float, float, float]): 3D coordinates in meters (ECEF: A right-handed cartesian coordinate system that has its origin at the Earth's center and is fixed with respect to the Earth's rotation).

            - x (float): Point along the axis passing through the equator at the prime meridian (i.e. latitude = 0, longitude = 0 degrees).
            - y (float): Point along the axis passing through the equator 90 degrees east of the Prime Meridian (i.e. latitude = 0, longitude = 90 degrees).
            - z (float): Point along the axis passing through the north pole (i.e. latitude = 90 degrees).
    """
    lat = float(lat)
    lon = float(lon)
    if alt is None:
        alt = 0.0
    else:
        alt = float(alt)

    sin = lambda x: math.sin(x)
    cos = lambda x: math.cos(x)
    sqrt = lambda x: math.sqrt(x)

    lat = math.radians(lat)
    lon = math.radians(lon)

    if perfect_sphere:
        # Calculate ECEF coordinates
        f = 1 - (semi_major / semi_major)  # Flattening of the ellipsoid
        N = semi_major / sqrt(
            1 - (f * sin(lat)) ** 2
        )  # Prime vertical radius of curvature

        x = (N + alt) * cos(lat) * cos(lon)
        y = (N + alt) * cos(lat) * sin(lon)
        z = ((semi_major**2 / semi_major**2) * N + alt) * sin(lat)

        # # Alternative
        # e2 = 1 - (semi_minor**2 / semi_major**2) # Square of the first numerical eccentricity of the ellipsoid
        # N = semi_major / sqrt(1 - e2 * (sin(lat) ** 2)) # Prime vertical radius of curvature

        # Scale ECEF coordinates to target radius
        R = ((semi_major + semi_major) / 2) / target_radius
        x = -x / R
        y = -y / R
        z = z / R
    else:
        # Calculate ECEF coordinates
        f = 1 - (semi_minor / semi_major)  # Flattening of the ellipsoid
        N = semi_major / sqrt(
            1 - (f * sin(lat)) ** 2
        )  # Prime vertical radius of curvature

        x = (N + alt) * cos(lat) * cos(lon)
        y = (N + alt) * cos(lat) * sin(lon)
        z = ((semi_minor**2 / semi_major**2) * N + alt) * sin(lat)

        # # Alternative
        # e2 = 1 - (semi_minor**2 / semi_major**2) # Square of the first numerical eccentricity of the ellipsoid
        # N = semi_major / sqrt(1 - e2 * (sin(lat) ** 2)) # Prime vertical radius of curvature

        # Scale ECEF coordinates to target radius
        R = ((semi_major + semi_minor) / 2) / target_radius
        x = -x / R
        y = -y / R
        z = z / R

    return x, y, z


def ecef_to_geo(
    x: SupportsFloat,
    y: SupportsFloat,
    z: SupportsFloat,
    target_radius: float = 1.0,
    perfect_sphere: bool = True,
    semi_major: float = SEMI_MAJOR_AXIS_METERS,
    semi_minor: float = SEMI_MINOR_AXIS_METERS,
) -> tuple[float, float, float]:
    """
    Converts Earth-centered, Earth-fixed (ECEF) coordinates (x, y, z)
    back to geodetic coordinates (latitude, longitude, altitude).

    Args:
        x, y, z (float): Cartesian ECEF coordinates.
        target_radius (float): Target mean radius of the Earth ellipsoid in the new cartesian coordinate system. Defaults to 1.
        perfect_sphere (bool): If True, assume a spherical Earth, else ellipsoidal (WGS-84).
        semi_major (float, optional): Semi-major axis of the Earth ellipsoid in meters. Defaults to 6378137 (WGS 84).
        semi_minor (float, optional): Semi-minor axis of the Earth ellipsoid in meters. Defaults to 6356752.314245 (WGS 84).

    Returns:
        coords (tuple[float, float, float]):

            - lat (float): Latitude in degrees
            - lon (float): Longitude in degrees
            - alt (float): Altitude above ellipsoid in meters
    """
    x = float(x)
    y = float(y)
    z = float(z)

    # Undo scaling
    R = (
        (semi_major + (semi_major if perfect_sphere else semi_minor)) / 2
    ) / target_radius
    x = -x * R
    y = -y * R
    z = z * R

    lon = math.atan2(y, x)

    if perfect_sphere:
        r = math.sqrt(x**2 + y**2 + z**2)
        lat = math.asin(z / r)
        alt = r - semi_major
    else:
        e2 = 1 - (semi_minor**2 / semi_major**2)
        p = math.sqrt(x**2 + y**2)
        # Initial guess
        lat = math.atan2(z, p * (1 - e2))
        # Iterative refienment
        for _ in range(5):
            N = semi_major / math.sqrt(1 - e2 * math.sin(lat) ** 2)
            alt = p / math.cos(lat) - N
            lat = math.atan2(z, p * (1 - e2 * (N / (N + alt))))
        N = semi_major / math.sqrt(1 - e2 * math.sin(lat) ** 2)
        alt = p / math.cos(lat) - N

    return math.degrees(lat), math.degrees(lon), alt


def sequence_geo_to_ecef(
    lats: NDArray | list[SupportsFloat],
    lons: NDArray | list[SupportsFloat],
    alts: NDArray | list[SupportsFloat] | SupportsFloat | None = None,
    target_radius: float = 1.0,
    perfect_sphere: bool = True,
    semi_major: float = SEMI_MAJOR_AXIS_METERS,
    semi_minor: float = SEMI_MINOR_AXIS_METERS,
) -> NDArray:
    lats = np.asarray(lats)
    lons = np.asarray(lons)
    if alts is None:
        alts = np.zeros(lats.shape)
    elif isinstance(alts, (float, int)):
        alts = np.repeat(float(alts), lats.shape)
    else:
        alts = np.asarray(alts)
    coords: NDArray = np.stack((lats, lons, alts)).T
    xyz = np.array(
        [
            list(
                geo_to_ecef(
                    c[0],
                    c[1],
                    c[2],
                    target_radius=target_radius,
                    perfect_sphere=perfect_sphere,
                    semi_major=semi_major,
                    semi_minor=semi_minor,
                )
            )
            for c in coords
        ]
    )
    return xyz
