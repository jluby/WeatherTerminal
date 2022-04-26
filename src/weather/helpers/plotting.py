import calendar
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import plotext

from weather.helpers.configure import set_entry_size_manual

def normalize(series):
    return (series - np.min(series))/(np.max(series) - min(series))*100

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


def plot_terminal(weather_dict, d):
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
        for m in weather_dict["sunriseTimeLocal"]:
            m = (m - time_range[0]).total_seconds() / 3600
            plotext.vertical_line(m, color=226)
        for m in weather_dict["sunsetTimeLocal"]:
            m = (m - time_range[0]).total_seconds() / 3600
            plotext.vertical_line(m, color=220)
        timediff = (datetime.now() - time_range[0]).total_seconds() / 3600
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

def define_marker(windDirection):
    if windDirection == "N":
        return "$\u2B06$"
    elif windDirection == "W":
        return "$\u2B05$"
    elif windDirection == "S":
        return "$\u2B07$"
    elif windDirection == "E":
        return "$\u27A1$"
    elif "N" in windDirection and "W" in windDirection:
        return "$\u2B09$"
    elif "S" in windDirection and "W" in windDirection:
        return "$\u2B0B$"
    elif "N" in windDirection and "E" in windDirection:
        return "$\u2B08$"
    elif "S" in windDirection and "E" in windDirection:
        return "$\u2B0A$"


def plot_matplot(weather_dict, d):
    """Plot to standard matplotlib output."""
    import matplotlib.pyplot as plt

    plt.rcParams["figure.figsize"] = (20, 7)
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.serif'] = 'Helvetica Neue'
    plt.rcParams['font.size'] = 8

    if d["n_days"] <= 2:
        title_str = "Hourly"
        if d["d"]:
            time_start = datetime.combine(date.today(), datetime.min.time())
            time_end = datetime.combine(
                date.today() + timedelta(days=d["n_days"]), datetime.min.time()
            )
            time_range = [
                t.to_pydatetime()
                for t in pd.date_range(time_start, time_end, freq="H")
            ][:-1]
            # plot current time
            timediff = (datetime.now() - time_range[0]).total_seconds() / 3600
            plt.vlines(timediff, ymin=0, ymax=100, alpha=0.8, color="red")
        else:
            time_range = weather_dict["validTimeLocal"]
        plot_dicts = [
                {"v": weather_dict["temperature"], "c": "#FF3838", "label": "Temperature (°F)"},
                {"v": weather_dict["temperatureFeelsLike"], "c": "#FFB338", "label": "Temperature Feels Like (°F)"},
                {"v": weather_dict["precipChance"], "c": "#4A5CFF", "label": "Precipitation Chance (%)"},
                {"v": weather_dict["cloudCover"], "c": "#A912E0", "label": "Cloud Cover (%)"},
                {"v": weather_dict["windSpeed"], "c": "#3FBE34", "label": "Wind Speed (mph)"}
        ]
        idx = [i for i in range(len(time_range))]
        for plot_dict in plot_dicts:
            plot_dict["v"] = plot_dict["v"] + [float("NaN")] * (len(idx)-len(plot_dict["v"]))
            if plot_dict["label"] != "Wind Speed (mph)":
                plt.step(idx, plot_dict["v"][: len(idx)], alpha=0.8, where="mid", color=plot_dict["c"], label=plot_dict["label"])
            else:
                plt.plot([], [], color=plot_dict["c"], marker=define_marker("N"), linestyle='None',
                          markersize=5, label='Wind Speed (mph)')
                for i in idx:
                    plt.plot(i, plot_dict["v"][i], color=plot_dict["c"], marker=define_marker(weather_dict["windDirectionCardinal"][i]))
        xticks = [datetime.strftime(x, "%I:%M") for x in time_range]
        plt.xticks(ticks=idx[::2], labels=[x if i%2 == 0 else None for i,x in enumerate(xticks[::2])])
        sunrise_diffs = [(m - time_range[0]).total_seconds() / 3600 for m in weather_dict["sunriseTimeLocal"]]
        sunset_diffs = [(m - time_range[0]).total_seconds() / 3600 for m in weather_dict["sunsetTimeLocal"]]
        plt.vlines(
            sunrise_diffs, ymin=0, ymax=100, alpha=0.8, linestyles=":", color="gold"
        )
        plt.vlines(
            sunset_diffs, ymin=0, ymax=100, alpha=0.8, linestyles=":", color="#FFC838"
        )
        night_periods = (
            [(sunrise_diffs[0]-12, sunrise_diffs[0])] + 
            [(sunset_diffs[i], sunrise_diffs[i+1]) for i in range(len(sunset_diffs)-1)] +
            [(sunset_diffs[-1], sunset_diffs[-1]+12)]
            )
        for p in night_periods:
            # add shading to nighttime
            plt.axvspan(p[0], p[1], alpha=.1, color='black')
        if "water_level" in weather_dict.keys():
            tides = {"rel_time":[], "water_level":[]}
            for i, t in enumerate(weather_dict["local_time"]):
                if t >= time_range[0] and t <= time_range[-1]:
                    rel_time = (t - time_range[0]).total_seconds()/3600
                    tides["rel_time"].append(rel_time); tides["water_level"].append(weather_dict["water_level"][i])
            tides["water_level"] = normalize(tides["water_level"])
            plt.plot(tides["rel_time"], tides["water_level"], label="Water Level (Relative %)", alpha=.2)
    else:
        title_str = "Daily"
        today = date.today()
        time_range = [
            calendar.day_name[(today + timedelta(days=i)).weekday()]
            for i in range(d["n_days"])
        ]
        plot_dicts = [
                {"v": weather_dict["precipChance"], "c": "#4A5CFF", "label": "Precipitation Chance (%)"},
                {"v": weather_dict["cloudCover"], "c": "#A912E0", "label": "Cloud Cover (%)"},
                {"v": weather_dict["windSpeed"], "c": "#3FBE34", "label": "Wind Speed (mph)"}
        ]
        idx = [i for i in range(len(time_range))]
        for plot_dict in plot_dicts:
            yvals = [v if v != "null" else float("NaN") for v in plot_dict["v"]]
            yvals = yvals + [float("NaN")] * (len(idx)-len(yvals))
            if plot_dict["label"] != "Wind Speed (mph)":
                plt.step(idx, yvals[: len(idx)], alpha=0.8, where="mid", color=plot_dict["c"], label=plot_dict["label"])
            else:
                plt.plot([], [], color=plot_dict["c"], marker=define_marker("N"), linestyle='None',
                          label='Wind Speed (mph)')
                for i in idx:
                    plt.plot(i, yvals[i], color=plot_dict["c"], marker=define_marker(weather_dict["windDirectionCardinal"][i]))
        temperature_dicts = [
            {"v": [weather_dict["calendarDayTemperatureMin"], weather_dict["calendarDayTemperatureMax"]], "c": "#6ED322", "label": "Temperature Range (°F)", "alpha": .7},
            {"v": [weather_dict["temperatureAverageMin"], weather_dict["temperatureAverageMax"]], "c": "#F7F957", "label": "Historical Average Temperature Range (°F)", "alpha": .1}
        ]
        for temp_dict in temperature_dicts:
            yvals = [[v if v != "null" else float("NaN") for v in l] + [float("NaN")] * (len(idx)-len(temp_dict["v"][0])) for l in temp_dict["v"]]
            if temp_dict["label"] == "Temperature Range (°F)":
                plt.fill_between(idx, yvals[0][: len(idx)], yvals[1][: len(idx)], step="mid", alpha=temp_dict["alpha"], color=temp_dict["c"], label=temp_dict["label"])
            else:
                for i in range(2):
                    plt.step(idx, yvals[i], where="mid", linestyle='--', label=temp_dict["label"] if i == 0 else None, alpha=.3, color="black")
        plt.xticks(ticks=idx, labels=time_range)
        plt.title(f"Daily Weather Forecast for {weather_dict['name']}")
    plt.xlim(0, np.max(idx))
    plt.ylim(0, 100)
    plt.yticks(range(0, 101, 10))
    plt.grid(True)
    plt.legend(loc="upper right")
    plt.title(f"{title_str} Weather Forecast for {weather_dict['name']}")
    plt.show()
