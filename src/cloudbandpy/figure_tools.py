#!/usr/bin/env python
# coding: utf-8
"""
A set of function to create different figures
"""

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
from matplotlib.ticker import MultipleLocator
import matplotlib as mpl
from skimage import measure

from .misc import wrapTo180


def set_fontsize(size: int = 11):
    """Set fontsize on the figure"""
    mpl.rcParams["text.usetex"] = False
    mpl.rcParams["font.size"] = size
    mpl.rcParams["axes.titlesize"] = size
    mpl.rcParams["axes.labelsize"] = size
    mpl.rcParams["xtick.labelsize"] = size
    mpl.rcParams["ytick.labelsize"] = size
    mpl.rcParams["legend.fontsize"] = size
    mpl.rcParams["figure.titlesize"] = size
    return


def set_presentation_style():
    # Set the figure facecolor and edgecolor to black
    mpl.rcParams["figure.facecolor"] = "#2A2A2A"
    mpl.rcParams["figure.edgecolor"] = "#2A2A2A"
    # Set the text color to white
    mpl.rcParams["text.color"] = "white"
    # Set the tick color to white
    mpl.rcParams["xtick.color"] = "white"
    mpl.rcParams["ytick.color"] = "white"
    # Set the grid color to white
    mpl.rcParams["grid.color"] = "white"
    # Set the axis spines color to white
    mpl.rcParams["axes.edgecolor"] = "white"
    # Set the legend facecolor and edgecolor to black
    mpl.rcParams["legend.facecolor"] = "#2A2A2A"
    mpl.rcParams["legend.edgecolor"] = "#2A2A2A"
    # Set the savefig facecolor and edgecolor to black
    mpl.rcParams["savefig.facecolor"] = "#2A2A2A"
    mpl.rcParams["savefig.edgecolor"] = "#2A2A2A"
    mpl.rcParams["font.family"] = "Futura"
    mpl.rcParams["axes.labelcolor"] = "white"
    return


def check_figure(
    lons: np.ndarray,
    lats: np.ndarray,
    variable: np.ndarray,
    figname: str,
    figtitle: str = "Outgoing longwave radiation",
    levels=10,
    cmap="Greys",
    date2show=None,
    coastlinecolor=None,
    threshold=None,
    cbarlabel: str = None,
    cbarticks=None,
    show: bool = True,
    save: bool = True,
):
    """
    Allows to plot one panel showing any data (array) that you want to see on a map
    eg: check_figure(lons, lats, variable2process, levels=range(100, 305, 5), date2show=itime, coastlinecolor='white', show=False, save=True)
    eg: check_figure(lons, lats, variable2process, levels=range(80, 310, 10), threshold=[OLR_THRESHOLD, OLR_MAX_THRESHOLD])
    eg: check_figure(lons, lats, labelled_candidates[idx], coastlinecolor="black", levels=len(labelled_candidates[idx])-1, cmap="tab20_r")
    """
    set_fontsize()
    fig, ax = plt.subplots(1, 1, subplot_kw={"projection": ccrs.PlateCarree(central_longitude=180)}, figsize=(10, 8))
    fill = ax.contourf(lons, lats, variable, transform=ccrs.PlateCarree(), levels=levels, cmap=cmap)
    if threshold:
        ax.contour(
            lons, lats, variable, transform=ccrs.PlateCarree(), levels=list(threshold), colors="white", linewidths=1
        )
    #
    lonticks = np.concatenate((np.arange(0, 180, 30), np.arange(-180, 0, 30)))
    latticks = np.arange(-90, 110, 20)
    ax.set_xticks(lonticks, crs=ccrs.PlateCarree())
    ax.set_yticks(latticks, crs=ccrs.PlateCarree())
    ax.xaxis.set_major_formatter(LON_FORMAT)
    ax.yaxis.set_major_formatter(LAT_FORMAT)
    lat_north, lat_south = round(lats[0]), round(lats[-1])
    ax.set_extent([wrapTo180(lons)[-1], wrapTo180(lons)[0], lat_south, lat_north])
    ax.set_ylim([lat_south, lat_north])
    if date2show and len(figtitle):
        title = f"{figtitle} - {date2show.strftime('%Y-%m-%d-%H:%M')}"
        ax.set_title(title, loc="left", color="k")
    #
    if not coastlinecolor:
        ax.coastlines("50m")
    else:
        ax.coastlines("50m", color=coastlinecolor)
    cbar = fig.colorbar(fill, orientation="horizontal")
    if cbarlabel:
        cbar.set_label(cbarlabel)
    if cbarticks:
        cbar.set_ticks(cbarticks)
    if show:
        plt.show(block=False)
    if save:
        if date2show:
            plt.savefig(
                f"{figname}_{date2show.strftime('%Y')}-{date2show.strftime('%m')}{date2show.strftime('%d')}-{date2show.strftime('%HH')}.png",
                dpi=300,
                bbox_inches="tight",
            )
        else:
            plt.savefig(f"{figname}.png", dpi=300, bbox_inches="tight")
    return


def show_blob_detection_process(
    lons: np.ndarray,
    lats: np.ndarray,
    OLR_THRESHOLD,
    variable2process: np.ndarray,
    fill_binarize_data: np.ndarray,
    dilation: np.ndarray,
    labelled_blobs: np.ndarray,
    labelled_candidates: np.ndarray,
    cloud_bands_over_time: np.ndarray,
    date2show,
    config,
):
    """
    For the South Pacific, create a panel for each step of the detection method:
    -> variable (OLR), variable + threshold, binary data, dilation, label, cloud band
    """
    if len(date2show) > 1:
        print("Warning!!! You must choose only 1 date to see the selection process.")
    lat_north, lat_south = round(lats[0]), round(lats[-1])
    fig, ax = plt.subplots(
        3,
        2,
        figsize=(9, 6.5),
        subplot_kw={"projection": ccrs.PlateCarree(central_longitude=180)},
        sharey=True,
        sharex=True,
    )
    conto = ax[0, 0].contourf(
        lons,
        lats,
        variable2process[0],
        transform=ccrs.PlateCarree(),
        levels=range(100, 300, 10),
        cmap="binary",
        extend="both",
    )
    ax[0, 0].contour(
        lons,
        lats,
        variable2process[0],
        transform=ccrs.PlateCarree(),
        levels=list([OLR_THRESHOLD]),
        colors="yellow",
        linewidths=0.6,
    )
    ax[0, 0].set_title(r"a) OLR (W.m$^{-2}$) + threshold", loc="left", fontsize=11)
    #
    ax[0, 1].contourf(
        lons,
        lats,
        np.ma.masked_where(fill_binarize_data[0] == 0, fill_binarize_data[0]),
        transform=ccrs.PlateCarree(),
        cmap="viridis",
    )
    ax[0, 1].set_title(r"b) Binarization", loc="left", fontsize=11)
    #
    ax[1, 0].contourf(
        lons, lats, np.ma.masked_where(dilation[0] == 0, dilation[0]), transform=ccrs.PlateCarree(), cmap="viridis"
    )
    ax[1, 0].set_title(r"c) Dilation", loc="left", fontsize=11)
    #
    ax[1, 1].contourf(
        lons,
        lats,
        np.ma.masked_where(labelled_blobs[0] == 0, labelled_blobs[0]),
        transform=ccrs.PlateCarree(),
        cmap="tab20_r",
    )
    ax[1, 1].set_title(r"d) Labeling", loc="left", fontsize=11)
    #
    ax[2, 0].contourf(
        lons,
        lats,
        np.ma.masked_where(labelled_candidates[0] == 0, labelled_candidates[0]),
        transform=ccrs.PlateCarree(),
        levels=len(labelled_candidates[0]) - 1,
        cmap="tab20_r",
    )
    ax[2, 0].set_title(r"e) Filtering out small cloud systems", loc="left", fontsize=11)
    #
    ax[2, 1].contourf(
        lons,
        lats,
        np.ma.masked_where(cloud_bands_over_time[0] == 0, cloud_bands_over_time[0]),
        transform=ccrs.PlateCarree(),
        cmap="viridis",
    )
    ax[2, 1].set_title(r"f) Cloud bands", loc="left", fontsize=11)
    #
    lonticks = np.concatenate((np.arange(0, 180, 30), np.arange(-180, 0, 30)))
    latticks = np.arange(-90, 110, 20)
    for axid in ax.ravel():
        axid.set_xticks(lonticks, crs=ccrs.PlateCarree())
        axid.set_yticks(latticks, crs=ccrs.PlateCarree())
        axid.xaxis.set_major_formatter(LON_FORMAT)
        axid.yaxis.set_major_formatter(LAT_FORMAT)
        axid.minorticks_on()
        axid.coastlines("50m", color="#404040")
        axid.set_extent([wrapTo180(lons)[-1], wrapTo180(lons)[0], lat_south, lat_north])
        axid.set_ylim([lat_south, lat_north])
    #
    ax[0, 0].coastlines("50m", color="#FFFFFF")
    fig.subplots_adjust(wspace=0.35, hspace=0.01)
    # [l,b,w,h]
    cax = ax[0, 0].inset_axes([1.01, 0.0, 0.03, 0.99])
    cbar = fig.colorbar(conto, ax=ax[0, 0], cax=cax)
    cbar.set_ticks(np.arange(100, 340, 40))
    plt.show(block=False)
    plt.savefig(
        f"{config['dir_figures']}/blob_detection_process_{date2show[0].strftime('%d')}-{date2show[0].strftime('%m')}-{date2show[0].strftime('%Y')}_{config['domain']}.png",
        dpi=300,
        bbox_inches="tight",
    )
    return


def plot_bbox_around_blobs(mapofblobs: np.ndarray, date, config: dict, show: bool = False, save: bool = False):
    """
    This function creates a figure to show boundary box, axis of elipse (around each blob), and angle of ellipse.
    The purpose here is just to monitor what the code does.
    Orientation is calculated between the horizontal and the the minor of the ellipse (around the blob)
    Angle is + or - 90 to be human readable, ie.
        0/90°: top-right quadrant of a circle
        -0/-90: bottom right-quadrant of a circle
    """
    set_fontsize()
    _, ax = plt.subplots()
    ax.imshow(mapofblobs, cmap=plt.cm.gray)
    blobs_regionprops = measure.regionprops(mapofblobs)
    for iblob in blobs_regionprops:
        y0, x0 = iblob.centroid
        x1 = x0 + np.cos(iblob.orientation) * 0.5 * iblob.axis_minor_length
        y1 = y0 - np.sin(iblob.orientation) * 0.5 * iblob.axis_minor_length
        x2 = x0 - np.sin(iblob.orientation) * 0.5 * iblob.axis_major_length
        y2 = y0 - np.cos(iblob.orientation) * 0.5 * iblob.axis_major_length
        ax.plot((x0, x2), (y0, y2), "--r", linewidth=2.5)
        ax.plot(x0, y0, ".g", markersize=15)
        if config["hemisphere"] == "south":
            angle_deg = (iblob.orientation * 360) / (2 * np.pi) - 90
        elif config["hemisphere"] == "north":
            angle_deg = (iblob.orientation * 360) / (2 * np.pi) + 90
        ax.text(x0 + 0.5, y0 + 0.5, str(int(angle_deg)) + r"°", color="pink")
        topindex, leftindex, bottomindex, rightindex = iblob.bbox
        bx = (leftindex, rightindex, rightindex, leftindex, leftindex)
        by = (topindex, topindex, bottomindex, bottomindex, topindex)
        ax.plot(bx, by, "-b", linewidth=2.5)
    if show:
        plt.show(block=False)
    if save:
        plt.savefig(
            f"{config['dir_figures']}/bbox_around_blobs_{date.strftime('%Y-%m-%d')}_{config['domain']}.png",
            dpi=300,
            bbox_inches="tight",
        )
    return


def plot_overlay_of_cloudbands(
    mpas_of_cloud_bands: list,
    config: dict,
    lons: np.ndarray,
    lats: np.ndarray,
    transparency: float = 0.1,
    show=True,
    save=False,
):
    """Overlay all cloud bands on one map"""
    set_fontsize()
    lat_north, lat_south = round(lats[0]), round(lats[-1])
    _, ax = plt.subplots(1, 1, subplot_kw={"projection": ccrs.PlateCarree(central_longitude=180)}, figsize=(10, 8))
    for _, el in enumerate(mpas_of_cloud_bands):
        ax.contourf(
            lons,
            lats,
            np.ma.masked_where(el == 0, el),
            transform=ccrs.PlateCarree(),
            levels=len(el),
            alpha=transparency,
            cmap="YlOrRd_r",
        )
    #
    lonticks = np.concatenate((np.arange(0, 180, 30), np.arange(-180, 0, 30)))
    latticks = np.arange(-90, 110, 20)
    ax.set_xticks(lonticks, crs=ccrs.PlateCarree())
    ax.set_yticks(latticks, crs=ccrs.PlateCarree())
    ax.xaxis.set_major_formatter(LON_FORMAT)
    ax.yaxis.set_major_formatter(LAT_FORMAT)
    ax.minorticks_on()
    ax.xaxis.set_minor_locator(MultipleLocator(5))
    ax.set_extent([wrapTo180(lons)[-1], wrapTo180(lons)[0], lat_south, lat_north])
    ax.set_ylim([lat_south, lat_north])
    ax.coastlines("50m", color="#404040")
    dateformat = "%Y-%m-%d"
    ax.set_title(
        f"Overlay of cloud bands from {config['datetime_startdate'].strftime(dateformat)} to {config['datetime_enddate'].strftime(dateformat)}",
        loc="left",
    )
    if show:
        plt.show(block=False)
    if save:
        plt.savefig(
            f"{config['dir_figures']}/cloud_bands_overlay_{config['startdate']}_{config['enddate']}_{config['domain']}.png",
            dpi=250,
            bbox_inches="tight",
        )
    return


def plot_time_evolution_blobs(
    blobs: np.ndarray,
    lons: np.ndarray,
    lats: np.ndarray,
    listofdates,
    config: dict,
    blobname: str = "cloudband",
    cmap="tab10",
    show=False,
    save=False,
):
    """
    Figure to show evolution of clouds bands during 15 days
    Plot one date per panel
    -> blobs can be labelled_blobs, labelled_candidates or cloud_bands_over_time
    """
    logger = logging.getLogger("figure_tools.plot_time_evolution_blobs")
    nrows = 4
    ncols = 4
    if len(listofdates) != nrows * ncols:
        logger.warning("")
        raise ValueError(f"This figure is made to show 16 days. Length of your data is {len(blobs)}")
    else:
        lat_north, lat_south = round(lats[0]), round(lats[-1])
        daystart = f"{listofdates[0].day}-{listofdates[0].strftime('%m')}-{listofdates[0].year}"
        dayend = f"{listofdates[-1].day}-{listofdates[-1].strftime('%m')}-{listofdates[-1].year}"
        #
        fig, axs = plt.subplots(
            nrows=nrows,
            ncols=ncols,
            subplot_kw={"projection": ccrs.PlateCarree(central_longitude=180)},
            figsize=(14, 8),
        )
        for inc, ax in enumerate(axs.ravel()):
            ax.contourf(
                lons,
                lats,
                np.ma.masked_where(blobs[inc] == 0, blobs[inc]),
                transform=ccrs.PlateCarree(),
                levels=range(20),
                cmap=cmap,
            )
            lonticks = np.concatenate((np.arange(20, 180, 40), np.arange(-200, 0, 40)))
            latticks = np.arange(-90, 110, 20)
            ax.set_xticks(lonticks, crs=ccrs.PlateCarree())
            ax.set_yticks(latticks, crs=ccrs.PlateCarree())
            ax.xaxis.set_major_formatter(LON_FORMAT)
            ax.yaxis.set_major_formatter(LAT_FORMAT)
            ax.minorticks_on()
            ax.xaxis.set_minor_locator(MultipleLocator(5))
            ax.xaxis.set_major_locator(MultipleLocator(40))
            ax.set_extent([wrapTo180(lons)[-1], wrapTo180(lons)[0], lat_south, lat_north])
            ax.set_ylim([lat_south, lat_north])
            ax.coastlines(color="#474747")
            # \u200A is a half space
            ax.set_title(
                f"{listofdates[inc].day}\u200A{listofdates[inc].strftime('%b')}\u200A{listofdates[inc].year}",
                loc="left",
            )
        #
        fig.subplots_adjust(wspace=0.25, hspace=0.025)
        if show:
            plt.show(block=False)
        if save:
            plt.savefig(
                f"{config['dir_figures']}/{blobname}_{daystart}_to_{dayend}_{config['domain']}.png",
                dpi=250,
                bbox_inches="tight",
            )
    return


def plot_time_evolution_inputvar_cloubdands(
    input_var: np.ndarray,
    cloud_bands_over_time: np.ndarray,
    lons: np.ndarray,
    lats: np.ndarray,
    listofdates,
    config: dict,
    show: bool = True,
    save: bool = False,
):
    """
    Figure to show evolution of clouds bands over the input variale during 15 days
    Plot one date per panel.
    -> by default, the input variable is OLR
    """
    nrows = 4
    ncols = 4
    lat_north, lat_south = round(lats[0]), round(lats[-1])
    daystart = f"{listofdates[0].day}-{listofdates[0].strftime('%m')}-{listofdates[0].year}"
    dayend = f"{listofdates[-1].day}-{listofdates[-1].strftime('%m')}-{listofdates[-1].year}"
    fig, axs = plt.subplots(
        nrows=nrows, ncols=ncols, subplot_kw={"projection": ccrs.PlateCarree(central_longitude=180)}, figsize=(13, 7)
    )
    for inc, ax in enumerate(axs.ravel()):
        ax.contourf(
            lons,
            lats,
            input_var[inc],
            transform=ccrs.PlateCarree(),
            levels=range(110, 300, 10),
            cmap="binary",
            extend="both",
        )
        ax.contourf(
            lons,
            lats,
            np.ma.masked_where(cloud_bands_over_time[inc] == 0, cloud_bands_over_time[inc]),
            transform=ccrs.PlateCarree(),
            levels=len(cloud_bands_over_time[inc]),
            cmap="RdYlBu",
            alpha=0.7,
        )
        lonticks = np.concatenate((np.arange(20, 180, 40), np.arange(-200, 0, 40)))
        latticks = np.arange(-90, 110, 20)
        ax.set_xticks(lonticks, crs=ccrs.PlateCarree())
        ax.set_yticks(latticks, crs=ccrs.PlateCarree())
        ax.xaxis.set_major_formatter(LON_FORMAT)
        ax.yaxis.set_major_formatter(LAT_FORMAT)
        ax.minorticks_on()
        ax.xaxis.set_minor_locator(MultipleLocator(5))
        ax.xaxis.set_major_locator(MultipleLocator(40))
        ax.set_extent([wrapTo180(lons)[-1], wrapTo180(lons)[0], lat_south, lat_north])
        ax.set_ylim([lat_south, lat_north])
        ax.coastlines(color="white")
        ax.set_title(f"{listofdates[inc].day} {listofdates[inc].strftime('%b')} {listofdates[inc].year}", loc="left")
    #
    fig.subplots_adjust(wspace=0.25, hspace=0.025)
    if show:
        plt.show(block=False)
    if save:
        plt.savefig(
            f"{config['dir_figures']}/OLR_CB_{daystart}_{dayend}_{config['domain']}.png", dpi=250, bbox_inches="tight"
        )
    return
