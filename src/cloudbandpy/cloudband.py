#!/usr/bin/env python
# coding: utf-8
"""
Brief discussion
"""

import datetime as dt
import numpy as np
from skimage import measure


class CloudBand:
    """Class defining a cloud band
    It sets the label of the cloud band according to the date and computes its orientation.
    Input: an array containing one cloud band, a map of its longitudes and latitudes, the date"""

    def __init__(
        self,
        cloud_band_array: np.ndarray,
        date_number: dt.datetime,
        area: float,
        lats: np.ndarray,
        lons: np.ndarray,
        connected_longitudes: bool = False,
        iscloudband: bool = True,
        parents: set[str] = set(),
    ):
        self.cloud_band_array = cloud_band_array
        self.date = date_number
        self.area = area
        # return a list, here we've got only one cloud band --> [0]
        regions_props = measure.regionprops(self.cloud_band_array)[0]
        # center of ellipse around cloud band
        self.latloncenter = regions_props.centroid
        # angle between the minor axis and the horizontal, at the centroid
        self.angle = (regions_props.orientation * 360) / (2 * np.pi)
        # Label/id of the cloud band
        self.parents = parents
        # id = "num date _ longitude (location)"
        self.id_ = f"{date_number}_{round(self.latloncenter[1])}"
        #
        self.lats = lats
        self.lons = lons
        self.iscloudband = iscloudband
        # If the cloud band crosses the edges of the (worldwide) domain,
        # the longitudes on the longitudinal edges are connected
        self.connected_longitudes = connected_longitudes
