"""Netatmo data downloader."""

# %%
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING

import lnetatmo

if TYPE_CHECKING:
    from datetime import datetime


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class NetatmoData:
    """Netatmo data downloader."""

    def __init__(
        self: NetatmoData,
        area: dict,
        startdate: datetime,
        enddate: datetime,
        name: str = "data",
    ) -> None:
        """Netatmo data downloader.

        Args:
            area (dict): The area to download data for.
            startdate (datetime): The start date for the data download in UTC.
            enddate (datetime): The end date for the data download in UTC.
            name (str | None, optional): The name of the data set. Defaults to None.
        """
        self.autorization = None
        self.stations: list = None
        self.name: str = name
        self.datadir: Path = Path(name)
        self.startdate: datetime = startdate
        self.enddate: datetime = enddate
        self.area: dict = area
        self.datadir.mkdir(exist_ok=True)

    def authorize(self: NetatmoData) -> None:
        """Authorize the client."""
        if self.autorization is None:
            self.authorization = lnetatmo.ClientAuth()

    def get_stations(
        self: NetatmoData,
        *,
        filter_stations: bool = True,
    ) -> list[dict]:
        """Get a list of stations in the area.

        Args:
            filter_stations (bool, optional): Filter stations by type. Defaults to True.

        Returns:
            list[dict]: List of dictionaries containing information about the stations.
        """
        if self.stations is not None:
            log.info("Stations already loaded")
            return self.stations
        fname = self.datadir.joinpath(
            f"stations-N{self.area['north']}W{self.area['west']}S{self.area['south']}E{self.area['east']}.json",
        )
        try:
            with fname.open() as f:
                self.stations = json.load(f)
                log.info(f"Loaded {len(self.stations)} stations from {fname}")
        except FileNotFoundError:
            log.info(
                f"Downloading stations for {self.area["north"]} {self.area['west']} {self.area['south']} {self.area['east']}",
            )
            self.authorize()
            self.stations = lnetatmo.rawAPI(
                self.authorization,
                "getpublicdata",
                {
                    "lat_ne": self.area["north"],
                    "lon_ne": self.area["east"],
                    "lat_sw": self.area["south"],
                    "lon_sw": self.area["west"],
                    "filter": filter_stations,
                },
            )
            with fname.open("w") as f:
                f.writelines(json.dumps(self.stations))
            log.info(f"Downloaded {len(self.stations)} stations to {fname}")
        return self.stations

    def get_data(
        self: NetatmoData,
        station_id: str,
        measurement_type: str,
        ratelimit: float | None = None,
    ) -> tuple[list, list]:
        """Get data from a station.

        Args:
            station_id (str): The ID of the station.
            measurement_type (str): The type of measurement to retrieve.
              Values: "temperature", "humidity", "pressure", "co2", "no2",
                  "o3", "voc", "pm10", "pm25".
            ratelimit (float, optional): The rate limit in seconds. Defaults to None.

        Returns:
            tuple (list, list): A tuple containing two lists - times and values.
            times (list): A list of timestamps for the retrieved data.
            values (list): A list of measurement values for the specified station and measurement type.
        """
        if self.stations is None:
            self.get_stations()

        module_id = None
        station = [s for s in self.stations if s["_id"] == station_id]
        if len(station) == 0:
            msg = f"Station {station_id} not found."
            raise ValueError(msg)
        station = station[0]

        for mid, measure in station["measures"].items():
            if measurement_type in measure["type"]:
                module_id = mid
                break

        measurements = None
        jsonfile = self.datadir.joinpath(
            f"{station_id}-{module_id}-{measurement_type}.json",
        )
        try:
            with jsonfile.open() as f:
                measurements = json.load(f)
            log.info(f"Loaded data for {station_id} {module_id} {measurement_type}")
        except FileNotFoundError:
            pass

        if measurements is None:
            log.info(
                f"Downloading data for {station_id} {module_id} {measurement_type}",
            )
            self.authorize()
            measurements = lnetatmo.rawAPI(
                self.authorization,
                "getmeasure",
                {
                    "device_id": station_id,
                    "module_id": module_id,
                    "type": measurement_type,
                    "scale": "max",
                    "date_begin": self.startdate.timestamp(),
                    "date_end": self.enddate.timestamp(),
                },
            )
            with jsonfile.open("w") as f:
                f.writelines(json.dumps(measurements))
            if ratelimit is not None:
                sleep(ratelimit)

        values = []
        times = []
        for m in measurements:
            if "step_time" not in m:
                times += [m["beg_time"]]
            else:
                times += range(
                    m["beg_time"],
                    m["beg_time"] + m["step_time"] * len(m["value"]),
                    m["step_time"],
                )
            values += [m[0] for m in m["value"]]

        return (times, values)

    def get_all_data(
        self: NetatmoData,
        measurement_type: str,
    ) -> list[tuple[list, list]]:
        """Get all data from a range of stations.

        Args:
            measurement_type (str): The type of measurement to retrieve.
              Values: "temperature", "humidity", "pressure", "co2", "no2",
                  "o3", "voc", "pm10", "pm25".

        Returns:
            list[tuple[list, list]]: A list of tuples containing two lists -
                times and values.
            times (list): A list of timestamps for the retrieved data.
            values (list): A list of measurement values for the specified station
                and measurement type.
        """
        if self.stations is None:
            self.get_stations()

        return [
            self.get_data(
                station["_id"],
                measurement_type,
                ratelimit=8,
            )
            for station in self.stations
        ]
