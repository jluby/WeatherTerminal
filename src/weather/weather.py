#!/usr/bin/env python3
"""Utilities for local weather plotting."""

# base imports
import argparse
import json
import re
from contextlib import suppress
from datetime import date, timedelta
from pathlib import Path
from pprint import pprint

import noaa_coops as nc
import requests

from weather.helpers import plotting, scrape
from weather.helpers.configure import config_path, init_config, reformat


def add_location(config):
    loc_config = {}
    aliases = list(config.keys())
    alias = ""
    while alias == "":
        alias = input(f"\nProvide an alias for this location: Existing aliases are: {aliases}\n\t").upper()
        if alias in config.keys():
            alias = ""
            print("\nAlias already exists in keys.\n")
    loc_config["weather_hash"] = ""
    match = None
    while match is None:
        if loc_config["weather_hash"] == "":
            input_str = "Please navigate to the weather.com page for the location and enter the URL below. The url should follow the format (https://weather.com/weather/[timeframe]/l/[location_hash])"
        else:
            input_str = "There was a problem verifying your location. Please verify your entry and try again:"
        with suppress(ValueError):
            loc_config["weather_hash"] = Path(input(reformat(input_str, input_type="input"))).stem
            page_text = requests.get(f"https://weather.com/weather/hourly/l/{loc_config['weather_hash']}").text
            # get latitude and logitude by regex to ensure we've found a page
            match = re.search(r'"latitude\\":(.*?),\\"longitude\\":(.*?),', page_text)
    config[alias] = loc_config
    config[alias]["lat_lon"] = (float(match.group(1)), float(match.group(2)))
    config[alias]["name"] = (
        re.search(r"Hourly Weather Forecast for(.*?)- The Weather Channel", page_text).group(1).strip()
    )

    json.dump(config, open(config_path, "w"))
    print("\n\tLocation successfully initialized and saved.\n")


def add_tides(config):
    aliases = list(config.keys())
    alias = ""
    while alias.upper() not in aliases:
        alias = input(f"\tTo which location would you like to add tides? Available aliases are: {aliases}\n\t").upper()
    station = input(
        "\n\tEnter the 7-digit NOAA station ID for this location. Stations can be found at https://tidesandcurrents.noaa.gov/\n\t"
    )
    try:
        nc_station = nc.Station(int(station))
        nc_station.get_data(
            begin_date=(date.today() - timedelta(days=1)).strftime("%Y%m%d"),
            end_date=(date.today() + timedelta(days=1)).strftime("%Y%m%d"),
            product="predictions",
            datum="MLLW",
            units="metric",
            time_zone="gmt",
        )
    except:
        raise ValueError(
            f"No valid datum value for MLLW ***station={station} Please check the station ID and try again."
        )

    config[alias]["tide_station"] = int(station)
    json.dump(config, open(config_path, "w"))
    print("\n\tTide station successfully initialized and saved.\n")


def rm_location(config):
    aliases = list(config.keys())
    rm_loc = ""
    while rm_loc.upper() not in aliases:
        rm_loc = input(f"\tWhich location would you like to remove? Available aliases are: {aliases}\n\t").upper()
    del config[rm_loc]
    json.dump(config, open(config_path, "w"))
    print("\n\tLocation metadata successfully deleted.\n")


def set_location(config):
    aliases = list(config.keys())
    set_loc = ""
    while set_loc.upper() not in aliases:
        set_loc = input(
            f"\tWhich location would you like to set as default? Available aliases are: {aliases}\n\t"
        ).upper()
    config = {**{set_loc: config[set_loc]}, **{k: v for k, v in config.items() if k != set_loc}}
    json.dump(config, open(config_path, "w"))
    print("\n\tLocation successfully set as default.\n")


def list_locations(config):
    print("\nAvailable locations are:")
    pprint({alias: config[alias]["name"] for alias in config.keys()})
    print("")


def main():
    config = init_config()

    # establish parser to pull in projects to view
    parser = argparse.ArgumentParser(description="Utilities for local weather plotting.")

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
        "-d",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, include today's history in hourly plotting.",
    )
    parser.add_argument(
        "-tide",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, plot tides when 'tide_station' has been specified in config.json.",
    )
    parser.add_argument(
        "-add_location",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, add a new location.",
    )
    parser.add_argument(
        "-add_tides",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, add a new tide station.",
    )
    parser.add_argument(
        "-rm_location",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, remove a saved location.",
    )
    parser.add_argument(
        "-set_location",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, set a specified saved location as default.",
    )
    parser.add_argument(
        "-list",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, list all available locations.",
    )
    d = vars(parser.parse_args())

    if sum([d["add_location"], d["add_tides"], d["rm_location"], d["set_location"], d["list"]]) > 1:
        raise ValueError(
            reformat(
                "Only one of -add_location, -add_tides, -rm_location, -set_location, or -list may be provided at one time.",
                input_type="error",
            )
        )
    elif sum([d["add_location"], d["add_tides"], d["rm_location"], d["set_location"], d["list"]]) == 1:
        if d["add_location"]:
            add_location(config)
        elif d["add_tides"]:
            add_tides(config)
        elif d["rm_location"]:
            rm_location(config)
        elif d["set_location"]:
            set_location(config)
        elif d["list"]:
            list_locations(config)
    else:
        if len(config) == 0:
            raise ValueError(
                reformat(
                    "No config yet specified. Use -add_location argument to initialize a weather location.",
                    input_type="error",
                )
            )
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
                        input_type="error",
                    )
                )

        soup = ""
        for page in ["today", "hourbyhour", "monthly"]:
            soup += requests.get(f"https://weather.com/weather/{page}/l/{loc_config['weather_hash']}").text

        if d["n_days"] <= 2:
            if not d["d"]:
                weather_dict = scrape.get_weather_hourly(soup)
            else:
                weather_dict = scrape.get_weather_hourly_h(soup)
            weather_dict = {k: v[: d["n_days"] * 24] for k, v in weather_dict.items()}
            sun_dict = scrape.get_sun(soup, d)
            weather_dict.update(sun_dict)
        else:
            historical_temp_dict = scrape.get_historical_temperatures(soup, d)
            weather_dict = scrape.get_weather_daily(soup)
            weather_dict.update(historical_temp_dict)
        if "tide_station" in loc_config.keys():
            tide_dict = scrape.get_tides(loc_config, d)
            weather_dict.update(tide_dict)

        weather_dict["name"] = loc_config["name"]

        plotting.plot_matplot(weather_dict, d)


if __name__ == "__main__":
    main()
