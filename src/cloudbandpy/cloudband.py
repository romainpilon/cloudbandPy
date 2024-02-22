#!/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import pickle


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
        angle: np.float32,
        lat_centroid: np.float32,
        lon_centroid: np.float32,
        date_number: np.int32,
        iscloudband: bool = True,
        connected_longitudes: bool = False,
        parents: set[str] = set(),
        connected2pv: bool = False,
        connected2eqwave: bool = False,
    ):
        self.cloud_band_array = cloud_band_array
        self.date_number = date_number
        
        self.angle = angle
        self.lat_centroid = lat_centroid
        self.lon_centroid = lon_centroid
        self.area = area
        # Label/id of the cloud band
        self.parents = parents
        self.connected2pv = connected2pv
        self.connected2eqwave = connected2eqwave
        # id = "num date _ longitude (location)"
        self.id_ = f"{self.date_number}_{self.lon_centroid}"
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
                data["angle"],
                data["lat_centroid"],
                data["lon_centroid"],
                data["date_number"],
                data["iscloudband"],
                data["connected_longitudes"],
                data["parents"],
                data["connected2pv"],
                data["connected2eqwave"],
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
            d["angle"],
            d["lat_centroid"],
            d["lon_centroid"],
            d["date_number"],
            d["connected_longitudes"],
            d["iscloudband"],
            d["parents"],
            d["connected2pv"],
            d["connected2eqwave"],
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
                    "angle": self.angle,
                    "lat_centroid": self.lat_centroid,
                    "lon_centroid": self.lon_centroid,
                    "date_number": self.date_number,
                    "connected_longitudes": self.connected_longitudes,
                    "iscloudband": self.iscloudband,
                    "parents": self.parents,
                    "connected2pv": self.connected2pv,
                    "connected2eqwave": self.connected2eqwave,
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
            "angle": self.angle,
            "lat_centroid": self.lat_centroid,
            "lon_centroid": self.lon_centroid,
            "date_number": self.date_number,
            "connected_longitudes": self.connected_longitudes,
            "iscloudband": self.iscloudband,
            "parents": self.parents,
            "connected2pv": self.connected2pv,
            "connected2eqwave": self.connected2eqwave,
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
