#!/usr/bin/env python3
"""Display weather forecast according to user config."""

# TODO: print #s in daily
# TODO: allow subsetting for rain/clouds, temperature, and wind/tides

# base imports
import argparse
import json
import re

import requests

from weather.helpers import plotting, scrape
from weather.helpers.configure import PKG_PATH, reformat


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

    if len(config) is 0:
        raise ValueError(
            reformat("No config yet specified.", input_type="error")
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
        soup += requests.get(
            f"https://weather.com/weather/{page}/l/{loc_config['weather_hash']}"
        ).text
    lat_long_str = re.search(
        r'"latitude\\":(.*?),\\"longitude\\":(.*?),', soup
    )
    loc_config["lat_lon"] = (
        float(lat_long_str.group(1)),
        float(lat_long_str.group(2)),
    )

    if d["n_days"] <= 2:
        if not d["d"]:
            weather_dict = scrape.get_weather_hourly(soup)
        else:
            weather_dict = scrape.get_weather_hourly_h(soup)
        weather_dict = {
            k: v[: d["n_days"] * 24] for k, v in weather_dict.items()
        }
        sun_dict = scrape.get_sun(soup, d)
        weather_dict.update(sun_dict)
    else:
        historical_temp_dict = scrape.get_historical_temperatures(soup, d)
        weather_dict = scrape.get_weather_daily(soup)
        weather_dict.update(historical_temp_dict)
    if "tide_station" in loc_config.keys():
        tide_dict = scrape.get_tides(loc_config, d)
        weather_dict.update(tide_dict)

    weather_dict["name"] = (
        re.search(
            r"Hourly Weather Forecast for(.*?)- The Weather Channel", soup
        )
        .group(1)
        .strip()
    )

    if d["terminal"]:
        plotting.plot_terminal(weather_dict, d)
    else:
        plotting.plot_matplot(weather_dict, d)


if __name__ == "__main__":
    main()
