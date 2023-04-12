#!/usr/bin/env python
# coding: utf-8
"""
Functions to manipulate longitudes, compute resolution and convert OLR values in W.m2
"""

import metpy.calc as mpcalc
import numpy as np
from typing import Any


def compute_resolution(lons: np.ndarray, lats: np.ndarray) -> np.ndarray:
    """From latitudes and longitudes, compute the resolution in meter"""
    dx, dy = mpcalc.lat_lon_grid_deltas(lons, lats)
    # resolution in km
    res_dx = dx[:, 0].magnitude / 1000.0  # length of lons/dx according to latitudes
    res_dy = dy.magnitude.mean() / 1000.0 * -1  # length of lat/dy constant on regular grid
    resolution = res_dx * res_dy  # in square km, shape of res_dx or lats
    return resolution


def wrapTo360(xin) -> Any:
    """
    wrap longitudes between 0 to 360
    xout = wrapTo360(xin)
    xin: input np.array with longitudes
    xout: output np.array with longitudes
    """
    xout = np.copy(xin)
    if np.size(xout) > 1:
        xout[xin < 0.0] = 360.0 + xin[xin < 0.0]
    else:
        if xin < 0.0:
            xout = 360.0 + xin
    return xout


def wrapTo180(xin) -> Any:
    """
    wrap longitudes between -180 to 180
    xout = wrapTo180(xin)
    xin: input np.array with longitudes
    xout: output np.array with longitudes
    """
    xout = np.copy(xin)
    if np.size(xout) > 1:
        xout[xin > 180.0] = xin[xin > 180.0] - 360.0
    else:
        if xin > 180.0:
            xout = xin - 360.0
    return xout


def convert_olr_in_wm2(olrin):
    # Convert top thermal radiation in J m**-2 into W.m**-2
    return np.divide(-1 * olrin, 3600)
