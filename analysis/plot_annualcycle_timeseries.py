#!/usr/bin/env python
# coding: utf-8
"""
Plot the annual cycles of:
- the number of cloud bands per month
- the mean number of cloud band days per month

and plot the number of cloud band per year,
for the South Pacific, North Pacific, South Atlantic and Indian Ocean domains,
as defined by the configuration files

Run: python cloudbandPy/analysis/plot_annualcycle_timeseries.py config_analysis.yml
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.patheffects as mpe
from matplotlib.ticker import MultipleLocator

import pandas as pd
import sys


from cloudbandPy.src.figure_tools import set_fontsize
from cloudbandPy.src.io_utilities import load_ymlfile, load_multiyears_data


def set_figures_props():
    set_fontsize(size=13)
    mpl.rcParams["axes.spines.left"] = True
    mpl.rcParams["axes.spines.right"] = False
    mpl.rcParams["axes.spines.top"] = False
    mpl.rcParams["axes.spines.bottom"] = True
    return


def get_cmap(n, name="viridis"):
    """Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
    RGB color; the keyword argument name must be a standard mpl colormap name."""
    return mpl.cm.get_cmap(name, n)


def plot_mean_ncloudband_per_year(yearlymsum):
    set_figures_props()
    # mean number of cloud band per month on the whole ERA5 period
    cmap = get_cmap(len(yearlymsum.keys()[:-1]))
    fig, ax = plt.subplots(1, 1, figsize=(11, 4))
    for i, name in enumerate(yearlymsum.keys()[:-1]):  # no index
        ax.plot(yearlymsum.index, yearlymsum[name], lw=2, c=cmap(i), label=name)
    #
    ax.set_xticklabels(yearlymsum.index)
    ax.xaxis.set_major_locator(mdates.YearLocator(10))
    ax.xaxis.set_minor_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlabel("Years")
    ax.set_ylabel("Number of cloud bands per years")
    plt.legend(
        bbox_to_anchor=(0, 1.02, 0.6, 0.2),
        loc="lower center",
        mode="expand",
        borderaxespad=0,
        ncol=2,
        framealpha=0.5,
    )
    return fig


def plot_mean_ncloudband_per_month(monthlysum):
    set_figures_props()
    # mean number of cloud band per month on the whole ERA5 period
    nyears = 61.0
    cmap = get_cmap(len(monthlysum.keys()[:-1]))
    fig, ax = plt.subplots(1, 1, figsize=(7, 5))
    for i, name in enumerate(monthlysum.keys()[:-1]):  # no index
        ax.plot(
            monthlysum.index, monthlysum[name] / nyears, lw=2, c=cmap(i), label=name
        )
    #
    ax.set_xticks(range(1, 13))
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.set_xlabel("Months")
    ax.set_ylabel("Number of cloud bands per month")
    plt.legend(
        bbox_to_anchor=(0, 1.02, 1, 0.2),
        loc="lower left",
        mode="expand",
        borderaxespad=0,
        ncol=2,
        framealpha=0.5,
    )
    return fig


def plot_mean_ncloud_band_days_permonth(monthlymean, monthlymax):
    set_figures_props()
    """Plot the mean number of cloud per day per month"""
    set_fontsize(size=13)
    mpl.rcParams["axes.spines.left"] = True
    mpl.rcParams["axes.spines.right"] = False
    mpl.rcParams["axes.spines.top"] = False
    mpl.rcParams["axes.spines.bottom"] = True
    width = 0.6
    pe1 = [mpe.Stroke(linewidth=3, foreground="black"), mpe.Normal()]
    fig, ax = plt.subplots(2, 2, figsize=(10, 10))
    ax[0, 0].bar(
        monthlymean.index,
        monthlymax["South Pacific"],
        width,
        alpha=0.8,
        color="#3f4d89",
        label="South Pacific",
    )
    ax[0, 0].plot(
        monthlymean.index,
        monthlymean["South Pacific"],
        path_effects=pe1,
        lw=3,
        color="#3f4d89",
    )
    ax[0, 0].set_title("a) South Pacific", loc="left")
    ax[0, 1].bar(
        monthlymean.index,
        monthlymax["North Pacific"],
        width,
        alpha=0.8,
        color="#3f4d89",
        label="North Pacific",
    )
    ax[0, 1].plot(
        monthlymean.index,
        monthlymean["North Pacific"],
        path_effects=pe1,
        lw=3,
        color="#3f4d89",
    )
    ax[0, 1].set_title("b) North Pacific", loc="left")
    ax[1, 0].bar(
        monthlymean.index,
        monthlymax["South Atlantic"],
        width,
        alpha=0.8,
        color="#3f4d89",
        label="South Atlantic",
    )
    ax[1, 0].plot(
        monthlymean.index,
        monthlymean["South Atlantic"],
        path_effects=pe1,
        lw=3,
        color="#3f4d89",
    )
    ax[1, 0].set_title("c) South Atlantic", loc="left")
    ax[1, 1].bar(
        monthlymean.index,
        monthlymax["Indian Ocean"],
        width,
        alpha=0.8,
        color="#3f4d89",
        label="Indian Ocean",
    )
    ax[1, 1].plot(
        monthlymean.index,
        monthlymean["Indian Ocean"],
        path_effects=pe1,
        lw=3,
        color="#3f4d89",
    )
    ax[1, 1].set_title("d) Indian Ocean", loc="left")
    for ax in ax.ravel():
        ax.set_xticks(range(13))
        ax.yaxis.set_minor_locator(MultipleLocator(0.2))
        ax.set_yticks(range(5))
        ax.set_xlabel("Months")

    fig.subplots_adjust(wspace=0.2, hspace=0.3)
    return fig


if __name__ == "__main__":
    config_file = sys.argv[-1]
    config = load_ymlfile(config_file)
    config["domain"] = "southPacific"
    list_of_cloud_bandsSP = load_multiyears_data(config, varname="list_of_cloud_bands")
    config["domain"] = "northPacific"
    list_of_cloud_bandsNP = load_multiyears_data(config, varname="list_of_cloud_bands")
    config["domain"] = "southAtlantic"
    list_of_cloud_bandsSA = load_multiyears_data(config, varname="list_of_cloud_bands")
    config["domain"] = "southAfricaIO"
    list_of_cloud_bandsAIO = load_multiyears_data(config, varname="list_of_cloud_bands")

    list_dates = load_multiyears_data(config, varname="listofdates")
    pdlist_dates = pd.to_datetime(list_dates)
    # -> number of cloud bands for each day
    nb_cb_each_dateSP = [len(el) for el in list_of_cloud_bandsSP]
    nb_cb_each_dateNP = [len(el) for el in list_of_cloud_bandsNP]
    nb_cb_each_dateSA = [len(el) for el in list_of_cloud_bandsSA]
    nb_cb_each_dateAIO = [len(el) for el in list_of_cloud_bandsAIO]

    # -> to pandas for easier data handling
    list4pandas = [
        [a, b, c, d, e]
        for a, b, c, d, e in zip(
            pdlist_dates,
            nb_cb_each_dateSP,
            nb_cb_each_dateNP,
            nb_cb_each_dateSA,
            nb_cb_each_dateAIO,
        )
    ]
    # Get monthly and yearly mean of cloud bands number per day (should be improved)
    df = pd.DataFrame(
        list4pandas,
        columns=[
            "time",
            "South Pacific",
            "North Pacific",
            "South Atlantic",
            "Indian Ocean",
        ],
    )
    df_daily = df.set_index("time")
    df_daily["year"] = df_daily.index.year
    df_daily["month"] = df_daily.index.month

    df2 = df_daily["South Pacific"]
    df3 = df_daily["North Pacific"]
    df4 = df_daily["South Atlantic"]
    df5 = df_daily["Indian Ocean"]
    newdf_daily = pd.concat(
        [df2, df3],
        axis=0,
        keys=["South Pacific", "North Pacific", "South Atlantic", "Indian Ocean"],
    ).reset_index()
    newdf_daily.columns = ["basin", "time", "ncb"]
    newdf_daily.set_index("time", inplace=True)
    newdf_daily["year"] = newdf_daily.index.year
    newdf_daily["month"] = newdf_daily.index.month

    monthlymax = df_daily.groupby("month").max()
    monthlymean = df_daily.groupby("month").mean()
    monthlysum = df_daily.groupby("month").sum()

    yearlymax = df_daily.groupby("year").max()
    yearlymean = df_daily.groupby("year").mean()
    yearlymsum = df_daily.groupby("year").sum()

    yearlymax.index = pd.to_datetime(yearlymax.index, format="%Y")
    yearlymsum.index = pd.to_datetime(yearlymsum.index, format="%Y")
    yearlymean.index = pd.to_datetime(range(1960, 2022), format="%Y")

    fig1 = plot_mean_ncloudband_per_year(yearlymsum)
    fig1.show()
    fig1.savefig(
        f"{config['dir_figures']}/n_cb_per_year_{config['startdate'][:4]}_{config['enddate'][:4]}_4basins.png",
        dpi=200,
        bbox_inches="tight",
    )

    fig2 = plot_mean_ncloudband_per_month(monthlysum)
    fig2.show()
    fig2.savefig(
        f"{config['dir_figures']}/annualcycle_n_cb_per_month_{config['startdate'][:4]}_{config['enddate'][:4]}_4basins.png",
        dpi=200,
        bbox_inches="tight",
    )

    fig3 = plot_mean_ncloud_band_days_permonth(monthlymean, monthlymax)
    fig3.show()
    fig3.savefig(
        f"{config['dir_figures']}/annualcycle_mean_cloudband_days_{config['startdate'][:4]}_{config['enddate'][:4]}_4basins.png",
        dpi=200,
        bbox_inches="tight",
    )
