#!/usr/bin/env python
# coding: utf-8
"""
A set of functions to load different files: config, parameter files,
and dataset, and to subset variables
"""


import datetime as dt
import logging
import netCDF4 as nc
import numpy as np
import os
import pandas
import pickle
import yaml

from utilities import convert_olr_in_wm2, wrapTo180
from time_utilities import get_startendtimes_from_config


def logging_setup():
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s: %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.INFO)


def load_ymlfile(yml_file: str = None, isconfigfile: bool = False) -> dict:
    """
    Load a Yaml file.
    If it is the config file, update it with datetime_startdate and datetime_enddate
    If no config file, terminate the script
    """
    logger = logging.getLogger("io_utilities.load_ymlfile")
    # if no configuration file, set a default one
    if not yml_file or not os.path.exists(yml_file) or not os.path.isfile(yml_file):
        raise FileNotFoundError("Config file was not found or is a directory")
    # Open and read settings from yaml file
    stream = open(yml_file, "r")
    config = yaml.full_load(stream)
    # if file if configuration file, we add start/end dates in datetime format
    if isconfigfile:
        datetime_startdate, datetime_enddate = get_startendtimes_from_config(config)
        config.update(
            {
                "datetime_startdate": datetime_startdate,
                "datetime_enddate": datetime_enddate,
            }
        )
        logger.info("Configuration file loaded")
    else:
        logger.info("Parameters file loaded")
    return config


def openncfile(filename: str, config) -> tuple:
    """
    Open netcdf data and return time, lons, lats and variable.
    Note: netCDF4 file assumed to contain only one variable
    and to have a single level (ERA5 surface field)
    """
    filedirectory = config["clouddata_path"]
    varname = config["varname"]
    timecoord_name = config["timecoord_name"]
    xcoord_name = config["xcoord_name"]
    ycoord_name = config["ycoord_name"]
    olr_convert2wm2 = config["olr_convert2wm2"]
    if os.path.isdir(filedirectory) and os.path.isfile(filedirectory + "/" + filename):
        ds = nc.Dataset(filedirectory + "/" + filename, "r")
        variable = ds.variables[varname]
        # Convert into W.m^-2 if needed
        if olr_convert2wm2:
            variable = convert_olr_in_wm2(variable)
        time = nc.num2date(
            ds.variables[timecoord_name][:],
            ds.variables[timecoord_name].units,
            calendar=ds.variables[timecoord_name].calendar,
            only_use_cftime_datetimes=False,
        )
        lats = ds.variables[ycoord_name][...]
        lons = ds.variables[xcoord_name][...]
        return time, lons, lats, variable
    else:
        raise ValueError("Directory or file does not exist")


def load_dataset(config: dict) -> tuple:
    """
    Load netCDF4 data and time. It considers that the filenames are formatted as 'varname_infilename_year.nc'
    Args:
        - config file
    Returns:
        - variable4cb: input variable to get cloud bands from
        - timein: times from inputa data in datetime
        - lons, lats, array of longitudes and latitudes of the domain
    """
    logger = logging.getLogger("io_utilities.load_dataset")
    logger.info("Loading dataset")
    # Read configurations
    varname_infilename = config["varname_infilename"]
    #
    datetime_startdate = config["datetime_startdate"]
    datetime_enddate = config["datetime_enddate"]
    lat_north = config["lat_north"]
    lat_south = config["lat_south"]
    lon_west = config["lon_west"]
    lon_east = config["lon_east"]
    #
    year_start = datetime_startdate.year
    year_end = datetime_enddate.year
    variable = []
    timein = []
    for iyear in range(int(year_start), int(year_end) + 1):
        logger.info(f"Loading {iyear} --> {year_end}")
        # construct the filename
        filename = f"{varname_infilename}_{iyear}.nc"
        # load a file per year
        time_tmp, lons_in, lats_in, variable_tmp = openncfile(filename, config)
        timein = np.append(timein, time_tmp, axis=0)
        del time_tmp
        variable.append(np.asarray(variable_tmp))
    #
    del variable_tmp
    # Transform list of N arrays into an array with a time dimension equal to N
    variable = np.vstack(variable)
    variable4cb, lons, lats = get_variable_lonlat_from_domain(
        variable, lons_in, lats_in, lon_west, lon_east, lat_north, lat_south
    )
    del variable
    logger.info("Dataset loaded")
    return variable4cb, timein, lons, lats


def get_variable_lonlat_from_domain(
    variable: np.ndarray,
    lons_in: np.ndarray,
    lats_in: np.ndarray,
    lon_west: int,
    lon_east: int,
    lat_north: int,
    lat_south: int,
) -> tuple:
    """
    Crop variable to the domain, using latitudes and longitudes.
    Return: Cropped variable, longitudes and latitudes
    """
    logger = logging.getLogger("io_utilities.get_variable_lonlat_from_domain")
    if lon_east < lon_west:
        logger.info("Domain is 'over' the map. Stitching one side to the other")
        # going over longitude 0° when the longitudes go from 0 to 360°
        # Atlantic ocean, we need to cycle the data due to the domain crossing 0°.
        lons_inwrap180 = wrapTo180(lons_in)
        lons180 = np.concatenate(
            (lons_inwrap180[len(lons_inwrap180) // 2 :], lons_inwrap180[: len(lons_inwrap180) // 2])
        )
        variable = np.dstack((variable[:, :, len(lons_in) // 2 :], variable[:, :, : len(lons_in) // 2]))
        indice_west = [idx for idx, el in enumerate(lons180) if el == wrapTo180(lon_west)][0]
        indice_east = [idx for idx, el in enumerate(lons180) if el == wrapTo180(lon_east)][0]
        lons = lons180[indice_west:indice_east]
        variable_lon = variable[
            :, :, np.where(lons180 == wrapTo180(lon_west))[0][0] : np.where(lons180 == wrapTo180(lon_east))[0][0]
        ]
    else:
        lon_ids = [id for id, el in enumerate(lons_in) if el <= lon_east if el >= lon_west]
        lons = lons_in[lon_ids]
        variable_lon = variable[:, :, lon_ids]
    lat_ids = [id for id, el in enumerate(lats_in) if el <= lat_north if el >= lat_south]
    lats = lats_in[lat_ids]
    #
    variable = variable_lon[:, lat_ids, :]
    logger.info("Subsetting dataset on domain done")
    return variable, lons, lats


def get_ids_start_end4timecrop(itime, config, inputtime: np.ndarray) -> tuple:
    """Select indexes to make daily average"""
    logger = logging.getLogger("io_utilities.get_ids_start_end4timecrop")
    dt_data = config["datatimeresolution"]
    period_detection = config["period_detection"]
    interval = period_detection / dt_data
    #
    lst_idstart = [id for id, el in enumerate(inputtime) if el == itime]
    id_start = lst_idstart[0]
    lst_idend = [id for id, el in enumerate(inputtime) if el == itime + dt.timedelta(hours=dt_data * interval)]
    # If we reach the end of the dataset, there will be no index for the next time,
    # eg. work on the year 1999, 01-01-2000 does not exist here, but we need its id for python average
    if not lst_idend:
        id_end = len(inputtime)
    else:
        id_end = [id for id, el in enumerate(inputtime) if el == itime + dt.timedelta(hours=dt_data * interval)][0]
    return id_start, id_end


def make_daily_average(variable2process: np.ndarray, inputtime: np.ndarray, listofdates, config: dict) -> np.ndarray:
    """
    Calculate the daily average of the input variable
    Uses the config file for the time step of the data
    """
    logger = logging.getLogger("io_utilities.make_daily_average")
    logger.info("Computation of daily average")
    daily_variable = []
    for itime in listofdates:
        # Select indexes to make daily average
        id_start, id_end = get_ids_start_end4timecrop(itime, config, inputtime=inputtime)
        # Daily mean of the input variable (OLR). Works as smoothing
        variable4cb = np.nanmean(variable2process[id_start:id_end, ...], 0)
        daily_variable.append(variable4cb)
    logger.info("Computation of daily average done")
    return np.stack(daily_variable)


def load_npydata(filename: str = None, config: dict = None, varname: str = None) -> np.ndarray:
    dirfiles = config["saved_dirpath"]
    filist_of_var = [fi for fi in os.listdir(dirfiles) if varname in fi]
    if len(filist_of_var):
        if filename:
            var2load = np.load(f"{dirfiles}/{filename}.npy")
        elif config and not filename:
            var2load = np.load(f"{dirfiles}/{varname}{config['startdate']}-{config['enddate']}-{config['domain']}.npy")
    return var2load


def load_pickledata(filename: str = None, config: dict = None, varname: str = None) -> np.ndarray:
    dirfiles = config["saved_dirpath"]
    filist_of_var = [fi for fi in os.listdir(dirfiles) if varname in fi]
    if len(filist_of_var):
        if filename:
            fd = open(f"{dirfiles}/{filename}.pickle", "rb")
        elif config and not filename:
            fd = open(f"{dirfiles}/{varname}{config['startdate']}-{config['enddate']}-{config['domain']}.pickle", "rb")
        var2load = pickle.load(fd, fix_imports=True)
        fd.close()
    return var2load


def load_multiyears_data(config, varname: str):
    """
    Load 1-year files and put the data into a list
    config: config file from detection workflow or analysis
    varname: list_of_cloud_bands, daily_variable, listofdates
    """
    logger = logging.getLogger("io_utilities.load_multiyears_data")
    if varname == "list_of_cloud_bands":
        method = "pickle"
    elif varname == "daily_variable":
        method = "npy"
    elif varname == "listofdates":
        method = "datesnpy"
    else:
        logger.warning("Wrong varnanme")
    #
    datalist = []
    if config["flag_use_saveddailyvar"]:
        if method == "pickle":
            for iyear in range(int(config["startdate"][:4]), int(config["enddate"][:4]) + 1):
                filename = f"{varname}{iyear}0101.00-{iyear}1231.00-{config['domain']}"
                if config["flag_djfm"]:
                    filename += "_djfm"
                datalist.extend(load_pickledata(filename=filename, config=config, varname=varname))
        elif method == "datesnpy":
            for iyear in range(int(config["startdate"][:4]), int(config["enddate"][:4]) + 1):
                filename = f"{varname}{iyear}0101.00-{iyear}1231.00-{config['domain']}"
                if config["flag_djfm"]:
                    filename += "_djfm"
                oneyearottime = load_npydata(filename=filename, config=config, varname=varname)
                datalist.extend([pandas.to_datetime(item) for item in oneyearottime])
        elif method == "npy":
            # final list has a length of the number of years
            # each element of the list has a shape of [ndays, lons, lats]
            for iyear in range(int(config["startdate"][:4]), int(config["enddate"][:4]) + 1):
                filename = f"{varname}{iyear}0101.00-{iyear}1231.00-{config['domain']}"
                if config["flag_djfm"]:
                    filename += "_djfm"
                datalist.append(load_npydata(filename=filename, config=config, varname=varname))
        return datalist
    else:
        logger.warning("Check your config file and if you have saved any data")


def npy_save_dates(config, listofdates):
    logger = logging.getLogger("io_utilities.save_dates_npy")
    outpath = config["saved_dirpath"]
    os.makedirs(outpath, exist_ok=True)
    new_listofdates = np.array([el.to_pydatetime() for el in listofdates], dtype=np.datetime64)
    np.save(f"{outpath}/listofdates{config['startdate']}-{config['enddate']}-{config['domain']}.npy", new_listofdates)
    logger.info("List of dates saved")
    return


def npy_save_dailyvar(config, daily_variable):
    logger = logging.getLogger("io_utilities.save_dailyvar_npy")
    outpath = config["saved_dirpath"]
    os.makedirs(outpath, exist_ok=True)
    if config["select_djfm"]:
        filename = f"daily_variable{config['startdate']}-{config['enddate']}-{config['domain']}_djfm.npy"
    else:
        filename = f"daily_variable{config['startdate']}-{config['enddate']}-{config['domain']}.npy"
    np.save(f"{outpath}/{filename}", daily_variable)
    logger.info("Daily variable saved")
    return


def pickle_save_cloudbands(config, list_of_cloud_bands):
    logger = logging.getLogger("io_utilities.pickle_save_cloudbands")
    outpath = config["saved_dirpath"]
    os.makedirs(outpath, exist_ok=True)
    if config["select_djfm"]:
        f = open(
            f"{outpath}/list_of_cloud_bands{config['startdate']}-{config['enddate']}-{config['domain']}_djfm.pickle",
            "wb",
        )
    else:
        f = open(
            f"{outpath}/list_of_cloud_bands{config['startdate']}-{config['enddate']}-{config['domain']}.pickle", "wb"
        )
    pickle.dump(obj=list_of_cloud_bands, file=f, fix_imports=True)
    f.close()
    logger.info("Cloud bands saved")
    return
