import calendar
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import plotext

from weather.helpers.printing import set_entry_size_manual


def my_step(yvals, label, idx):
    if label == "precip":
        yvals = [y[0] for y in yvals]
    xvals = (
        [idx[0]]
        + [np.mean([i, i + 1]) for i in idx[:-1] for x in range(2)]
        + [idx[-1]]
    )
    yvals = [y for y in yvals for x in range(2)]
    plotext.plot(xvals, yvals, label=label)


def plot_terminal(weather_dict, sun_dict, d):
    """Plot to terminal."""

    if d["n_days"] <= 2:
        time_start = datetime.combine(date.today(), datetime.min.time())
        time_end = datetime.combine(
            date.today() + timedelta(days=d["n_days"]), datetime.min.time()
        )
        time_range = [
            t.to_pydatetime()
            for t in pd.date_range(time_start, time_end, freq="H")
        ]
        current_time = datetime.now()
        timediff = (current_time - time_range[0]).total_seconds() / 3600
        idx = [i for i in range(len(time_range))]
        for label, yvals in weather_dict.items():
            if label in [
                "temperature",
                "temperatureFeelsLike",
                "precipChance",
                "cloudCover",
                "windSpeed",
            ]:
                my_step(yvals, label=label, idx=idx)
        xticks = [datetime.strftime(x, "%I:%M") for x in time_range]
        plotext.xticks(ticks=idx[::2], labels=xticks[::2])
        for m in sun_dict["sunriseTimeLocal"]:
            m = (m - time_range[0]).total_seconds() / 3600
            plotext.vertical_line(m, color=226)
        for m in sun_dict["sunsetTimeLocal"]:
            m = (m - time_range[0]).total_seconds() / 3600
            plotext.vertical_line(m, color=220)
        plotext.vertical_line(timediff, color=1)
    else:
        today = date.today()
        time_range = [
            calendar.day_name[(today + timedelta(days=i)).weekday()]
            for i in range(d["n_days"])
        ]
        idx = [i for i in range(len(time_range))]
        for label, yvals in weather_dict.items():
            if label in [
                "calendarDayTemperatureMax",
                "calendarDayTemperatureMin",
                "precipChance",
                "cloudCover",
                "windSpeed",
            ]:
                my_step(yvals, label=label, idx=idx)
        plotext.xticks(ticks=idx, labels=time_range)
    plotext.xlim(0, np.max(idx))
    plotext.ylim(0, 100)
    plotext.yticks(range(0, 101, 10))
    plotext.plot_size(150, 40)
    plotext.limit_size(False, False)
    plotext.grid(True)
    plotext.show()
    set_entry_size_manual(height=41, width=154)


def plot_matplot(weather_dict, sun_dict, d):
    """Plot to standard matplotlib output."""
    import matplotlib.pyplot as plt

    plt.rcParams["figure.figsize"] = (20, 7)

    if d["n_days"] <= 2:
        time_start = datetime.combine(date.today(), datetime.min.time())
        time_end = datetime.combine(
            date.today() + timedelta(days=d["n_days"]), datetime.min.time()
        )
        time_range = [
            t.to_pydatetime()
            for t in pd.date_range(time_start, time_end, freq="H")
        ][:-1]
        current_time = datetime.now()
        timediff = (current_time - time_range[0]).total_seconds() / 3600
        idx = [i for i in range(len(time_range))]
        for label, yvals in weather_dict.items():
            if label in [
                "temperature",
                "temperatureFeelsLike",
                "precipChance",
                "cloudCover",
                "windSpeed",
            ]:
                plt.step(idx, yvals[: len(idx)], label=label, alpha=0.8, where="mid")
        xticks = [datetime.strftime(x, "%I:%M") for x in time_range]
        plt.xticks(ticks=idx[::4], labels=xticks[::4])
        for m in sun_dict["sunriseTimeLocal"]:
            m = (m - time_range[0]).total_seconds() / 3600
            plt.vlines(
                m, ymin=0, ymax=100, alpha=0.8, linestyles=":", color="yellow"
            )
        for m in sun_dict["sunsetTimeLocal"]:
            m = (m - time_range[0]).total_seconds() / 3600
            plt.vlines(
                m, ymin=0, ymax=100, alpha=0.8, linestyles=":", color="gold"
            )
        plt.vlines(timediff, ymin=0, ymax=100, alpha=0.8, color="red")
    else:
        today = date.today()
        time_range = [
            calendar.day_name[(today + timedelta(days=i)).weekday()]
            for i in range(d["n_days"])
        ]
        idx = [i for i in range(len(time_range))]
        for label, yvals in weather_dict.items():
            yvals = [y if y != "null" else float("NaN") for y in yvals]
            if label in [
                "calendarDayTemperatureMax",
                "calendarDayTemperatureMin",
                "precipChance",
                "cloudCover",
                "windSpeed",
            ]:
                plt.step(idx, yvals[: len(idx)], label=label, alpha=0.8, where="mid")
        plt.xticks(ticks=idx, labels=time_range)
    plt.xlim(0, np.max(idx))
    plt.ylim(0, 100)
    plt.yticks(range(0, 101, 10))
    plt.grid(True)
    plt.legend(loc="upper right")
    plt.show()
