import calendar
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotext as plt

from weather.helpers.printing import set_entry_size_manual


def get_sun_moves(weather_dict):
    sun = {"sunrises": [], "sunsets": []}
    day = 0
    while len(sun["sunrises"]) + len(sun["sunsets"]) < 6:
        sunrise_time = weather_dict["daily"]["sunriseTimeLocal"][day]
        sunset_time = weather_dict["daily"]["sunsetTimeLocal"][day]
        if sunrise_time > datetime.now():
            sun["sunrises"].append(sunrise_time)
            sun["sunsets"].append(sunset_time)
        else:
            sun["sunsets"].append(sunset_time)
        day += 1
    return sun


def relTime(times, time0, fifteen_m: bool):
    relTime = [(t - time0).total_seconds() / 3600 for t in times]
    if fifteen_m:
        relTime = [t * 4 for t in relTime]

    return relTime


# def process_weather_calls(weather_calls):
#     weather_dict = {}
#     for call in weather_calls:
#         weather_dict[call.reference_time()] = {
#             "temp":call.temperature('fahrenheit')["temp"],
#             "feel":call.temperature('fahrenheit')["feels_like"],
#             "hum":call.humidity,
#             "wind":call.wind()["speed"],
#             "wind_dir": call.wind()["deg"],
#             "cover":call.clouds
#         }


def daily_plot(d: dict, weather_dict: dict, day_night: bool = False):
    pass


def my_step(yvals, label, idx):
    if label == "precip":
        yvals = [y[0] for y in yvals]
    xvals = (
        [idx[0]]
        + [np.mean([i, i + 1]) for i in idx[:-1] for x in range(2)]
        + [idx[-1]]
    )
    yvals = [y for y in yvals for x in range(2)]
    plt.plot(xvals, yvals, label=label)


def plot_terminal(weather_dict, sun_dict, historical_temp_dict, d):
    import plotext as plt

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
        plt.xlim(0, np.max(idx))
        xticks = [datetime.strftime(x, "%I:%M") for x in time_range]
        plt.xticks(ticks=idx[::2], labels=xticks[::2])
        plt.ylim(0, 100)
        plt.yticks(range(0, 101, 10))
        plt.plot_size(150, 40)
        plt.limit_size(False, False)
        plt.grid(True)
        for m in sun_dict["sunriseTimeLocal"]:
            m = (m - time_range[0]).total_seconds() / 3600
            plt.vertical_line(m, color=226)
        for m in sun_dict["sunsetTimeLocal"]:
            m = (m - time_range[0]).total_seconds() / 3600
            plt.vertical_line(m, color=220)
        plt.vertical_line(timediff, color=1)
        plt.show()
        set_entry_size_manual(height=41, width=154)
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
        plt.xlim(0, np.max(idx))
        plt.xticks(ticks=idx, labels=time_range)
        plt.ylim(0, 100)
        plt.yticks(range(0, 101, 10))
        plt.plot_size(150, 40)
        plt.limit_size(False, False)
        plt.grid(True)
        plt.show()
        set_entry_size_manual(height=41, width=154)


def plot_matplot(weather_dict, sun_dict, historical_temp_dict, d):
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
                plt.step(idx, yvals[: len(idx)], label=label, alpha=0.8)
        plt.xlim(0, np.max(idx))
        xticks = [datetime.strftime(x, "%I:%M") for x in time_range]
        plt.xticks(ticks=idx[::4], labels=xticks[::4])
        plt.ylim(0, 100)
        plt.yticks(range(0, 101, 10))
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
                plt.step(idx, yvals[: len(idx)], label=label, alpha=0.8)
        plt.xlim(0, np.max(idx))
        plt.xticks(ticks=idx, labels=time_range)
        plt.ylim(0, 100)
        plt.yticks(range(0, 101, 10))
    plt.grid(True)
    plt.legend(loc="upper right")
    plt.show()
