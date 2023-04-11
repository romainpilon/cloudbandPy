import datetime as dt
import logging
import pandas
import netCDF4 as nc
from typing import Any
import sys


def convert_date2num(time_in) -> Any:
    return nc.date2num(time_in, "hours since 1900-01-01 00:00:00.0", calendar="gregorian")


def convert_num2date(time_in) -> Any:
    return nc.num2date(
        time_in, "hours since 1900-01-01 00:00:00.0", calendar="gregorian", only_use_cftime_datetimes=False
    )


def create_list_of_dates(config: dict) -> pandas.date_range:
    """
    Returns:
    - a list of days ranging from the start date to the end date
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
    return pandas.date_range(start=config["datetime_startdate"], end=config["datetime_enddate"], freq=freq)





def add_startend_datetime2config(config: dict) -> tuple:
    """
    Transforms start/end times from the config file in 'yyyymmdd.hh' format to datetime format
    Update config file
    """
    startdate = config["startdate"]
    enddate = config["enddate"]
    timeformat_in_datetime = "%Y%m%d.%H"
    datetime_startdate = dt.datetime.strptime(startdate, timeformat_in_datetime)
    datetime_enddate = dt.datetime.strptime(enddate, timeformat_in_datetime)
    config.update(
            {
                "datetime_startdate": datetime_startdate,
                "datetime_enddate": datetime_enddate,
            }
        )
    return
