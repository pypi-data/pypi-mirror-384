from dataclasses import dataclass
from logging import Logger

import numpy as np
import pandas as pd
from requests.exceptions import HTTPError

from ..utils._cli import get_counter_message
from ..utils.time import time_to_iso, to_timestamp
from ._eo_collection import EOCollection
from ._eo_product import (
    EOProduct,
    get_available_products,
    remove_duplicates_keeping_latest,
)


@dataclass
class EOSearchRequest:
    """This class contains all data required as input for the URL template of the OpenSearch API request to EO-CAT."""

    candidate_collections: list[EOCollection]
    product_type: str | None = None
    product_version: str | None = None
    radius: str | None = None
    lat: str | None = None
    lon: str | None = None
    bbox: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    orbit_number: list[int] | None = None
    start_orbit_number: int | None = None
    end_orbit_number: int | None = None
    frame_id: str | None = None
    limit: int = 2000
    orbit_direction: str | None = None
    instrument: str | None = None
    product_id: str | None = None
    illumination_elevation_angle: str | None = None

    def copy(self) -> "EOSearchRequest":
        return EOSearchRequest(
            candidate_collections=self.candidate_collections,
            product_type=self.product_type,
            product_version=self.product_version,
            radius=self.radius,
            lat=self.lat,
            lon=self.lon,
            bbox=self.bbox,
            start_time=self.start_time,
            end_time=self.end_time,
            orbit_number=self.orbit_number,
            start_orbit_number=self.start_orbit_number,
            end_orbit_number=self.end_orbit_number,
            frame_id=self.frame_id,
            limit=self.limit,
            orbit_direction=self.orbit_direction,
            instrument=self.instrument,
            product_id=self.product_id,
            illumination_elevation_angle=self.illumination_elevation_angle,
        )

    def split_optimize_requests(self) -> list["EOSearchRequest"]:
        new_requests: list[EOSearchRequest] = []

        num_frames: int = 1 if self.frame_id else 8

        num_orbits: int = 0
        if isinstance(self.end_orbit_number, int):
            _so = 0 if not self.start_orbit_number else self.start_orbit_number
            num_orbits = self.end_orbit_number - _so

            num_files = num_orbits * num_frames
            num_new_requests = int(np.ceil(num_files / self.limit))
            _last_eo = 0
            for i in range(num_new_requests):
                new_r = self.copy()
                new_r.start_orbit_number = max(
                    _last_eo, int(_so + np.floor(num_orbits / num_new_requests) * i)
                )
                new_r.end_orbit_number = int(
                    _so + np.ceil(num_orbits / num_new_requests) * (i + 1)
                )
                _last_eo = new_r.end_orbit_number
                new_requests.append(new_r)
        elif isinstance(self.start_orbit_number, int):
            _so = self.start_orbit_number
            _t_ref = pd.Timestamp("2025-08-01")
            _o_ref = 6675
            _t_now = pd.Timestamp.now()
            _t_delta = _t_now - _t_ref
            _days = _t_delta.total_seconds() / (60 * 60 * 24)
            _eo = int(_o_ref + (_days * 16))
            num_orbits = _eo - _so

            num_files = num_orbits * num_frames
            num_new_requests = int(np.ceil(num_files / self.limit))
            _last_eo = 0
            for i in range(num_new_requests):
                new_r = self.copy()
                new_r.start_orbit_number = max(
                    _last_eo, int(_so + np.floor(num_orbits / num_new_requests) * i)
                )
                new_r.end_orbit_number = int(
                    _so + np.floor(num_orbits / num_new_requests) * (i + 1)
                )
                _last_eo = new_r.end_orbit_number
                new_requests.append(new_r)
        elif self.orbit_number:
            num_orbits = len(self.orbit_number)

            num_files = num_orbits * num_frames
            num_new_requests = int(np.ceil(num_files / self.limit))
            for i in range(num_new_requests):
                new_r = self.copy()
                _idx1 = int(np.floor(num_orbits / num_new_requests) * i)
                _idx2 = int(np.floor(num_orbits / num_new_requests) * (i + 1))
                new_r.orbit_number = self.orbit_number[_idx1:_idx2]
                new_requests.append(new_r)
        elif self.end_time:
            _et = to_timestamp(self.end_time)
            _st = (
                to_timestamp("2024-07-31")
                if not self.start_time
                else to_timestamp(self.start_time)
            )
            _t_delta = _et - _st
            _days = _t_delta.total_seconds() / (60 * 60 * 24)
            num_orbits = max(1, int(_days * 16.0))

            num_files = num_orbits * num_frames
            num_new_requests = int(np.ceil(num_files / self.limit))
            for i in range(num_new_requests):
                new_r = self.copy()
                new_r.start_time = time_to_iso(_st + (_t_delta / num_new_requests) * i)
                new_r.end_time = time_to_iso(
                    _st + (_t_delta / num_new_requests) * (i + 1)
                )
                new_requests.append(new_r)
        elif self.start_time:
            _et = pd.Timestamp.now()
            _st = to_timestamp(self.start_time)
            _t_delta = _et - _st
            _days = _t_delta.total_seconds() / (60 * 60 * 24)
            num_orbits = max(1, int(_days * 16.0))

            num_files = num_orbits * num_frames
            num_new_requests = int(np.ceil(num_files / self.limit))
            for i in range(num_new_requests):
                new_r = self.copy()
                new_r.start_time = time_to_iso(_st + (_t_delta / num_new_requests) * i)
                new_r.end_time = time_to_iso(
                    _st + (_t_delta / num_new_requests) * (i + 1)
                )
                new_requests.append(new_r)
        else:
            new_requests = [self.copy()]

        num_files = num_orbits * num_frames

        return new_requests

    @property
    def stac_parameters(self) -> dict[str, str]:
        params: dict[str, str] = {}
        if isinstance(self.limit, int):
            params["limit"] = str(self.limit + 1)
        if isinstance(self.orbit_direction, str):
            params["orbitDirection"] = self.orbit_direction
        if isinstance(self.instrument, str):
            params["instrument"] = self.instrument
        if isinstance(self.product_id, str):
            params["uid"] = self.product_id
        if isinstance(self.illumination_elevation_angle, str):
            params["illuminationElevationAngle"] = self.illumination_elevation_angle
        # Product
        if isinstance(self.product_type, str):
            params["productType"] = self.product_type
        if isinstance(self.product_version, str):
            params["productVersion"] = self.product_version.lower()
        # Geo search
        if isinstance(self.radius, str):
            params["radius"] = self.radius
        if isinstance(self.lat, str):
            params["lat"] = self.lat
        if isinstance(self.lon, str):
            params["lon"] = self.lon
        if isinstance(self.bbox, str):
            params["bbox"] = self.bbox
        # Orbit number and frame ID
        if isinstance(self.orbit_number, list):
            orb_num_list_str = ",".join([str(int(o)) for o in self.orbit_number])
            params["orbitNumber"] = "{" + orb_num_list_str + "}"
        elif isinstance(self.start_orbit_number, int) and isinstance(
            self.end_orbit_number, int
        ):
            params["orbitNumber"] = (
                f"[{str(self.start_orbit_number)},{str(self.end_orbit_number)}]"
            )
        elif isinstance(self.start_orbit_number, int):
            params["orbitNumber"] = f"[{str(self.start_orbit_number)},99999]"
        elif isinstance(self.end_orbit_number, int):
            params["orbitNumber"] = f"[0,{str(self.end_orbit_number)}]"
        if isinstance(self.frame_id, str):
            params["frame"] = self.frame_id
        # Time search
        if isinstance(self.start_time, str) and isinstance(self.end_time, str):
            params["datetime"] = f"{self.start_time}/{self.end_time}"
        elif isinstance(self.start_time, str):
            params["datetime"] = f"{self.start_time}/"
        elif isinstance(self.end_time, str):
            params["datetime"] = f"/{self.end_time}"

        return params

    def run(
        self,
        logger: Logger | None = None,
        total_count: int | None = None,
        counter: int | None = None,
    ) -> list[EOProduct]:
        count_msg, _ = get_counter_message(counter=counter, total_count=total_count)

        if logger:
            logger.info(f"*{count_msg} {self.low_detail_summary}")
            logger.debug(f" {count_msg} {self}")

        if len(self.candidate_collections) == 0:
            if logger:
                logger.warning(
                    f" {count_msg} No collection was selected. Please make sure that you have added the appropriate collections for this product in the configuration file and that you are allowed to access to them."
                )
                return []

        _available_products: list[EOProduct] = []
        for cc in sorted(self.candidate_collections):

            try:
                _available_products = get_available_products(
                    cc,
                    params=self.stac_parameters,
                    logger=logger,
                )
            except HTTPError as e:
                if logger:
                    logger.exception(e)
                    if (
                        self.stac_parameters.get("productType") == "AUX_MET_1D"
                        and self.stac_parameters.get("radius") is not None
                    ):
                        logger.error("Radius search is not supported for AUX_MET_1D.")

            _available_products = remove_duplicates_keeping_latest(_available_products)

            if len(_available_products) > 0:
                if logger:
                    logger.info(
                        f" {count_msg} Files found in collection '{cc.name}': {len(_available_products)}"
                    )
                    if len(_available_products) >= self.limit:
                        logger.warning(
                            f"The number of results equals the limit of results per search request ({self.limit}). Please divide your requests into smaller, manageable chunks (e.g., by selecting a shorter time range)."
                        )
                break

        return _available_products

    @property
    def low_detail_summary(self):
        msg = f"Search request: {self.product_type}"
        if self.product_version:
            msg = f"{msg}:{self.product_version}"
        if self.start_time and self.end_time:
            if self.start_time == self.end_time:
                msg = f"{msg}, time={self.start_time}"
            else:
                st_msg = self.start_time if self.start_time else "..."
                et_msg = self.end_time if self.end_time else "..."
                msg = f"{msg}, time_range=({st_msg},{et_msg})"
        if self.radius and self.lat and self.lon:
            msg = f"{msg}, radius=({self.radius}m, {self.lat}N, {self.lon}E)"
        if self.bbox:
            msg = f"{msg}, bbox={self.bbox}"
        if self.frame_id:
            msg = f"{msg}, frame={self.frame_id}"
        if self.start_orbit_number or self.end_orbit_number:
            so_msg = self.start_orbit_number if self.start_orbit_number else "..."
            eo_msg = self.end_orbit_number if self.end_orbit_number else "..."
            msg = f"{msg}, orbit_range=({so_msg},{eo_msg})"
        if self.orbit_number:
            o_msg = f"{self.orbit_number}"
            if len(o_msg.split(",")) > 6:
                o_msg = (
                    ",".join(o_msg.split(",")[0:2])
                    + f",... {len(o_msg.split(',')) - 4} more orbits ...,"
                    + ",".join(o_msg.split(",")[-2:])
                )
            msg = f"{msg}, orbits={o_msg.replace(',', ', ')}"
        return msg
