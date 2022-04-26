#!/usr/bin/env python3
"""Display weather forecast according to user config."""

# TODO: add in tide data
# TODO: get tide data automatically from lat_lon with saved data on lat/long and available station IDs
# TODO: a bit of shading for historical avg. high and low (lower alpha than true daily values)
# TODO: shade daily highs and lows as range instead of lines
# TODO: print #s in daily
# TODO: allow subsetting for rain/clouds, temperature, and wind/tides
# TODO: lighter gridlines at 2 hour marks for hourly
# TODO: add some kind of location label for all plots

# base imports
import argparse
import json
import re
import warnings
from contextlib import suppress
from pathlib import Path
from matplotlib.pyplot import hist

import requests

from weather.helpers import plotting, scrape
from weather.helpers.configure import config_path, init_config, timed_sleep, reformat

def add_location(config):
    loc_config = {}
    alias = ""
    while alias == "":
        alias = input(reformat(f"Provide an alias for this location: Existing aliases are {list(config.keys())}", input_type="input"))
        if alias.upper() in config.keys():
            alias = ""; print("\nAlias already exists in keys.")
            timed_sleep()
    loc_config["loc_hash"] = ""
    while True:
        if loc_config["loc_hash"] == "":
            input_str = "Please navigate to the weather.com page for the location and enter the URL below. The url should follow the format (https://weather.com/weather/[timeframe]/l/[location_hash])"
        else:
            input_str = "There was a problem verifying your location. Please verify your entry and try again:"
        with suppress(ValueError):
            loc_config["loc_hash"] = Path(
                input(reformat(input_str, input_type="input"))
            ).stem
            page_text = requests.get(
                f"https://weather.com/weather/today/l/{loc_config['loc_hash']}"
            ).text
            # get latitude and logitude by regex to ensure we've found a page
            match = re.search(
                r'"latitude\\":(.*?),\\"longitude\\":(.*?),', page_text
            )
        if match is not None:
            config[alias] = loc_config
            loc_config["lat_lon"] = (float(match.group(1)), float(match.group(2)))
            json.dump(config, open(config_path, "w"))
            print(f"\n\tLocation successfully initialized and saved.")
            timed_sleep()
            return loc_config

def main():
    config = init_config()

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
    parser.add_argument(
        "-add_location",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, add a new location.",
    )
    parser.add_argument(
        "-rm_location",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, remove an existing location.",
    )
    parser.add_argument(
        "-set_default",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, set a new default location.",
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

    locations = config.keys()
    if d["rm_location"]:
        if not locations:
            raise ValueError(
                reformat(
                    "No locations yet initialized."
                )
            )
        else:
            loc = ""
            while loc not in locations:
                loc = input(reformat(f"Location options are {locations}. Enter the location to be removed.", input_type="input")).upper()
            del config[loc]
            print(f"Location {loc} successfully removed.")
            json.dump(config, open(config_path, "w"))
            return 1
    if d["set_default"]:
        loc = ""
        while loc not in locations:
            loc = input(reformat(f"Location options are {locations}. Enter the location to be set as default (case insensitive).", input_type="input")).upper()
        x_dict = {k:v for k,v in config.items() if k != loc}
        config = {loc: config[loc], **x_dict}
        json.dump(config, open(config_path, "w"))
    if len(config) is 0 or d["add_location"]:
        loc_config = add_location(config)
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
            f"https://weather.com/weather/{page}/l/{loc_config['loc_hash']}"
        ).text

    if d["n_days"] <= 2:
        if not d["d"]:
            weather_dict = scrape.get_weather_hourly(soup)
        else:
            weather_dict = scrape.get_weather_hourly_h(soup)
        weather_dict = {k:v[:d["n_days"]*24] for k,v in weather_dict.items()}
        sun_dict = scrape.get_sun(soup, d)
        weather_dict.update(sun_dict)
    else:
        weather_dict = scrape.get_weather_daily(soup)
        historical_temp_dict = scrape.get_historical_temperatures(soup, d)
        weather_dict.update(historical_temp_dict)
    tide_dict = scrape.get_tides(loc_config, d)
    weather_dict.update(tide_dict)

    if not d["print"]:
        if d["terminal"]:
            plotting.plot_terminal(weather_dict, sun_dict, d)
        else:
            plotting.plot_matplot(weather_dict, sun_dict, d)

if __name__ == "__main__":
    main()
