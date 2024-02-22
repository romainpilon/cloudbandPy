#!/usr/bin/env python
# coding: utf-8

from functools import reduce
import logging
import numpy as np

try:
    import cartopy.crs as ccrs
    from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
    LON_FORMAT = LongitudeFormatter(zero_direction_label=True, degree_symbol="")
    LAT_FORMAT = LatitudeFormatter(degree_symbol="")
except ModuleNotFoundError:
    print("Cartopy is not installed. Figure will not be produced.")

import matplotlib.pyplot as plt
from matplotlib.patches import ConnectionPatch
from matplotlib.ticker import MultipleLocator
from typing import Optional, Set

from .cloudband import CloudBand
from .figure_tools import set_fontsize
from .cb_detection import compute_blob_area
from .misc import wrapTo180


logger = logging.getLogger(__name__)


def findCloud(dates, name) -> Optional[CloudBand]:
    """Find a cloud using its ID in the complete list of dates and clouds"""
    for d in dates:
        for c in d:
            if c.id_ == name:
                return c
    return None


def tracking(list_of_cloud_bands, resolution, overlapfactor: float = 0.1) -> list:
    """
    Allows to get the parents of each clouds if they have any.
    Each cloud band are compared with whatever cloud bands are present the previous day
    through intersection -> they can have a parent or more,
    Then each parents are compared with cloud abnds of the day whether they intersect
    --> allows a two-way parenting identification
    
    By default, we day that we want at least 10% of overlap: subjective value.
    If no value -> possibility of 1 pixel overlap, but also it may allow a better temporal connection between cloud bands
    """
    logger.info("Inheritance tracking in progress")
    list_tracked_cloudband = list_of_cloud_bands.copy()  # copy to avoid side effects
    for idx, clouds in enumerate(list_of_cloud_bands):
        if len(clouds):
            for icloud in clouds:
                # look for parents, starting on second date
                parents: Set[str] = set()
                if idx > 0 and len(list_tracked_cloudband[idx - 1]):
                    for parent_cloud in list_of_cloud_bands[idx - 1]:
                        if is_in(parent_cloud, icloud, resolution, overlapfactor):
                            parents.add(parent_cloud.id_)
                        if is_in(icloud, parent_cloud, resolution, overlapfactor):
                            parents.add(parent_cloud.id_)
                icloud.parents = parents
                # print("cb_id_", icloud.id_, "cloud.parents", icloud.parents)
    logger.info("Inheritance tracking done")
    return list_tracked_cloudband


def is_in(orig: "CloudBand", other: "CloudBand", resolution: np.ndarray, overlapfactor: float) -> bool:
    """Check whether the cloud band is in (overlayed over) another cloud band"""
    intersection = orig.cloud_band_array * other.cloud_band_array
    area_intersection = compute_blob_area(intersection, 1, resolution)
    # Plot overlap of cloud bands
    # import matplotlib.pyplot as plt
    # plt.figure()
    # plt.imshow(self.cloud_band_array, alpha=0.5)
    # plt.imshow(other.cloud_band_array, alpha=0.5)
    # plt.title(str(area_intersection/self.area))
    # plt.show(block=True)
    if area_intersection > overlapfactor * orig.area:
        return True
    else:
        return False


def plot_tracking_on_map(
    list_of_cloud_bands: list,
    lons: np.ndarray,
    lats: np.ndarray,
    listofdates: list,
    config: dict,
    show: str = True,
    save: str = False,
):
    """Plot connection between cloud bands on maps.
    It will shows as many sublpots as days.
    'listofdates' is here to set the date on each panel. Date of cb in 'list_of_cloud_bands' does not exist if no cb"""
    set_fontsize(size=16)
    colors = ["red", "blue", "yellowgreen", "goldenrod", "darkturquoise", "mediumpurple", "darkorange"]
    cid = 0
    fig, axes = plt.subplots(
        nrows=len(list_of_cloud_bands),
        ncols=1,
        subplot_kw={"projection": ccrs.PlateCarree(central_longitude=180)},
        sharex=True,
        figsize=(10, 28),
    )
    lat_north, lat_south = round(lats[0]), round(lats[-1])
    lonticks = np.concatenate((np.arange(20, 180, 40), np.arange(-200, 0, 40)))
    latticks = np.arange(-90, 110, 20)
    for inc, ax in enumerate(axes):
        # display image
        if len(list_of_cloud_bands[inc]):  # only build an image if we have clouds
            map = list_of_cloud_bands[inc][0].cloud_band_array
            for i, m in enumerate(list_of_cloud_bands[inc][1:]):
                map = map + (i + 2) * m.cloud_band_array
            colorband = ["forestgreen", "deepskyblue"]
            masked_map = np.ma.masked_where(map == 0, map)
            ax.contourf(lons,
                        lats,
                        masked_map,
                        transform=ccrs.PlateCarree(),
                        levels=range(4),
                        alpha=0.95,
                        colors=colorband[: masked_map.max()])
        else:  # no cloud band: we show an empty array made out the first cloud band array in the list
            emap = np.copy([el for el in list_of_cloud_bands if len(el)][0][0].cloud_band_array)
            emap[emap != 0] = 0
            ax.contourf(lons, lats, np.ma.masked_where(emap == 0, emap), transform=ccrs.PlateCarree(), levels=range(4))
        #
        ax.text(
            0.95,
            0.75,
            listofdates[inc].strftime("%Y-%m-%d"),
            verticalalignment="bottom",
            horizontalalignment="right",
            transform=ax.transAxes,
            zorder=1,
            bbox={"facecolor": "white", "edgecolor": "white", "pad": 0.5},
        )
        ax.set_xticks(lonticks, crs=ccrs.PlateCarree())
        ax.set_yticks(latticks, crs=ccrs.PlateCarree())
        ax.xaxis.set_major_formatter(LON_FORMAT)
        ax.yaxis.set_major_formatter(LAT_FORMAT)
        ax.minorticks_on()
        ax.xaxis.set_minor_locator(MultipleLocator(5))
        ax.xaxis.set_major_locator(MultipleLocator(40))
        ax.set_extent([round(wrapTo180(lons)[-1]), round(wrapTo180(lons)[0]), lat_south, lat_north])
        ax.set_ylim([lat_south, lat_north])
        ax.coastlines(color="#474747", zorder=0)
        # links between clouds
        for cloud in list_of_cloud_bands[inc]:
            # y0, x0 = cloud.lon_centroid
            lon0 = cloud.lon_centroid
            lat0 = cloud.lat_centroid
            xyA = ccrs.PlateCarree(central_longitude=180).transform_point(lon0, lat0, ccrs.PlateCarree())
            for parent_id in cloud.parents:
                parent = findCloud(list_of_cloud_bands, parent_id)
                lon1 = parent.lon_centroid
                lat1 = parent.lat_centroid
                xyB = ccrs.PlateCarree(central_longitude=180).transform_point(lon1, lat1, ccrs.PlateCarree())
                ## Add a point at the center of mass
                con = ConnectionPatch(
                    xyA=xyA,
                    xyB=xyB,
                    coordsA="data",
                    coordsB="data",
                    axesA=ax,
                    axesB=axes[inc - 1],
                    color=colors[cid % len(colors)],
                    linewidth=3,
                    zorder=2,
                )
                cid += 1
                ax.add_artist(con)
    #
    fig.subplots_adjust(wspace=0.25, hspace=0.025)
    if show:
        plt.show(block=False)
    if save:
        plt.savefig(
            f"{config['dir_figures']}/tracking_"
            + listofdates[0].strftime("%Y-%m-%d")
            + "_"
            + listofdates[-1].strftime("%Y-%m-%d")
            + ".png",
            dpi=250,
            bbox_inches="tight",
        )
    return


def plot_pix(list_of_cloud_bands: list):
    """Same as previous function without creating a cartopy map"""
    colors = ["red", "blue", "yellowgreen", "goldenrod", "darkturquoise", "mediumpurple", "darkorange"]
    cid = 0
    _, axes = plt.subplots(len(list_of_cloud_bands), 1)
    for inc, ax in enumerate(axes):
        # display image
        if len(list_of_cloud_bands[inc]):  # only build an image if we have clouds
            map = list_of_cloud_bands[inc][0].cloud_band_array
            for i, m in enumerate(list_of_cloud_bands[inc][1:]):
                map = map + (i + 2) * m.cloud_band_array
            ax.imshow(map, cmap="tab20_r")
        # links between clouds
        for cloud in list_of_cloud_bands[inc]:
            # ax.plot(cloud.lon_centroid, cloud.lat_centroid, ".g", markersize=10)
            for parent_id in cloud.parents:
                parent = findCloud(list_of_cloud_bands, parent_id)
                con = ConnectionPatch(
                    xyA=(cloud.lon_centroid,cloud.lat_centroid),
                    xyB=(parent.lon_centroid,parent.lat_centroid),
                    coordsA="data",
                    coordsB="data",
                    axesA=ax,
                    axesB=axes[inc - 1],
                    color=colors[cid % len(colors)],
                    linewidth=2,
                )
                cid += 1
                ax.add_artist(con)
    plt.show(block=False)
    return


def compute_density(dates: list, list_of_cloud_bands: list) -> np.ndarray:
    """
    Compute the total number of cloud bands per grid point and the mean number of cloud band per day per year
    Return:
        - ntot_cb: total number of cloud bands per grid point
        - density: mean number of cloud band per day per year over the period
    """
    logger = logging.getLogger("tracking.compute_density")
    # To set the shape of the ntot_cb and density,
    # we need the shape of an array of cloud band (= [len(lons), len(lats)] of domain)
    # Get the first cloud band of the period
    onecloudband = reduce(lambda s1, s2: s1 or s2, list_of_cloud_bands)[0]
    if onecloudband == None or []:
        logger.warning("No cloud band has been detected")
    ntot_cb = np.zeros(onecloudband.cloud_band_array.shape)
    density = np.zeros(onecloudband.cloud_band_array.shape)
    for itime in range(len(dates)):
        for icb in enumerate(list_of_cloud_bands[itime]):
            ntot_cb += icb[1].cloud_band_array
    numberofyear = len(set([el.year for el in dates]))
    # check if the period covers one or multiple full years
    if dates[0].month == 1 and dates[0].day == 1 and dates[-1].month == 12 and dates[-1].day == 31:
        density = np.divide(ntot_cb, numberofyear)
    else:
        logger.warning(
            "Period not covering a full year. You will get, for each grid point, the total of cloud bands divided by the number of days"
        )
    return ntot_cb, density
