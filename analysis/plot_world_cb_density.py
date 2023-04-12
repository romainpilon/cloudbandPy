#!/usr/bin/env python
# coding: utf-8

"""
Here we aim at plotting a world map overlayed by cloud bands of each hemisphere
to obtain a world climatology of cloud band density

0. you need to have saved data first fopr both hemispheres
1. Load data: list_of_cloud_bands to compute density of cb
2. Load one year for lon, lat
3. Plot a map
"""

import sys
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.cm import get_cmap
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import numpy as np

try:
    import cartopy.crs as ccrs
    import cartopy.util as cutil
except ImportError:
    print("Cartopy is not installed. Figure will not be produced.")

try:
    import colorcet as cc  # better looking colorblind-proof colormaps
except ImportError:
    pass

DIRCODE = "/users/rpilon/codes/unil/CloudBandDetection/"
sys.path.insert(0, DIRCODE + "src/")
from figure_tools import set_fontsize
from io_utilities import load_ymlfile, load_data_from_saved_var_files
from tracking import compute_density
from time_utilities import create_list_of_dates

# FIXME
# from CloudBandDetection.src.figure_tools import set_fontsize
# from CloudBandDetection.src.io_utilities import load_ymlfile, load_data_from_saved_var_files
# from CloudBandDetection.src.tracking import compute_density
# from CloudBandDetection.src.utilities import wrapTo180


def overlay_array_on_map_withlatitudes(
    array2overlay: np.ndarray,
    lats2overlay: np.ndarray,
    lats: np.ndarray,
    lons: np.ndarray,
    final_array: np.ndarray = None,
    initial: bool = True,
) -> np.ndarray:
    if initial:
        final_array = np.zeros((len(lats), len(lons)))
    index = np.intersect1d(lats, lats2overlay, return_indices=True)[1]
    final_array[index[::-1], :] = array2overlay
    return final_array


def create_worldmap_density(density, lons, lats):
    # 4. Create figure
    set_fontsize()
    try:
        # better looking colorblind-proof colormap
        cmap = get_cmap("cet_CET_CBL2_r")
    except:
        cmap = get_cmap("viridis")
    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.EqualEarth(central_longitude=180))
    fill = ax.contourf(
        lons,
        lats,
        np.ma.masked_where(density == 0, density),
        transform=ccrs.PlateCarree(),
        levels=range(0, 61, 1),
        cmap=cmap,
        extend="max",
    )
    # add contours every 7 days
    ax.contour(
        lons,
        lats,
        np.ma.masked_where(density == 0, density),
        transform=ccrs.PlateCarree(),
        levels=range(0, 56, 7),
        linewidths=0.6,
        colors="white",
    )
    ax.coastlines("50m", color="#404040", linewidth=0.8)
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=0.6, color="gray", alpha=0.4, linestyle="-")
    gl.top_labels = False
    gl.ylocator = mticker.FixedLocator([-60, -40, -20, 0, 20, 40, 60])
    gl.xlocator = mticker.FixedLocator([60, 120, 180, -120, -60])
    # Add colorbar
    axins = inset_axes(ax, width="100%", height="5%", loc="lower center", borderpad=-5)
    cbar = fig.colorbar(fill, cax=axins, orientation="horizontal")
    cbar.set_label("Number of cloud band days per year")
    return fig


if __name__ == "__main__":
    config_file = sys.argv[-1] or f"{DIRCODE}/config/config_analysis_world_cb_density.yml"
    config = load_ymlfile(config_file, isconfigfile=True)

    # 1.1 Get latitude and longitude of 0.5 degree ERA5 data
    lats_globe = np.load(DIRCODE + "data/lats_globe0.5_ERA5.npy")
    lons_globe = np.load(DIRCODE + "data/lons_globe0.5_ERA5.npy")

    # 1.2 Get longitudes and latitudes of southern hemisphere
    lon_ids = np.where(np.logical_and(lons_globe <= config["lon_east"], lons_globe >= config["lon_west"]))[0]
    lonssh = lons_globe[lon_ids]
    lat_ids = np.where(np.logical_and(lats_globe <= config["lat_north"], lats_globe >= config["lat_south"]))[0]
    latssh = lats_globe[lat_ids]

    # 1.3 Load cloud bands from the southern hemisphere (default config is for southern hemisphere)
    listofdates = create_list_of_dates(config)
    list_of_cloud_bandssh = load_data_from_saved_var_files(config, varname="list_of_cloud_bands")

    # 1.4 Compute density for the southern hemisphere
    ntot_cbsh, densitysh = compute_density(
        lats=latssh, lons=lonssh, dates=listofdates, list_of_cloud_bands=list_of_cloud_bandssh
    )

    # 2.1 Load cloud bands and dates from the northern hemisphere
    config["domain"] = "northernhemisphere"
    config["lat_north"] = 50
    config["lat_south"] = 10
    list_of_cloud_bandsnh = load_data_from_saved_var_files(config, varname="list_of_cloud_bands")

    # 2.2 Get longitudes and latitudes of northern hemisphere domain
    lon_ids = np.where(np.logical_and(lons_globe <= config["lon_east"], lons_globe >= config["lon_west"]))[0]
    lonsnh = lons_globe[lon_ids]
    lat_ids = np.where(np.logical_and(lats_globe <= config["lat_north"], lats_globe >= config["lat_south"]))[0]
    latsnh = lats_globe[lat_ids]

    # 2.3 Compute density for the northern hemisphere
    ntot_cbnh, densitynh = compute_density(
        lats=latsnh, lons=lonsnh, dates=listofdates, list_of_cloud_bands=list_of_cloud_bandsnh
    )

    # 3. Overlay southern hemisphere densities over an empty world map
    world_density = overlay_array_on_map_withlatitudes(
        array2overlay=densitysh, lats2overlay=latssh, lats=lats_globe, lons=lons_globe, initial=True
    )
    # Overlay northern hemisphere densities over world map
    world_density = overlay_array_on_map_withlatitudes(
        array2overlay=densitynh,
        lats2overlay=latsnh,
        lats=lats_globe,
        lons=lons_globe,
        final_array=world_density,
        initial=False,
    )
    # 4. Create world map of cloud band density
    cworld_density, clons = cutil.add_cyclic_point(world_density, lons_globe)
    fig = create_worldmap_density(cworld_density, clons, lats_globe)
    fig.show()
    figname = f"{config['dir_figures']}/number_days_cloud_band_per_year{config['datetime_startdate'].year}_{config['datetime_enddate'].year}_world_cont7days.png"
    fig.savefig(figname, dpi=250, bbox_inches="tight")
