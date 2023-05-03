#!/usr/bin/env python
# coding: utf-8
"""
Script to create histogram showing the percentage of the cloud band number distribution
Run: python cloudbandpy/analysis/plot_distribution_cb_area.py config_analysis.yml
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import sys


from cloudbandpy.figure_tools import set_fontsize
from cloudbandpy.io_utilities import load_ymlfile, load_data_from_saved_var_files
from cloudbandpy.misc import parse_arguments
from cloudbandpy.time_utilities import add_startend_datetime2config


def create_bins(min_value=0.01, max_value=100, stepbins=5):
    bins = np.linspace(min_value, max_value, stepbins)
    return bins


def pdfbinned(bins, variable):
    qt = [0] * bins
    for idx, q in enumerate(bins):
        if idx < np.size(bins) - 1:
            qabove = bins[idx + 1]
            pts = [i for i in range(len(variable)) if q <= variable[i] < qabove]
            Ps = [variable[p] for p in pts]
        elif idx == np.size(bins) - 1:
            continue
        qt[idx] = np.size(Ps) / float(len(variable))
    return qt


def plot_distribution_cb_area(cbarea1, cbarea2):
    # Distribution
    bins = create_bins(min_value=min(cbarea1), max_value=max(cbarea1), stepbins=100)
    qt1 = pdfbinned(bins, cbarea1)
    qt2 = pdfbinned(bins, cbarea2)
    # Figure
    set_fontsize(size=14)
    mpl.rcParams["axes.spines.left"] = True
    mpl.rcParams["axes.spines.right"] = False
    mpl.rcParams["axes.spines.top"] = False
    mpl.rcParams["axes.spines.bottom"] = True
    #
    yearstart = config["datetime_startdate"].year
    yearend = config["datetime_enddate"].year
    fig, ax = plt.subplots()
    ax.plot(bins, qt1, color="#3abc76", label=f"{yearstart}-{yearend}")
    ax.plot(bins, qt2, color="#3f4d89", label=f"{yearstart}-{yearend} DJFM")
    #
    ax.set_yticks([el * 1e-2 for el in np.arange(0, 4.5, 0.5)])
    ax.set_yticklabels([f"{el:2.1f}" for el in [el for el in np.arange(0, 4.5, 0.5)]])
    ax.set_xticks([el * 1e7 for el in np.arange(0.25, 2.5, 0.25)])
    ax.set_xticklabels([f"{el:3.1f}" for el in [el * 10 for el in np.arange(0.25, 2.5, 0.25)]])
    ax.set(xlabel=r"Cloud band area (10$^6\,$m$^2$)", ylabel=r"Standardized distribution (10$^{-2}$)")
    plt.legend(framealpha=0.0)
    return fig


if __name__ == "__main__":
    # Load analysis configuration file
    args = parse_arguments()
    config_file = args.config_file
    config = load_ymlfile(config_file, isconfigfile=True)
    # Make sure the dates are covering the whole period
    config_copy = config.copy()
    config_copy["startdate"] = "19590101.00"
    config_copy["enddate"] = "20211231.00"
    add_startend_datetime2config(config_copy)
    
    list_of_cloud_bandsSP = load_data_from_saved_var_files(config_copy, varname="list_of_cloud_bands")
    config_copy["select_djfm"] = True
    list_of_cloud_bandsSP_djfm = load_data_from_saved_var_files(config_copy, varname="list_of_cloud_bands")
    # flatten list of cloud band areas
    cb_areaSP = [cb.area for sublist in list_of_cloud_bandsSP for cb in sublist]
    cb_areaSP_djfm = [cb.area for sublist in list_of_cloud_bandsSP_djfm for cb in sublist]
    fig = plot_distribution_cb_area(cb_areaSP, cb_areaSP_djfm)
    fig.show()
    figurename = f"{config_copy['dir_figures']}/distribution_cb_area_{config_copy['datetime_startdate'].year}_{config_copy['datetime_enddate'].year}_fullperiod_vs_djfm_{config_copy['domain']}.png"
    fig.savefig(figurename, dpi=200, bbox_inches="tight")