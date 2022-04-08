#!/usr/bin/env python3
"""Display weather forecast according to user config."""

# base imports
import argparse
import json
import re
from contextlib import suppress
from pathlib import Path
from pprint import pprint

import numpy as np
import requests
from pyowm.owm import OWM

from weather.helpers import helpers, plotting, scrape
from weather.helpers.configure import config_path, init_config, timed_sleep
from weather.helpers.printing import reformat, set_entry_size_manual


def request_config():
    config = json.load(open(config_path, "r"))
    key = ""
    while True:
        if key == "":
            input_str = "Please enter your OpenWeatherMap API key:"
        else:
            input_str = "There was a problem verifying your key. Please verify your entry and try again:"
        key = input(reformat(input_str, input_type="input"))
        with suppress(ValueError):
            owm = OWM(key)
        if owm is not None:
            config["key"] = key
            json.dump(config, open(config_path, "w"))
            print("\n\tKey successfully initialized and saved.")
            timed_sleep()
            return owm, key


def request_location(owm, config):
    lat_long = ""
    while True:
        if lat_long == "":
            input_str = "Please navigate to your local weather.com page and enter the URL below. The url should follow the format (https://weather.com/weather/[timeframe]/l/[location_hash])"
        else:
            input_str = "There was a problem verifying your location. Please verify your entry and try again:"
        with suppress(ValueError):
            config["loc_hash"] = Path(
                input(reformat(input_str, input_type="input"))
            ).stem
            page_text = requests.get(
                f"https://weather.com/weather/today/l/{config['loc_hash']}"
            ).text
            match = re.search(
                r'"latitude\\":(.*?),\\"longitude\\":(.*?),', page_text
            )
        if match is not None:
            config["lat_lon"] = (float(match.group(1)), float(match.group(2)))
            json.dump(config, open(config_path, "w"))
            print(f"\n\tLocation successfully initialized and saved.")
            timed_sleep()
            return config


def main():
    init_config()

    # establish parser to pull in projects to view
    parser = argparse.ArgumentParser(description="Input parameters.")
    config = json.load(open(config_path, "r"))

    parser.add_argument(
        "n_days",
        type=int,
        nargs="?",
        default=config["n_days"],
        help="Number of days to show. If n_days <= 2, forecasts will be shown at the hourly level.",
    )
    parser.add_argument(
        "-show",
        type=str,
        nargs="+",
        default=config["show"],
        choices=helpers.fields,
        help="Attributes to show.",
    )
    parser.add_argument(
        "-matplot",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, print to terminal instead of standard matplotlib.show().",
    )
    parser.add_argument(
        "-save_config",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, save the provided configuration (at the 'graph' level) as default.",
    )
    parser.add_argument(
        "--config_api",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, reconfigure api.",
    )
    parser.add_argument(
        "--config_location",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, reconfigure location.",
    )
    d = vars(parser.parse_args())

    if d["save_config"]:
        json.dump(
            {k: v for k, v in d.items() if k not in ["graph", "save_config"]},
            open(config_path, "w"),
        )

        print(reformat(f"Parameters saved. Defaults are now:"))
        show_width = sum([len(s) + 4 for s in config["config"]["show"]]) + 14
        pprint(config["config"], indent=4)
        print("")
        set_entry_size_manual(
            height=len(config) + 8, width=np.max([29, show_width])
        )
        timed_sleep()

    if config["key"] is None or d["config_api"]:
        owm, config["key"] = request_config()
    else:
        owm = OWM(config["key"])
    if config["lat_long"] is None or d["config_location"]:
        config["lat_long"] = request_location(owm, config)

    today_soup = requests.get(
        f"https://weather.com/weather/today/l/{config['loc_hash']}"
    ).text
    hourly_soup = requests.get(
        f"https://weather.com/weather/hourbyhour/l/{config['loc_hash']}"
    ).text
    daily_soup = requests.get(
        f"https://weather.com/weather/monthly/l/{config['loc_hash']}"
    ).text
    soup = today_soup + daily_soup + hourly_soup

    # If it does exist, get weather using location
    if d["n_days"] <= 2:
        weather_dict = scrape.get_weather_hourly(soup, d=d)
    else:
        weather_dict = scrape.get_weather_daily(soup)
    sun_dict = scrape.get_sun(soup, d)
    historical_temp_dict = scrape.get_historical_temperatures(soup, d)

    if not d["matplot"]:
        plotting.plot_terminal(weather_dict, sun_dict, historical_temp_dict, d)
    else:
        plotting.plot_matplot(weather_dict, sun_dict, historical_temp_dict, d)
    # if d["timeframe"] in ["15m", "hourly"]:
    #     d["periods"] = len(weather_dict[d["timeframe"]]["validTimeLocal"])
    #     graph.hourly_graph(d, weather_dict)
    # elif d["timeframe"] in ["daily", "day_night"]:
    #     d["periods"] = len(weather_dict[d["timeframe"]]["validTimeLocal"])
    #     graph.daily_graph(d, weather_dict)


if __name__ == "__main__":
    main()
