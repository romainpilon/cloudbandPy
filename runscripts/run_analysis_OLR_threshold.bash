#!/bin/bash

# Runscript to show OLR distribution and thresholding 

# code directory
srcdir=/users/rpilon/codes/unil/
# choose and modify you config file accoding to your need and setup
configfilename=config_analysis.yml
# config file directory
configpath="${srcdir}"/CloudBandDetection/config/"${configfilename}"

# run the detection
python "${srcdir}"/CloudBandDetection/analysis/OLR_threshold.py "${configpath}"
