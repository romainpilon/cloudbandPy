#!/bin/bash
# FIXME remove this
# code directory
srcdir=/users/rpilon/codes/unil/
# choose and modify you config file accoding to your need and setup
configfilename=config_cbworkflow_southPacific.yml
# config file directory
configpath="${srcdir}"/cloudbandPy/config/"${configfilename}"

# run the detection
python "${srcdir}"/cloudbandPy/src/run.py "${configpath}"
