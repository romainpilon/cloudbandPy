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


import numpy as np
import sys
from matplotlib.cm import get_cmap
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

try:
    import cartopy.crs as ccrs
    import cartopy.util as cutil
except:
    print("Cartopy is not installed. Figure will not be produced.")

try:
    # better looking colorblind-proof colormaps
    import colorcet as cc
except:
    pass

from cloudbandPy.src.figure_tools import set_fontsize
from cloudbandPy.src.io_utilities import load_ymlfile, load_multiyears_data, openncfile, get_variable_lonlat_from_domain
from cloudbandPy.src.tracking import compute_density


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
    final_array[np.intersect1d(lats, lats2overlay, return_indices=True)[1][::-1], :] = array2overlay
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
    config_file = sys.argv[-1]
    config = load_ymlfile(config_file)

    # 1.1 Load one netCDF file to get global longitudes and latitudes
    ncfile = f"{config['varname_infilename']}_{config['startdate'][:4]}.nc"
    _, lons_globe, lats_globe, varin = openncfile(ncfile, config)

    # 1.2 Load cloud bands from the southern hemisphere (default config is for southern hemisphere)
    listofdatessh = load_multiyears_data(config, varname="listofdates")
    list_of_cloud_bandssh = load_multiyears_data(config, varname="list_of_cloud_bands")

    # 1.3 Get longitudes and latitudes of southern hemisphere domain
    _, lonssh, latssh = get_variable_lonlat_from_domain(
        varin, lons_globe, lats_globe, config["lon_west"], config["lon_east"], config["lat_north"], config["lat_south"]
    )
    # 1.4 Compute density for the southern hemisphere
    ntot_cbsh, densitysh = compute_density(
        lats=latssh, lons=lonssh, dates=listofdatessh, list_of_cloud_bands=list_of_cloud_bandssh
    )

    # 2.1 Load cloud bands and dates from the northern hemisphere
    config["domain"] = "northernhemisphere"
    config["lat_north"] = 50
    config["lat_south"] = 10
    listofdatesnh = load_multiyears_data(config, varname="listofdates")
    list_of_cloud_bandsnh = load_multiyears_data(config, varname="list_of_cloud_bands")
    # 2.2 Get longitudes and latitudes of northern hemisphere domain
    _, lonsnh, latsnh = get_variable_lonlat_from_domain(
        varin, lons_globe, lats_globe, config["lon_west"], config["lon_east"], config["lat_north"], config["lat_south"]
    )
    # 2.3 Compute density for the northern hemisphere
    ntot_cbnh, densitynh = compute_density(
        lats=latsnh, lons=lonsnh, dates=listofdatesnh, list_of_cloud_bands=list_of_cloud_bandsnh
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
    figname = f"{config['dir_figures']}/number_days_cloud_band_per_year{config['startdate'][:4]}_{config['enddate'][:4]}_world_cont7days.png"
    fig.savefig(figname, dpi=250, bbox_inches="tight")
