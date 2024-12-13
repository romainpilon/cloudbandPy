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
import pickle
import yaml

from .cloudband import CloudBand
from .misc import is_decreasing, convert_olr_in_wm2, wrapTo180
from .time_utilities import add_startend_datetime2config, convert_date2num, create_list_of_dates, create_array_of_times


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
    # if the .yml file is a configuration file, we add start/end dates in datetime format
    # and update the config file
    if isconfigfile:
        add_startend_datetime2config(config)
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
    logger = logging.getLogger("io_utilities.load_dataset")
    filedirectory = config["clouddata_path"]
    varname = config["varname"]
    timecoord_name = config["timecoord_name"]
    xcoord_name = config["xcoord_name"]
    ycoord_name = config["ycoord_name"]
    olr_convert2wm2 = config["olr_convert2wm2"]
    if os.path.isdir(filedirectory) and os.path.isfile(filedirectory + "/" + filename):
        ds = nc.Dataset(filedirectory + "/" + filename, "r")
        variable = ds.variables[varname][...]
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
        # Make that latitudes are decreasing (90° -> 0 -> -90°) and reshape variable accordingly
        if not is_decreasing(lats):
            logger.warning("latitudes are increasing. Must be decreasing. Reshapping latitudes and variable.")
            lats = lats[::-1]
            variable = variable[:, ::-1, :]
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
    logger.info(f"Loading dataset from {config['clouddata_path']}")
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
    # Create daily mean of the input variable?
    if config["qd_var"]:
        variable4cb = make_daily_average(variable4cb, timein, config)
        # Save daily variable (and latitudes and longitudes)
        if config["save_dailyvar"]:
            logger.info("Saving daily variable")
            npy_save_dailyvar(config, variable4cb)
            # Save longitudes and latitudes for further use with the saved daily variable
            np.save(f"{config['saved_dirpath']}/lons_{config['domain']}.npy", np.asarray(lons))
            np.save(f"{config['saved_dirpath']}/lats_{config['domain']}.npy", np.asarray(lats))
    logger.info("Dataset loaded")
    return variable4cb, lons, lats


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
        variable = np.dstack((variable[..., len(lons_in) // 2 :], variable[..., : len(lons_in) // 2]))
        indice_west = [idx for idx, el in enumerate(lons180) if el == wrapTo180(lon_west)][0]
        indice_east = [idx for idx, el in enumerate(lons180) if el == wrapTo180(lon_east)][0]
        lons = lons180[indice_west:indice_east]
        variable_lon = variable[
            ..., np.where(lons180 == wrapTo180(lon_west))[0][0] : np.where(lons180 == wrapTo180(lon_east))[0][0]
        ]
    else:
        lon_ids, lons = subset_longitudes(lons_in, lon_west, lon_east)
        variable_lon = variable[..., lon_ids]
    lat_ids, lats = subset_latitudes(lats_in, lat_north, lat_south)
    #
    variable = variable_lon[..., lat_ids, :]
    logger.info("Subsetting dataset on domain done")
    return variable, lons, lats


def subset_longitudes(lons_in: np.ndarray, lon_west: float, lon_east: float) -> np.ndarray:
    lon_ids = [id for id, el in enumerate(lons_in) if el <= lon_east if el >= lon_west]
    return lon_ids, lons_in[lon_ids]


def subset_latitudes(lats_in: np.ndarray, lat_north: float, lat_south: float) -> np.ndarray:
    lat_ids = [id for id, el in enumerate(lats_in) if el <= lat_north if el >= lat_south]
    return lat_ids, lats_in[lat_ids]


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


def make_daily_average(variable2process: np.ndarray, inputtime: np.ndarray, config: dict) -> np.ndarray:
    """
    Calculate the daily average of the input variable
    Uses the config file for the time step of the data
    """
    logger = logging.getLogger("io_utilities.make_daily_average")
    logger.info("Computation of daily average")
    daily_tmp_variable = []
    listofdates = create_list_of_dates(config)
    for itime in listofdates:
        # Select indexes to make daily average
        id_start, id_end = get_ids_start_end4timecrop(itime, config, inputtime=inputtime)
        # Daily mean of the input variable (OLR). Works as smoothing
        variable4cb = np.nanmean(variable2process[id_start:id_end, ...], 0)
        daily_tmp_variable.append(variable4cb)
    # Stack list of daily averages
    daily_variable = np.stack(daily_tmp_variable)
    logger.info("Computation of daily average done")
    return daily_variable

def load_npydata(filename: str = None, config: dict = None, varname: str = None) -> np.ndarray:
    if not filename and not config:
        raise ValueError("Either filename or config must be provided.")
    #
    dirpath = config.get("saved_dirpath", ".")
    if filename:
        filepath = os.path.join(dirpath, f"{filename}")
    else:
        startdate = config.get("startdate", "")
        enddate = config.get("enddate", "")
        domain = config.get("domain", "")
        filepath = os.path.join(dirpath, f"{varname}{startdate}-{enddate}-{domain}")
    #
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"{filepath} not found.")
    #
    try:
        var2load = np.load(filepath)
    except Exception as e:
        raise e
    #
    return var2load


def load_data_from_saved_var_files(config: dict, varname: str):
    """
    Load 1-year files and put the data into a list
    config: config file from detection workflow or analysis
    varname: list_of_cloud_bands, daily_variable
    """
    logger = logging.getLogger("io_utilities.load_data_from_saved_var_files")
    if config["load_saved_files"]:
        logger.info(
            f"Load data from: {config['datetime_startdate'].strftime('%Y%m%d.%H')} to {config['datetime_enddate'].strftime('%Y%m%d.%H')}"
        )
        if varname == "list_of_cloud_bands":
            datalist = []
            extension_fout = ".bin"
            for iyear in range(int(config["datetime_startdate"].year), int(config["datetime_enddate"].year) + 1):
                filename = f"{varname}{iyear}{config['datetime_startdate'].strftime('%m%d.%H')}-{iyear}{config['datetime_enddate'].strftime('%m%d.%H')}-{config['domain']}{extension_fout}"
                if config["select_djfm"]:
                    filename = filename.rsplit(".", 1)[0] + "_djfm" + extension_fout
                # Load pickle list of CloudBands
                var4oneyear = load_list(filename=f"{config['saved_dirpath']}/{filename}")
                datalist.extend(var4oneyear)
        elif varname == "daily_variable":
            tmplist = []
            for iyear in range(int(config["datetime_startdate"].year), int(config["datetime_enddate"].year) + 1):
                filename = f"{varname}{iyear}{config['datetime_startdate'].strftime('%m%d.%H')}-{iyear}{config['datetime_enddate'].strftime('%m%d.%H')}-{config['domain']}.npy"
                if config["select_djfm"]:
                    filename = filename.rsplit(".", 1)[0] + "_djfm" + ".npy"
                var4oneyear = load_npydata(filename=filename, config=config, varname=varname)
                tmplist.append(var4oneyear)
            datalist = np.concatenate(tmplist, axis=0)
            # subset the data to chossen selected period
            listofdates = create_list_of_dates(config)
            id_start = np.argwhere(listofdates == config["datetime_startdate"])[0][0]
            id_end = np.argwhere(listofdates == config["datetime_enddate"])[0][0]
            interval = int(24.0 / config["period_detection"])
            datalist = datalist[id_start : id_end + interval, :, :]
        return datalist
    else:
        logger.warning("Check your config file and if you have saved any data")


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


def write_cloud_bands_to_netcdf(
    list_of_cloud_bands: list,
    cloud_band_array: np.ndarray,
    lons: np.ndarray,
    lats: np.ndarray,
    config: dict,
):
    logger = logging.getLogger("io_utilities.write_cloud_bands_to_netcdf")
    # Initialize the netCDF file
    outpath = config["saved_dirpath"]
    os.makedirs(outpath, exist_ok=True)
    filename = f"{outpath}/cloud_bands_{config['datetime_startdate'].strftime('%Y%m%d')}-{config['datetime_enddate'].strftime('%Y%m%d')}-{config['domain']}.nc"
    rootgrp = nc.Dataset(filename, "w", format="NETCDF4")
    # Create dimensions
    time_dim = rootgrp.createDimension("time", None)  # unlimited dimension (can append data)
    object_dim = rootgrp.createDimension("object", None)  # unlimited dimension
    rootgrp.createDimension('longitude', len(lons))
    rootgrp.createDimension('latitude', len(lats))

    dates = create_array_of_times(config)
    date_numbers = nc.date2num(dates, "hours since 1900-01-01 00:00:00.0", calendar="gregorian")

    time_out = rootgrp.createVariable(
        varname="time", dimensions=("time",), datatype="f8"
    )
    time_out.units = "hours since 1900-01-01 00:00:00.0"
    time_out[:] = date_numbers
    
    # Variables
    area = rootgrp.createVariable("area","f4",("time", "object"), fill_value=-9999)
    area.units = 'km2'

    latcenters = rootgrp.createVariable("latcenter","f4",("time", "object"), fill_value=-9999)
    latcenters.description = 'Latitude of centroid around cloud band'

    loncenters = rootgrp.createVariable("loncenter","f4",("time", "object"), fill_value=-9999)
    loncenters.description = 'Latitude of centroid around cloud band'

    angle = rootgrp.createVariable("angle","f4",("time", "object"), fill_value=-9999)
    angle.description = "Angle between long axis of ellipse around cloud band and parallels"
    angle.units = "degrees"

    cbid = rootgrp.createVariable("id", "i8", ("time", "object"), fill_value=-9999)
    cbid.description = "ids of cloud bands. yyyymmddhhMMSS_latitude_of_centroid"

    lat_out = rootgrp.createVariable('latitude', np.float32, ('latitude',))
    lon_out = rootgrp.createVariable('longitude', np.float32, ('longitude',))
    lat_out.units = 'degrees_north'
    lon_out.units = 'degrees_east'
    lat_out[:] = lats[:]
    lon_out[:] = lons[:]
    
    cloud_band_mask = rootgrp.createVariable("cloud_band_mask","f4",("time", "latitude", "longitude"), fill_value=-9999)
    cloud_band_mask.description = "Mask of cloud bands"
    # loop over the list of lists of objects and store the data
    for day_index, cbdays in enumerate(list_of_cloud_bands):
        # Mask
        cloud_band_mask[day_index, :, :] = cloud_band_array[day_index, :, :]
        for object_index, cloud_band in enumerate(cbdays):
            # date_number[day_index, object_index] = cloud_band.date_number
            area[day_index, object_index] = cloud_band.area
            latcenters[day_index, object_index] = cloud_band.lat_centroid
            loncenters[day_index, object_index] = cloud_band.lon_centroid
            angle[day_index, object_index] = cloud_band.angle
            cbid[day_index, object_index] = cloud_band.id_

    rootgrp.close()
    return



def pickle_save_cloudbands(config, list_of_cloud_bands):
    logger = logging.getLogger("io_utilities.pickle_save_cloudbands")
    outpath = config["saved_dirpath"]
    os.makedirs(outpath, exist_ok=True)
    extension_fout = ".bin"
    file_basename = f"list_of_cloud_bands{config['startdate']}-{config['enddate']}-{config['domain']}"
    if config["select_djfm"]:
        file_basename += "_djfm"
    fout = f"{outpath}/{file_basename}{extension_fout}"
    dump_list(list_of_cloud_bands, fout)
    logger.info("Cloud bands saved")
    return



def dump_list(l, filename):
    """
    Dumps a list of lists of instances of `CloudBand` into a pickle file,
    after converting the instances to dictionaries, so that `CloudBand`
    is not pickled

    Input:
        filename: Output file name (str)
    """
    with open(filename, "wb") as f:
        pickle.dump([[c.todict() for c in j] for j in l], f)


def load_list(filename):
    """
    Loads a pickle file constructed with `dump_list` into a list of
    lists of instances of `CloudBand`

    Returns: list with data
    """
    try:
        with open(filename, "rb") as f:
            return [[CloudBand.fromdict(e) for e in j] for j in pickle.load(f)]
    except FileNotFoundError:
        raise FileNotFoundError(f"{filename} not found.")
    except Exception as e:
        raise e
    
