#!/bin/bash
# FIXME remove this
# code directory
srcdir=/users/rpilon/codes/unil/
# choose and modify you config file accoding to your need and setup
configfilename=config_cbworkflow_southPacific.yml
# config file directory
configpath="${srcdir}"/CloudBandDetection/config/"${configfilename}"

# run the detection
python "${srcdir}"/CloudBandDetection/src/run.py "${configpath}"
