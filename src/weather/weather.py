#!/usr/bin/env python3
"""Display weather forecast according to user config."""

# TODO: add in tide data
# TODO: a bit of shading for historical avg. high and low
# TODO: print #s in daily
# TODO: allow subsetting for rain/clouds, temperature, and wind/tides
# TODO: lighter gridlines at 2 hour marks for hourly

# base imports
import argparse
import json
from multiprocessing.sharedctypes import Value
import re
import warnings
from contextlib import suppress
from pathlib import Path

import requests

from weather.helpers import plotting, scrape
from weather.helpers.configure import PKG_PATH, config_path, init_config, timed_sleep, reformat

def main():
    config = json.load(open(f"{PKG_PATH}/config.json", "r"))

    # establish parser to pull in projects to view
    parser = argparse.ArgumentParser(description="Input parameters.")

    parser.add_argument(
        "n_days",
        type=int,
        nargs="?",
        default=2,
        help="Number of days to show. If n_days <= 2, forecasts will be shown at the hourly level.",
    )
    parser.add_argument(
        "alias",
        type=str,
        nargs="?",
        help="Provide alias of selected location.",
    )
    parser.add_argument(
        "-print",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Print results. Only supported for n_days >= 3.",
    )
    parser.add_argument(
        "-d",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, include today's history in hourly plotting.",
    )
    parser.add_argument(
        "-show",
        type=str,
        nargs="?",
        choices=[
            "rain",
            "temp",
            "row",
        ],  # rain: precipChance, cloudCover. temp: temperature, temperatureFeelsLike. row: windSpeed, windDirectionCardinal, tides
        help="Attributes types to show.",
    )
    parser.add_argument(
        "-terminal",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, display with 'plotext' in terminal instead of 'matplotlib'.",
    )
    d = vars(parser.parse_args())

    if d["print"]:
        if d["n_days"] <= 2:
            raise ValueError(
                reformat(
                    "Printing is only supported for n_days >= 3.",
                    input_type="error",
                )
            )
        elif d["show"]:
            warnings.warn(
                reformat(
                    "'show' kwarg is only supported for plotting.",
                    input_type="error",
                )
            )
        elif d["terminal"]:
            warnings.warn(
                reformat(
                    "'terminal' argument will be ignored while printing.",
                    input_type="error",
                )
            )

    if len(config) is 0:
        raise ValueError(reformat("No config yet specified.", input_type="error"))
    elif d["alias"] is None:
        loc_config = config[list(config.keys())[0]]
    else:
        d["alias"] = d["alias"].upper()
        if d["alias"] in config.keys():
            loc_config = config[d["alias"]]
        else:
            raise ValueError(
                reformat(
                    f"Provided alias not found in config. Available aliases are {list(config.keys())}",
                    input_type="error"
                    )
                )

    soup = ""
    for page in ["today", "hourbyhour", "monthly"]:
        soup += requests.get(
            f"https://weather.com/weather/{page}/l/{loc_config['weather_hash']}"
        ).text

    if d["n_days"] <= 2:
        if not d["d"]:
            weather_dict = scrape.get_weather_hourly(soup)
        else:
            weather_dict = scrape.get_weather_hourly_h(soup)
        weather_dict = {k:v[:d["n_days"]*24] for k,v in weather_dict.items()}
    else:
        weather_dict = scrape.get_weather_daily(soup)
    sun_dict = scrape.get_sun(soup, d)
    #tide_dict = scrape.get_tides(loc_config)
    historical_temp_dict = scrape.get_historical_temperatures(soup, d)

    if not d["print"]:
        if d["terminal"]:
            plotting.plot_terminal(weather_dict, sun_dict, d)
        else:
            plotting.plot_matplot(weather_dict, sun_dict, d)

if __name__ == "__main__":
    main()
