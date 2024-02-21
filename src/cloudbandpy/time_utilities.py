import datetime as dt
import logging
import pandas as pd
import netCDF4 as nc
import numpy as np
from typing import Any
import sys


def convert_date2num(time_in) -> Any:
    return nc.date2num(time_in, "hours since 1900-01-01 00:00:00.0", calendar="gregorian").astype(np.int32)


def convert_num2date(time_in) -> Any:
    return nc.num2date(
        time_in, "hours since 1900-01-01 00:00:00.0", calendar="gregorian", only_use_cftime_datetimes=False
    )


def create_list_of_dates(config: dict) -> pd.date_range:
    """
    Create a list of days ranging from the start date to the end date
    Handles "day is out of range for month" problem
    """
    logger = logging.getLogger("time_utilities.create_list_of_dates")
    # tranform dates from config file in datetime format and create a pandas date range
    if config["period_detection"] == 24:
        freq = "1D"
    elif config["period_detection"] == 12:
        freq = "12H"
    elif config["period_detection"] == 6:
        freq = "6H"
    elif config["period_detection"] == 3:
        freq = "3H"
    elif config["period_detection"] == 1:
        freq = "1H"
    else:
        logger.error("Detection period must be 24h, 12h, 6h, 3h or 1h!")
        sys.exit(1)
    
    datetime_range = pd.date_range(
        start=config["datetime_startdate"], end=config["datetime_enddate"], freq=freq
    ) 
    try:
        return datetime_range
    except ValueError:
        logger.warning("ValueError: day is out of range for month")
        config["datetime_enddate"] = dt.datetime.strptime(config["datetime_enddate"], "%Y-%m-%d %H:%M:%S") - dt.timedelta(days=1)
        return create_list_of_dates(config)


def create_array_of_times(config: dict) -> np.ndarray:
    """
    Transform a list of pandas datetime to an array of python datetime
    """
    datetime_range = create_list_of_dates(config)
    datetime_array = np.array(datetime_range.to_pydatetime())
    return datetime_array


def add_startend_datetime2config(config: dict) -> tuple:
    """
    Transforms start/end times from the config file in 'yyyymmdd.hh' format to datetime format
    Update config file
    Handles "day is out of range for month" problem
    """
    logger = logging.getLogger("time_utilities.add_startend_datetime2config")
    timeformat_in_datetime = "%Y%m%d.%H"
    try:
        config.update(
            {
                "datetime_startdate": dt.datetime.strptime(config["startdate"], timeformat_in_datetime),
                "datetime_enddate": dt.datetime.strptime(config["enddate"], timeformat_in_datetime),
            }
        )
    except ValueError as e:
        if "day is out of range for month" in str(e):
            logger.error("Error: Invalid date range. February has only 28 or 29 days.")
        else:
            logger.error(f"Error: {e}")
        sys.exit(1)
