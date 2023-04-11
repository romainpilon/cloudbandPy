#!/usr/bin/env python
# coding: utf-8

"""
This script allows to create a map of the spatial distribution of precipitation 
average over 1983 to 2019 overlaid by cloud band days per year, over the South Pacific.
The work performed was done by using data from the Global Precipitation Climatology Project and from ERA5.

Before running this script, ensure that you have extracted the cloud bands and have thecloud band files ready.
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.cm import get_cmap
from netCDF4 import Dataset
import numpy as np
import sys

try:
    import cartopy.crs as ccrs
    import cartopy.util as cutil
    from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

    LON_FORMAT = LongitudeFormatter(zero_direction_label=True, degree_symbol="")
    LAT_FORMAT = LatitudeFormatter(degree_symbol="")
except:
    print("Cartopy is not installed. Figure will not be produced.")

try:
    # better looking colorblind-proof colormaps
    import colorcet
except:
    pass


dir_package = "/users/rpilon/codes/unil/CloudBandDetection/"
sys.path.insert(0, dir_package + "src/")
from figure_tools import set_fontsize
from io_utilities import load_ymlfile, load_data_from_saved_var_files, subset_latitudes, subset_longitudes
from time_utilities import create_list_of_dates
from tracking import compute_density


def plot_gpcg_precip_cloudbandday(lons, lats, lonscb, latscb, config):
    # Global map of OLR year mean
    set_fontsize(17)
    try:
        # better looking colorblind-proof colormap from colorcet
        cmap = get_cmap("cet_CET_CBL2_r")
    except:
        cmap = get_cmap("viridis")
    #
    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
    fill = ax.contourf(
        lons,
        lats,
        np.ma.masked_where(cdata == 0, cdata),
        transform=ccrs.PlateCarree(),
        levels=np.arange(0.0, 12.2, 0.2),
        cmap=cmap,
        extend="max",
    )
    cs = ax.contour(
        lonscb,
        latscb,
        np.ma.masked_where(density == 0, density),
        transform=ccrs.PlateCarree(),
        levels=range(0, 56, 7),
        linewidths=1.5,
        colors="#497C3F",
    )
    ax.clabel(cs, cs.levels, inline=True)
    ax.coastlines("50m", color="#404040", linewidth=0.8)
    ax.set_extent(
        (config["lon_west"], config["lon_east"], config["lat_south"], config["lat_north"]), crs=ccrs.PlateCarree()
    )
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=0.6, color="gray", alpha=0.4, linestyle="-")
    gl.top_labels = False
    gl.ylocator = mticker.MultipleLocator(20)
    gl.xlocator = mticker.MultipleLocator(20)
    gl.xformatter = LON_FORMAT
    gl.yformatter = LAT_FORMAT
    #
    im_ratio = cdata.shape[0] / cdata.shape[1]
    cbar = fig.colorbar(fill, orientation="vertical", ticks=range(0, 13, 1), fraction=0.04 * im_ratio)
    cbar.ax.set_yticklabels([el if el % 2 == 0 else "" for el in range(13)])
    cbar.set_label(r"Precipitation rate (mm.day$^{-1}$)")
    return fig


if __name__ == "__main__":
    # Load GPCP precipitation (copyright 2023 GPCP)
    ncfile = Dataset(dir_package + "data/GPCPMON_L3_1983_2019_timemean.nc4", "r")
    lons = ncfile.variables["lon"][:]
    lats = ncfile.variables["lat"][:]
    precip = ncfile.variables["sat_gauge_precip"][0]  # mm/day
    # add cyclic point
    cdata, clons = cutil.add_cyclic_point(precip, lons)
    config_file = dir_package + "config/config_analysis.yml"
    config = load_ymlfile(config_file, isconfigfile=True)
    # Make sure that the period for the cloud bands cover the same period as GPCP
    config["startdate"] = "19830101.00"
    config["enddate"] = "20191231.00"
    # Get latitude and longitude of 0.5 degree ERA5 data
    lats_globe = np.load(dir_package + "data/lats_globe0.5_ERA5.npy")
    lons_globe = np.load(dir_package + "data/lons_globe0.5_ERA5.npy")
    # Get longitudes and latitudes of South Pacific domain
    _, lonsSP = subset_longitudes(lons_globe, config["lon_west"], config["lon_east"])
    _, latsSP = subset_latitudes(lats_globe, config["lat_north"], config["lat_south"])
    # Load cloud bands from the South Pacific
    listofdates = create_list_of_dates(config)
    list_of_cloud_bands = load_data_from_saved_var_files(config, varname="list_of_cloud_bands")
    # Compute density for the southern hemisphere
    _, density = compute_density(lats=latsSP, lons=lonsSP, dates=listofdates, list_of_cloud_bands=list_of_cloud_bands)
    # Create figure and save it
    fig = plot_gpcg_precip_cloudbandday(clons, lats, lonsSP, latsSP, config)
    fig.show()
    fig.savefig(
        f"./map_precip_GPCP_avg_{config['datetime_startdate'].year}-{config['datetime_enddate'].year}_cloudbands7days.png",
        dpi=200,
        bbox_inches="tight",
    )
