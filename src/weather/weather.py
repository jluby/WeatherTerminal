#!/usr/bin/env python3
"""Display weather forecast according to user config."""

# TODO: get wind to show with turned arrow (on matplot)
# TODO: allow subsetting for rain/clouds, temperature, and wind/tides
# TODO: add in tide data
# TODO: make print function, include emojis for hourly blocks in day (maybe just for today and tomorrow)
# Make print on the daily level for 9am, 1pm, 5pm, 9pm

# base imports
import argparse
import json
import re
import warnings
from contextlib import suppress
from pathlib import Path
from pprint import pprint

import requests

from weather.helpers import plotting, scrape
from weather.helpers.configure import config_path, init_config, timed_sleep
from weather.helpers.printing import reformat, set_entry_size_manual


def request_location(config):
    config["loc_hash"] = ""
    while True:
        if config["loc_hash"] == "":
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
            # get latitude and logitude by regex
            match = re.search(
                r'"latitude\\":(.*?),\\"longitude\\":(.*?),', page_text
            )
        if match is not None:
            config["lat_lon"] = (float(match.group(1)), float(match.group(2)))
            json.dump(config, open(config_path, "w"))
            print(f"\n\tLocation successfully initialized and saved.")
            timed_sleep()
            return config["loc_hash"]


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
        "-print",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Print results. Only supported for n_days >= 3.",
    )
    parser.add_argument(
        "-show",
        type=str,
        nargs="?",
        choices=[
            "rain",
            "temp",
            "row",
        ],  # rain: precipChance, cloudCover. temp: temperature, temperatureFeelsLike. row: windSpeed, windDirection, tides
        help="Attributes types to show.",
    )
    parser.add_argument(
        "-terminal",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, display with 'plotext' in terminal instead of 'matplotlib'.",
    )
    parser.add_argument(
        "-save_config",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, save the provided configuration as default.",
    )
    parser.add_argument(
        "--config_location",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="If provided, reconfigure location.",
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

    if d["save_config"]:
        json.dump(
            {k: v for k, v in d.items() if k != "save_config"},
            open(config_path, "w"),
        )

        print(reformat(f"Parameters saved. Defaults are now:"))
        pprint(config["config"], indent=4)
        print("")
        timed_sleep()

    if config["loc_hash"] is None or d["config_location"]:
        config["loc_hash"] = request_location(config)

    soup = ""
    for page in ["today", "hourbyhour", "monthly"]:
        soup += requests.get(
            f"https://weather.com/weather/{page}/l/{config['loc_hash']}"
        ).text

    if d["n_days"] <= 2:
        weather_dict = scrape.get_weather_hourly(soup, d=d)
    else:
        weather_dict = scrape.get_weather_daily(soup)
    sun_dict = scrape.get_sun(soup, d)
    historical_temp_dict = scrape.get_historical_temperatures(soup, d)

    if not d["print"]:
        if d["terminal"]:
            plotting.plot_terminal(weather_dict, sun_dict, d)
        else:
            plotting.plot_matplot(weather_dict, sun_dict, d)
    else:
        printing.print_weather(weather_dict, sun_dict, historical_temp_dict, d)


if __name__ == "__main__":
    main()
