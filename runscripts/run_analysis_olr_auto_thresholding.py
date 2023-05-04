#!/usr/bin/env python
# coding: utf-8

"""
Runscript to show OLR distribution and thresholding 

This script creates:
- an histogram of OLR values with 2 optimal values according to global optimal thresholding
- a world map of OLR
This can help to understand the chosen parameters.

It uses data that have been previoulsy saved using the main script. It does not use netcdf files.

Run: python cloudbandpy/runscripts/run_analysis_olr_auto_thresholding.py cloudbandpy/config/config_analysis.yml

"""


import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
import numpy as np
from skimage.filters import threshold_otsu, threshold_yen
from skimage import exposure
import os

from cloudbandpy.figure_tools import set_fontsize
from cloudbandpy.io_utilities import load_ymlfile, load_data_from_saved_var_files
from cloudbandpy.misc import parse_arguments

def plot_histogram(variable4analyis):
    # Histogram of OLR with optimal global threshold
    # Make one value per year
    valyen = [threshold_yen(var) for var in variable4analyis]
    valotsu = [threshold_otsu(var) for var in variable4analyis]
    hist, bins_center = exposure.histogram(np.concatenate(variable4analyis).ravel())
    #
    set_fontsize(size=13)
    fig, ax = plt.subplots()
    ax.axvline(np.median(valyen), color="k", ls="solid")
    ax.axvspan(np.min(valyen), np.max(valyen), alpha=0.5, facecolor="#ababab")
    ax.axvline(np.median(valotsu), color="#ff5c7f", ls="dashed")
    ax.axvspan(np.min(valotsu), np.max(valotsu), alpha=0.5, facecolor="#ff5c7f")
    ax.plot(bins_center, hist, lw=2)
    ax.set_xlabel(r"OLR (W.m$^{-2}$)")
    ax.set_ylabel(r"PDF")
    ax.text(np.median(valyen) + 2, hist.max() / 1.5, "Yen " + "{:3.1f}".format(np.median(valyen)))
    ax.text(np.median(valotsu) + 2, hist.max() / 3, "Otsu " "{:3.1f}".format(np.median(valotsu)))
    ax.xaxis.set_major_locator(MultipleLocator(30))
    ax.xaxis.set_major_formatter("{x:.0f}")
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.set_xlim([75, 350])
    plt.tight_layout()
    return fig


if __name__ == "__main__":
    # Load analysis config file: use default config/config_analysis.yml
    args = parse_arguments()
    config_file = args.config_file
    config = load_ymlfile(config_file, isconfigfile=True)
    # Load daily OLR previously saved
    daily_variable = load_data_from_saved_var_files(config, varname="daily_variable")
    # Plot histogram of the input variable (eg, OLR) with optimalglobal threshold
    print("Create distribution of OLR values with global optimal threshold values")
    os.makedirs(config["dir_figures"], exist_ok=True)
    savedfigurename = f"{config['dir_figures']}/distribution_valYen_Otsu_autoThreshold_{config['datetime_startdate'].year}_{config['datetime_enddate'].year}_{config['domain']}"
    if config["select_djfm"]:
        savedfigurename += "_djfm"
    fig = plot_histogram(daily_variable)
    fig.show()
    fig.savefig(savedfigurename + ".png", dpi=200, bbox_inches="tight")
