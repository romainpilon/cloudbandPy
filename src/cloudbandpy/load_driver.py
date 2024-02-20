#!/usr/bin/env python
# coding: utf-8

import logging
import numpy as np

from .io_utilities import (
    logging_setup,
    load_dataset,
    load_data_from_saved_var_files,
    load_ymlfile,
)
# from .time_utilities import create_list_of_dates
from .misc import compute_resolution

logging_setup()

def run_load_data(config: dict):
    logger = logging.getLogger("load_driver.run_load_data")
    logger.info("Loading data and parameters ")
    # Loading of the parameters to set the specific parameters for the studied hemisphere
    parameters = load_ymlfile(config["parameters_file"])
    # Load data from netcdf files or from saved files
    if not config["load_saved_files"]:
        # Load file(s) and variable: open and load OLR from ERA5 netcdf file(s)
        # variable2process will have the length of the period with the timestep "period_detection" from config__.yml
        # ie. the same length of "listofdates"
        variable2process, lons, lats = load_dataset(config)
    else:
        # Load from saved files
        logger.info(f"Use data saved in {config['saved_dirpath']}")
        # todo make is more general, eg for a specific domain
        lons = np.load(f"{config['saved_dirpath']}/lons_{config['domain']}.npy")
        lats = np.load(f"{config['saved_dirpath']}/lats_{config['domain']}.npy")
        variable2process = load_data_from_saved_var_files(config, varname="daily_variable")

    resolution = compute_resolution(lons, lats)

    if config["select_djfm"]:
        logger.info("DJFM period selected. Subsetting the data.")
        index_djfm = [idx for idx, el in enumerate(listofdates) if el.month in [1, 2, 3, 12]]
        listofdates = listofdates[index_djfm]
        variable2process = variable2process[index_djfm]

    return variable2process, parameters, lats, lons, resolution
