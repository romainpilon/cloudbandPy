#!/usr/bin/env python
# coding: utf-8
"""
Script to create histogram showing the percentage of the cloud band number distribution
Run: python CloudBandDetection/analysis/plot_distribution_number_of_cb.py config_analysis.yml
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import sys

DIRCODE = "/users/rpilon/codes/unil/CloudBandDetection/"
sys.path.insert(0, DIRCODE + "/src/")
from figure_tools import set_fontsize
from io_utilities import load_ymlfile, load_data_from_saved_var_files

# FIXME
# from CloudBandDetection.src.figure_tools import set_fontsize
# from CloudBandDetection.src.io_utilities import load_ymlfile, load_data_from_saved_var_files


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
    config_file = sys.argv[-1]
    config = load_ymlfile(config_file, isconfigfile=True)
    list_of_cloud_bandsSP = load_data_from_saved_var_files(config, varname="list_of_cloud_bands")
    config["select_djfm"] = True
    list_of_cloud_bandsSP_djfm = load_data_from_saved_var_files(config, varname="list_of_cloud_bands")
    # -> number of cloud bands for each day
    nb_cb_each_dateSP = [len(el) for el in list_of_cloud_bandsSP]
    nb_cb_each_dateSP_djfm = [len(el) for el in list_of_cloud_bandsSP_djfm]
    figurename = f"{config['dir_figures']}/histogram_cb_{config['datetime_startdate'].year}_{config['datetime_enddate'].year}_fullmonth_vs_djfm_{config['domain']}.png"
    fig = plot_histogram_number_of_cloudbands(nb_cb_each_dateSP, nb_cb_each_dateSP_djfm)
    fig.show()
    fig.savefig(figurename, dpi=200, bbox_inches="tight")
