#!/usr/bin/env python
# coding: utf-8
"""
Functions to detect cloud bands from outgoing longwave radiations
"""

import logging
import numpy as np
from scipy import ndimage as ndi
from skimage import measure, morphology
from skimage.filters import threshold_otsu, threshold_yen

from .cloudband import CloudBand
from .time_utilities import convert_date2num
from .misc import wrapTo360


def blob_detection(
    input_variable: np.ndarray, parameters: dict, resolution: np.ndarray, connectlongitudes: bool = False
):
    """
    This function uses morphological labelling, ie blob detection, to detect cloud bands
    Input:
        - input_variable: variable which will be processed and from which blobs of clouds will be detected
        - thresh_value: threshold value we will use to detect cloud bands
        - cloud_band_area_threshold: en m2
    Output:
        - detected_blobs: a map of blobs
    Side note: One could use the Yen (or Ostu) global thresholding method, change in parameters. For testing purpose, note for research.
    """
    logger = logging.getLogger("cb_detection.blob_detection")
    cloud_band_area_threshold = float(parameters["CLOUD_BAND_AREA_THRESHOLD"])
    # Threshold value
    # We add the possibility to use histogram based methods. By default, it will use the specific threshold.      
    if str(parameters["thresholding_method"]).lower() == "yen":
        thresh_value = threshold_yen(input_variable)
        logger.warning(f"Use Yen thresholding method. Threshold:{thresh_value}")
    elif str(parameters["thresholding_method"]).lower() == "otsu":
        thresh_value = threshold_otsu(input_variable)
        logger.warning(f"Use Otsu thresholding method. Threshold:{thresh_value}")
    else:
        thresh_value = parameters["OLR_THRESHOLD"]
    # Sanitize input. make sure all values < 0 are all set to 0
    if not np.all((input_variable >= 0)):
        logger.warning("Some Missing Values in the Input")
        input_variable[input_variable < 0] = 0
    # Binarize the data and fill holes
    fill_binarize_data = ndi.binary_fill_holes(input_variable < thresh_value)
    # We apply a morphological dilation: adds pixels to the boundaries of each objects
    dilation = morphology.dilation(fill_binarize_data)
    # -- Connected Components Labelling
    labelled_blobs = measure.label(dilation, connectivity=2, background=0)
    """
    labelled_blobs =
    array([[ 1,  1,  1, ...,  0,  0,  0],
        [ 1,  1,  1, ...,  0,  0,  0],
        [ 1,  1,  1, ...,  0,  0,  0],
        ...,
        [ 0,  0,  0, ...,  0,  0,  0],
        [ 0,  0,  0, ...,  0, 26, 26],
        [ 0,  0,  0, ..., 26, 26, 26]], dtype=int32)
    """
    # -- If hemispheric detection (0-360°), first and last longitudes must be connected
    # Consolidate blob's labels
    if connectlongitudes:
        consolidated_labels = connectLongitudes(labelled_blobs)
        # copy to avoid side effects
        labelled_blobs = np.copy(consolidated_labels)
    # Compute cluster areas and sort them from largest to smallest for further speed up the process
    # background (cluster)'s label = 0
    # --> blobs_size, sorted_blobs and cloudband_candidate are like [[cluster ID, cluster area], ...]
    blobs_size = [
        [i, compute_blob_area(labelled_blobs, i, resolution=resolution)] for i in range(1, labelled_blobs.max() + 1)
    ]
    sorted_blobs = sorted(blobs_size, key=lambda c: c[1], reverse=True)
    # --  Filtering
    # 1) We filter blobs according to their area (subjective threshold).
    #    We filter out the largest cloud bands from the 'sorted_blobs' list according to 'cloud_band_area_threshold'
    cloudband_candidate = [
        el for idx, el in enumerate(sorted_blobs) if sorted_blobs[idx][1] >= cloud_band_area_threshold
    ]
    # 2) We make an array/map of these cloud band candidates
    labelled_candidates = np.zeros_like(labelled_blobs, dtype=np.uint8)
    for idx in [idcb[0] for idcb in cloudband_candidate]:
        labelled_candidates[labelled_blobs == idx] = idx
    #
    return fill_binarize_data, dilation, labelled_blobs, labelled_candidates


def candidates2class(labelled_candidates, date, resolution, lons, lats):
    """
    Transform cloud band candidates into a CloudBand class
    """
    logger = logging.getLogger("cb_detection.candidates2class")
    list_candidates = []
    for ilabel in set(labelled_candidates[np.where(labelled_candidates != 0)]):
        icloudband = np.zeros_like(labelled_candidates, dtype=np.uint8)
        icloudband[np.where(labelled_candidates == ilabel)] = 1
        cb_area = compute_blob_area(icloudband, 1, resolution)
        cb_num_date = convert_date2num(date)
        cb_lon, cb_lat = get_cloudband_latlon(icloudband, lons, lats)
        # If the cloud band crosses the edges of the (worldwide) domain,
        # the longitudes on the longitudinal edges are connected, we flag the candidate as such
        connected_longitudes = False
        if wrapTo360(np.nanmin(cb_lon)) == 0.0 and wrapTo360(np.nanmax(cb_lon)) > 250.0:
            connected_longitudes = True
        # Geometric properties are computed here and then incorporated into the class
        regions_props = measure.regionprops(icloudband)[0] # return a list, here we've got only one cloud band --> [0]
        # angle between the minor axis and the horizontal, at the centroid
        angle = (regions_props.orientation * 360) / (2 * np.pi)
        # center of ellipse around cloud band
        centroid = regions_props.centroid
        lon_centroid, lat_centroid = (
            lons[int(centroid[1])].item(),
            lats[int(centroid[0])].item(),
        )
        # Setting up cloud band object
        cloud = CloudBand(
            cloud_band_array=icloudband,
            date_number=cb_num_date,
            area=cb_area,
            lats=cb_lat,
            lons=cb_lon,
            angle=angle,
            lon_centroid=lon_centroid,
            lat_centroid=lat_centroid,
            iscloudband=False,
            connected_longitudes=connected_longitudes,
        )
        list_candidates.append(cloud)
    return list_candidates


def filter_blobs2cloudbands(list_candidates: list, parameters: dict) -> np.ndarray:
    """
    For one time, select the cloud bands from candidates.
    Cloud bands are filter out from candidates using different criterion:
    -> angle and extend above the tropical line
    Args: list of cloud bands candidates for one time/date
    Return: list of cloud band object and map of all cloud bands at one time/date (one label per cloud band)
    """
    logger = logging.getLogger("cb_detection.filter_blobs2cloudbands")
    top_lat_criteria = parameters["TOP_LATITUDE"]
    bottom_lat_criteria = parameters["BOTTOM_LATITUDE"]
    angle_min = parameters["ANGLE_MIN"]
    angle_max = parameters["ANGLE_MAX"]
    #
    list_of_cloud_bands = []
    for iblob in list_candidates:
        blob_center_lat = iblob.lat_centroid
        blob_max_lat = np.nanmax(iblob.lats)
        blob_min_lat = np.nanmin(iblob.lats)
        # we want to compare the long axis of the blob's ellipse
        if blob_center_lat < 0.0:
            # southern hemisphere
            angle2longaxis = -90.0
        else:  # northern hemisphere
            angle2longaxis = +90.0
        #
        if not iblob.connected_longitudes:
            condition4cloudband = (
                (angle_min < iblob.angle + angle2longaxis < angle_max)
                and (blob_min_lat <= bottom_lat_criteria)
                and (blob_max_lat >= top_lat_criteria)
            )
        else:
            # We assume that if the cloud band candidate is crosing the edge of the domain (map), it has an acceptable angle
            condition4cloudband = (blob_min_lat <= bottom_lat_criteria) and (blob_max_lat >= top_lat_criteria)
        # If all conditions are right, the candidate is a cloud band
        if condition4cloudband:
            iblob.iscloudband = True
            list_of_cloud_bands.append(iblob)
    #
    return list_of_cloud_bands


def detection_workflow(
    var2process: np.ndarray,
    parameters: dict,
    latitudes: np.ndarray,
    longitudes: np.ndarray,
    resolution: np.ndarray,
    listofdates,
    config: dict,
):
    """
    Runs the detection of cloud bands by firstly processing the input variable with morphological and labelling operations,
    and secondly separate cloud bands from all labelled blobs
    Args:
        - var2process: variable that will be used for detection.
            The detection algorithm will iterate over the time dimension of the array
        - parameters: criteria used for filtering out cloud bands from the input variable
        - latitudes: array of latitudes from the input file
        - resolution: array of the data resolution (length of the longitudes)
        - config: configurations needed to check whether it's needed to connect longitudes
            (hemispheric detection) in order to connect cloud bands that extend from 359° to 0°.
    Returns
        - fill_binarize_data: binarized data
        - dilation: after thresholding the data, they are dilated to expand from the threshold value
        - labelled_blobs: all the blobs that have been labelled after dilation
        - labelled_candidates: candidate blobs that can be cloud bands
        - cloud_bands_map: actual cloud bands after applying the criteria
    """
    logger = logging.getLogger("cb_detection.detection_workflow")
    logger.info("Cloud band detection in progress")
    fill_binarize_data = np.zeros_like(var2process, dtype=np.uint8)
    dilation = np.zeros_like(var2process, dtype=np.uint8)
    labelled_blobs = np.zeros_like(var2process, dtype=np.uint8)
    labelled_candidates = np.zeros_like(var2process, dtype=np.uint8)
    cloud_bands_map = np.zeros_like(var2process, dtype=np.uint8)
    list_of_candidates = []
    list_of_cloud_bands = []
    connectlongitudes = False
    # If hemispheric detection (0-360°), first and last longitudes must be connected
    if abs(config["lon_east"] - config["lon_west"]) == 360:
        connectlongitudes = True
        logger.info("Blobs that are longitudinally crossing the map will be connected")
    #
    # Iteration over the time dimension. One blob-detection per timestep.
    for idx, itime in enumerate(listofdates):
        (
            fill_binarize_data[idx],
            dilation[idx],
            labelled_blobs[idx],
            labelled_candidates[idx],
        ) = blob_detection(var2process[idx], parameters, resolution, connectlongitudes)
        # Objectify the cloud band candidates
        list_of_candidates.append(
            candidates2class(
                labelled_candidates[idx], date=itime, resolution=resolution, lons=longitudes, lats=latitudes
            )
        )
        # Filtering out the cloud bands according the angle and "crossing the tropical line" criterion
        # -> return for each time, an array with all cloud bands (per snapshot)
        list_of_cloud_bands.append(
            filter_blobs2cloudbands(
                list_of_candidates[idx],
                parameters=parameters,
            )
        )
        # Array of all the cloud bands for one time
        for icb, iblob in enumerate(list_of_cloud_bands[idx]):
            if iblob:
                # cloud_band_array = 1 -> set and increment the label of each cloud band
                cloud_bands_map[idx] += iblob.cloud_band_array * (icb + 1)
    #
    logger.info("Cloud band detection done")
    return fill_binarize_data, dilation, labelled_blobs, labelled_candidates, cloud_bands_map, list_of_candidates, list_of_cloud_bands


def compute_blob_area(img: np.ndarray, idx: int, resolution: np.ndarray) -> float:
    """
    Compute the area of a given blob (based on the index of that blob) in an image
    """
    # transform the blob into a True/False array. True is set for values of the blob
    bool_img = img == idx
    # make a blob/array of values of the resolution array. 0 outside the blob, resolution array for the blob
    blob_mask_resolution = np.multiply(bool_img.T, resolution).T
    blob_area = np.sum(blob_mask_resolution)
    return blob_area


def get_cloudband_latlon(cloudband: np.ndarray, lons: np.ndarray, lats: np.ndarray):
    """
    Make maps of the cloud band's longitudes and latitudes
    Note: not used
    """
    xlon, xlat = np.meshgrid(lons, lats)
    mask = np.ones_like(cloudband, dtype=np.float16)
    mask[cloudband != 0] = 1
    mask[cloudband == 0] = np.nan
    cloud_lonmap = xlon * mask
    cloud_latmap = xlat * mask
    return cloud_lonmap, cloud_latmap


def reNumberLabels(labels):
    """
    Make sure all label values in a label image are sequential with no gaps
    """
    res = np.array(labels)  # copy to avoid side effects
    labelMap = []
    nextlabel = 1
    for i in range(1, np.max(res) + 1):
        if np.sum(res == i):  # if label i is used
            labelMap.append((i, nextlabel))
            nextlabel += 1
    for old, new in labelMap:
        res[res == old] = new
    return res


def connectLongitudes(labels, nolabel=0):
    """
    Merge labels that connects through the boundaries of the image, vertically and horizontally
    """
    # make a copy to work on, to avoid side effects on the original label array
    res = np.array(labels)
    # connect horizontally
    for i in range(0, res.shape[0]):
        # if the first pixel of the line is not null and the last one is also not null but different, we merge them
        # we use the minimum label of both to make sure we don't miss concave regions
        if res[i, 0] != nolabel and res[i, -1] != nolabel and res[i, -1] != res[i, 0]:
            lMin, lMax = min(res[i, 0], res[i, -1]), max(res[i, 0], res[i, -1])
            res[res == lMax] = lMin
    return reNumberLabels(res)
