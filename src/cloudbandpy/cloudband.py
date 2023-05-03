#!/bin/env python
# -*- coding: utf-8 -*-

import datetime as dt
import numpy as np
import pickle
from skimage import measure


class CloudBand(object):
    """Class defining a cloud band
    It sets the label of the cloud band according to the date and computes its orientation.
    Input: an array containing one cloud band, a map of its longitudes and latitudes, the date"""

    def __init__(
        self,
        cloud_band_array: np.ndarray,
        area: float,
        lats: np.ndarray,
        lons: np.ndarray,
        date_number: np.int32,
        iscloudband: bool = True,
        connected_longitudes: bool = False,
        parents: set[str] = set(),
    ):
        self.cloud_band_array = cloud_band_array
        self.date_number = date_number
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
        self.id_ = f"{self.date_number}_{round(self.latloncenter[1])}"
        #
        self.lats = lats
        self.lons = lons
        self.iscloudband = iscloudband
        # If the cloud band crosses the edges of the (worldwide) domain,
        # the longitudes on the longitudinal edges are connected
        self.connected_longitudes = connected_longitudes

    @classmethod
    def fromfile(cls, filename):
        """
        Alternative constructor loading the data from a pickle file

        Input:
            filename: File name (str)
        """
        with open(filename, "rb") as f:
            data = pickle.load(f)
            return cls(
                data["cloud_band_array"],
                data["area"],
                data["lats"],
                data["lons"],
                data["date_number"],
                data["iscloudband"],
                data["connected_longitudes"],
                data["parents"],
            )

    @classmethod
    def fromdict(cls, d):
        """
        Alternative construction loading the data from a dictionary

        Input:
            d: dictionary (dict)
        """
        return cls(
            d["cloud_band_array"],
            d["area"],
            d["lats"],
            d["lons"],
            d["date_number"],
            d["connected_longitudes"],
            d["iscloudband"],
            d["parents"],
        )

    def tofile(self, filename):
        """
        Dumps the data to a pickle file

        Input:
            filename: Output file name (str)
        """
        with open(filename, "wb") as f:
            pickle.dump(
                {
                    "cloud_band_array": self.cloud_band_array,
                    "area": self.area,
                    "lats": self.lats,
                    "lons": self.lons,
                    "date_number": self.date_number,
                    "connected_longitudes": self.connected_longitudes,
                    "iscloudband": self.iscloudband,
                    "parents": self.parents,
                },
                f,
            )

    def todict(self):
        """
        Dumps the data to a dictionary structure

        Returns: dictionary
        """
        return {
            "cloud_band_array": self.cloud_band_array,
            "area": self.area,
            "lats": self.lats,
            "lons": self.lons,
            "date_number": self.date_number,
            "connected_longitudes": self.connected_longitudes,
            "iscloudband": self.iscloudband,
            "parents": self.parents,
        }


# def dump_list(l, filename):
#     """
#     Dumps a list of lists of instances of `CloudBand` into a pickle file,
#     after converting the instances to dictionaries, so that `CloudBand`
#     is not pickled

#     Input:
#         filename: Output file name (str)
#     """
#     with open(filename, "wb") as f:
#         pickle.dump([[c.todict() for c in j] for j in l], f)


# def load_list(filename):
#     """
#     Loads a pickle file constructed with `dump_list` into a list of
#     lists of instances of `CloudBand`

#     Returns: list with data
#     """
#     with open(filename, "rb") as f:
#         return [[CloudBand.fromdict(e) for e in j] for j in pickle.load(f)]
