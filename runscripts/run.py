#!/usr/bin/env python
# coding: utf-8
"""
This script allows to run the detection algorithm.

Run cloudbandpy/runscripts/run.py cloudbandpy/config/config_cbworkflow_southPacific.yml
"""

import logging
import os

from cloudbandpy.load_driver import run_load_data

from cloudbandpy.cb_detection import detection_workflow
from cloudbandpy.figure_tools import *
from cloudbandpy.io_utilities import (
    logging_setup,
    load_ymlfile,
    pickle_save_cloudbands,
)
from cloudbandpy.misc import parse_arguments
from cloudbandpy.tracking import tracking, compute_density, plot_tracking_on_map

logging_setup()
logger = logging.getLogger(__name__)


def run(config: dict):
    # Load data and parameters
    variable2process, parameters, listofdates, lats, lons, resolution = run_load_data(config)
    # Cloud band detection
    (
        fill_binarize_data,
        dilation,
        labelled_blobs,
        labelled_candidates,
        cloud_bands_over_time,
        list_of_cloud_bands,
    ) = detection_workflow(
        var2process=variable2process,
        parameters=parameters,
        latitudes=lats,
        longitudes=lons,
        resolution=resolution,
        listofdates=listofdates,
        config=config,
    )
    # Tracking
    if config["run_inheritance_tracking"]:
        # Update the list of cloud bands
        list_of_cloud_bands = tracking(list_of_cloud_bands, resolution, overlapfactor=parameters["othresh"])
    # Save cloud bands
    if config["save_listcloudbands"]:
        pickle_save_cloudbands(config, list_of_cloud_bands)
    return (
        listofdates,
        lats,
        lons,
        resolution,
        variable2process,
        fill_binarize_data,
        dilation,
        labelled_blobs,
        labelled_candidates,
        cloud_bands_over_time,
        list_of_cloud_bands,
    )


if __name__ == "__main__":
    # Load configuration file
    args = parse_arguments()
    config_file = args.config_file
    config = load_ymlfile(config_file, isconfigfile=True)
    # Run detection
    (
        listofdates,
        lats,
        lons,
        resolution,
        variable2process,
        fill_binarize_data,
        dilation,
        labelled_blobs,
        labelled_candidates,
        cloud_bands_over_time,
        list_of_cloud_bands,
    ) = run(config)

    # Visualization
    if config["fig_detection_process"]:
        os.makedirs(config["dir_figures"], exist_ok=True)
        show_blob_detection_process(
            lons,
            lats,
            OLR_THRESHOLD=parameters["OLR_THRESHOLD"],
            variable2process=variable2process,
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
            variable2process, cloud_bands_over_time, lons, lats, listofdates, config, show=True, save=True
        )

    if config["fig_overlay_cloudband"]:
        # Overlay of cloud bands
        os.makedirs(config["dir_figures"], exist_ok=True)
        plot_overlay_of_cloudbands(
            cloud_bands_over_time, config, lons=lons, lats=lats, transparency=0.1, show=True, save=True
        )

    if config["fig_inheritance_tracking"] and config["run_inheritance_tracking"]:
        # Plot tracking on maps. It will shows as many sublpots as days
        # needs Tracking
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
            figname=f"{config['dir_figures']}/number_days_cloud_band_per_year{config['datetime_startdate'].year}_{config['datetime_enddate'].year}_{config['domain']}",
            figtitle="",
            levels=np.arange(0, np.max(density) + 1, 1),
            coastlinecolor="#404040",
            cmap="magma_r",
            cbarlabel="Number of cloud band days per year",
            show=True,
            save=True,
        )

    if config["fig_show_bbox_around_blobs"]:
        # To use for a few days max, to see the boundary box and otrientation of labelled objects
        os.makedirs(config["dir_figures"], exist_ok=True)
        for idx, itime in enumerate(listofdates):
            plot_bbox_around_blobs(labelled_candidates[idx], date=itime, config=config, show=True, save=True)
