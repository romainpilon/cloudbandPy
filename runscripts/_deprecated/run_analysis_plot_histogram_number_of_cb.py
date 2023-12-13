#!/usr/bin/env python
# coding: utf-8
"""
Create a histogram showing the percentage of the cloud band number distribution for 2 periods: DJFM and full years

Run: python cloudbandPy/analysis/run_analysis_plot_histogram_number_of_cb.py cloudbandPy/config/config_analysis.yml
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import sys


from cloudbandpy.figure_tools import set_fontsize
from cloudbandpy.io_utilities import load_ymlfile, load_data_from_saved_var_files
from cloudbandpy.misc import parse_arguments
from cloudbandpy.time_utilities import add_startend_datetime2config


def plot_histogram_number_of_cloudbands(number_of_cb_per_day1, number_of_cb_per_day2):
    # Distribution
    bins = np.arange(5)
    hisSP = np.histogram(number_of_cb_per_day1, bins=bins, density=True)
    hisSP_djfm = np.histogram(number_of_cb_per_day2, bins=bins, density=True)
    # Figure
    set_fontsize(size=14)
    mpl.rcParams["axes.spines.left"] = True
    mpl.rcParams["axes.spines.right"] = False
    mpl.rcParams["axes.spines.top"] = False
    mpl.rcParams["axes.spines.bottom"] = True
    width = 0.4
    #
    yearstart = config["datetime_startdate"].year
    yearend = config["datetime_enddate"].year
    fig, ax = plt.subplots()
    ax.bar(bins[:-1], hisSP[0], color="#3abc76", width=width, label=f"{yearstart}-{yearend}")
    ax.bar(bins[:-1] + width, hisSP_djfm[0], color="#3f4d89", width=width, label=f"{yearstart}-{yearend} DJFM")
    for p in ax.patches:
        width = p.get_width()
        height = p.get_height()
        x, y = p.get_xy()
        ax.annotate(f"{height*100:2.1f}", (x + width / 2, y + height + 0.01), ha="center")
    #
    ax.set_xticks(bins[:-1] + width / 2.0, [0, 1, 2, 3])
    ax.set_yticks(np.linspace(0, 1, 11))
    ax.set_ylim([0, 0.6])
    ax.set(xlabel="Number of cloud bands", ylabel="Standardized occurrence")
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
    # Load cloud bands
    list_of_cloud_bandsSP = load_data_from_saved_var_files(config, varname="list_of_cloud_bands")
    config["select_djfm"] = True
    list_of_cloud_bandsSP_djfm = load_data_from_saved_var_files(config, varname="list_of_cloud_bands")
    # -> number of cloud bands for each day
    nb_cb_each_dateSP = [len(el) for el in list_of_cloud_bandsSP]
    nb_cb_each_dateSP_djfm = [len(el) for el in list_of_cloud_bandsSP_djfm]
    figurename = f"{config['dir_figures']}/histogram_cb_{config['datetime_startdate'].year}_{config['datetime_enddate'].year}_fullmonth_vs_djfm_{config['domain']}.png"
    fig = plot_histogram_number_of_cloudbands(nb_cb_each_dateSP, nb_cb_each_dateSP_djfm)
    fig.show()
    fig.savefig(figurename, dpi=300, bbox_inches="tight")
