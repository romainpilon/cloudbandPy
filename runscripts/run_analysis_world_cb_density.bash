#!/bin/bash

# Runscript to create a world climatology of cloud band density

# code directory
srcdir=/users/rpilon/codes/unil/
# choose and modify you config file accoding to your need and setup
configfilename=config_analysis_world_cb_density.yml
# config file directory
configpath="${srcdir}"/CloudBandDetection/config/"${configfilename}"

# run the detection
python "${srcdir}"/CloudBandDetection/analysis/plot_cb_density.py "${configpath}"
