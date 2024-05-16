"""Retrieve Netatmo data."""

# %%
import logging
from datetime import datetime, timezone
from pathlib import Path

from netatmodata import NetatmoData

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("retrieve-data")

# Choose a time range, location and name for the data
nd = NetatmoData(
    area={"north": 55, "west": -130, "south": 15, "east": -60},
    startdate=datetime(2022, 1, 15, tzinfo=timezone.utc),
    enddate=datetime(2022, 1, 17, tzinfo=timezone.utc),
    name="netatmo-2022-01-15-17",
)


def retrieve(nd: NetatmoData) -> None:
    """Download data."""
    for station in nd.stations:
        nd.get_data(
            station["_id"],
            "pressure",
            ratelimit=8,
        )


def convert(nd: NetatmoData, outputdir: str) -> None:
    """Convert data to CSV."""
    import numpy as np
    import pandas as pd

    stationdata = [
        (
            s["place"]["location"],
            np.array(([datetime.fromtimestamp(t, tz=timezone.utc) for t in ts], p)),
        )
        for s, (ts, p) in zip(nd.stations, nd.get_all_data("pressure"))
        if len(p) > 0
    ]

    outputdir.mkdir(exist_ok=True)
    for station in stationdata:
        dtstationdata = pd.DataFrame(station[1].T, columns=(["time", "pressure"]))
        dtstationdata.to_csv(
            outputdir.joinpath(f"Lon{station[0][0]}Lat{station[0][1]}.csv"),
            index=False,
        )
        log.info(
            f"Saved {outputdir.joinpath(f'Lon{station[0][0]}Lat{station[0][1]}.csv')}",
        )


def plot_stations(nd: NetatmoData) -> None:
    """Plot stations."""
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from matplotlib import pyplot as plt

    # Define the latitude and longitude coordinates for the rectangle
    lon1, lon2 = -60, -130
    lat1, lat2 = 15, 55

    # Create a new figure and axis with a PlateCarree projection
    fig, ax = plt.subplots(
        figsize=(10, 10),
        subplot_kw={"projection": ccrs.PlateCarree()},
    )

    # Add a map background
    ax.stock_img()

    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linestyle=":")

    # Draw the rectangle on the map
    ax.plot(
        [lon1, lon2, lon2, lon1, lon1],
        [lat1, lat1, lat2, lat2, lat1],
        color="red",
        linewidth=2,
        transform=ccrs.PlateCarree(),
    )

    # Set the extent of the map to include the rectangle
    ax.set_extent([lon1, lon2, lat1, lat2], crs=ccrs.PlateCarree())

    nd.stations = nd.get_stations()
    pressures = nd.get_all_data("pressure")
    lons = [
        s["place"]["location"][0]
        for s, p in zip(nd.stations, pressures, strict=True)
        if len(p[0]) > 0
    ]
    lats = [
        s["place"]["location"][1]
        for s, p in zip(nd.stations, pressures, strict=True)
        if len(p[0]) > 0
    ]
    ax.plot(
        lons,
        lats,
        color="blue",
        marker="o",
        markersize=1,
        linestyle="None",
        label=f"data available from {len(lons)} stations",
        transform=ccrs.PlateCarree(),
    )

    lons = [
        s["place"]["location"][0]
        for s, p in zip(nd.stations, pressures, strict=True)
        if len(p[0]) == 0
    ]
    lats = [
        s["place"]["location"][1]
        for s, p in zip(nd.stations, pressures, strict=True)
        if len(p[0]) == 0
    ]
    ax.plot(
        lons,
        lats,
        color="red",
        marker="o",
        markersize=1,
        linestyle="None",
        label=f"no data available from {len(lons)} stations",
        transform=ccrs.PlateCarree(),
    )
    ax.legend()

    # Show the plot
    plt.show()
    fig.savefig("map.pdf", bbox_inches="tight")


def main() -> None:
    """Retrieve Netatmo data."""
    nd.get_stations()

    retrieve(nd)
    convert(nd, Path("csv"))
    plot_stations(nd)


if __name__ == "__main__":
    main()
