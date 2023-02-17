#!/usr/bin/env python
# coding: utf-8
"""
This script allows to run the detection algorithm.
Run CloudBandDetection/runscripts/run_.. .py for appropriate use.
"""

import logging
import numpy as np
import os, sys

from blob_tools import detection_workflow
from figure_tools import *
from io_utilities import (
    logging_setup,
    load_ymlfile,
    load_dataset,
    make_daily_average,
    npy_save_dates,
    npy_save_dailyvar,
    pickle_save_cloudbands,
)
from time_utilities import create_list_of_dates
from utilities import compute_resolution
from tracking import tracking, plot_tracking_on_map, compute_density

logging_setup()
logger = logging.getLogger(__name__)

# 1 --> Load config and parameters file
config_file = sys.argv[-1]
config = load_ymlfile(config_file, isconfigfile=True)
parameters = load_ymlfile(config["parameters_file"])

# 2 --> Load data
# Load file(s) and variable: open and load OLR from ERA5 netcdf file(s)
variable2process, timein, lons, lats = load_dataset(config)
resolution = compute_resolution(lons, lats)
listofdates = create_list_of_dates(config)

# Create daily mean of the input variable?
if config["qd_var"]:
    daily_variable = make_daily_average(variable2process, timein, listofdates, config)

if config["select_djfm"]:
    logger.info("DJFM period selected. Subsetting the data.")
    index_djfm = [idx for idx, el in enumerate(listofdates) if el.month in [1, 2, 3, 12]]
    listofdates = listofdates[index_djfm]
    daily_variable = daily_variable[index_djfm]

# 3 --> Detection
(
    fill_binarize_data,
    dilation,
    labelled_blobs,
    labelled_candidates,
    cloud_bands_over_time,
    list_of_cloud_bands,
) = detection_workflow(
    var2process=daily_variable,
    parameters=parameters,
    latitudes=lats,
    longitudes=lons,
    resolution=resolution,
    listofdates=listofdates,
    config=config,
)

# 4 --> Tracking
# Get the list of tracked cloud bands per day. Each cloud can have one or several parents
# list_of_cloud_bands will have the same length as listofdates or cloud_bands_over_time
if config["run_inheritance_tracking"]:
    list_of_cloud_bands = tracking(list_of_cloud_bands, resolution, overlapfactor=parameters["othresh"])

# FIXME put in functions
# Saving data
# - save dates for cloud band density (todo could use date_number from cloud band object)
if config["save_listdates"]:
    npy_save_dates(config, listofdates)

# - save daily variable
if config["save_dailyvar"] and config["qd_var"]:
    npy_save_dailyvar(config, daily_variable)

# - save list of cloud bands
if config["save_listcloudbands"]:
    pickle_save_cloudbands(config, list_of_cloud_bands)


# Figures
if config["fig_detection_process"]:
    os.makedirs(config["dir_figures"], exist_ok=True)
    show_blob_detection_process(
        lons,
        lats,
        OLR_THRESHOLD=parameters["OLR_THRESHOLD"],
        variable2process=daily_variable,
        fill_binarize_data=fill_binarize_data,
        dilation=dilation,
        labelled_blobs=labelled_blobs,
        labelled_candidates=labelled_candidates,
        cloud_bands_over_time=cloud_bands_over_time,
        date2show=listofdates,
        config=config,
    )


if config["fig_time_evolution_object"]:
    # Time evolution of cloud bands (one panel per day, 16 days total)
    # you may change cloud_bands_over_time to labelled_candidates
    os.makedirs(config["dir_figures"], exist_ok=True)
    plot_time_evolution_blobs(
        blobs=cloud_bands_over_time,
        lons=lons,
        lats=lats,
        listofdates=listofdates,
        config=config,
        blobname="cloud_bands_over_time",
        show=True,
        save=True,
    )


if config["fig_time_evolution_var_cloudband"]:
    # Show cloud bands overlaid on OLR
    os.makedirs(config["dir_figures"], exist_ok=True)
    plot_time_evolution_inputvar_cloubdands(
        daily_variable, cloud_bands_over_time, lons, lats, listofdates, config, show=True, save=True
    )


if config["fig_overlay_cloudband"]:
    # Overlay of cloud bands
    os.makedirs(config["dir_figures"], exist_ok=True)
    plot_overlay_of_cloudbands(
        cloud_bands_over_time, config, lons=lons, lats=lats, transparency=0.1, show=True, save=True
    )


if config["fig_inheritance_tracking"] and config["run_inheritance_tracking"]:
    # Plot tracking on maps. It will shows as many sublpots as days
    os.makedirs(config["dir_figures"], exist_ok=True)
    plot_tracking_on_map(
        list_of_cloud_bands=list_of_cloud_bands,
        lons=lons,
        lats=lats,
        listofdates=listofdates,
        config=config,
        show=True,
        save=True,
    )


if config["fig_density"] and config["run_inheritance_tracking"]:
    logger.info("Density plot")
    os.makedirs(config["dir_figures"], exist_ok=True)
    _, density = compute_density(lats, lons, listofdates, list_of_cloud_bands)
    check_figure(
        lons,
        lats,
        variable=np.ma.masked_where(density == 0, density),
        figname=f"{config['dir_figures']}/number_days_cloud_band_per_year{config['datetime_startdate'].year}_{config['domain']}",
        figtitle="",
        levels=np.arange(0, np.max(density) + 1, 1),
        coastlinecolor="#404040",
        cmap="magma_r",
        cbarlabel="Number of cloud band days per year",
        show=True,
        save=True,
    )


if config["fig_show_bbox_around_blobs"]:
    os.makedirs(config["dir_figures"], exist_ok=True)
    for idx, itime in enumerate(listofdates):
        plot_bbox_around_blobs(labelled_candidates[idx], date=itime, config=config, show=True, save=True)

logger.info("End of detections script")
