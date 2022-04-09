import re
import time
from datetime import date, datetime, timedelta

import pandas as pd
import requests
from parse import *
from suntime import Sun

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

def clean_hour(hour_str):
    return hour_str.replace(" ", ":00 ").upper()


def pad(s, l=8):
    if len(s) < l:
        return s + " " * (l - len(s))
    else:
        return s


def get_weather_hourly(mgr, d, config):
    lat_long = config["lat_long"]

    one_call = mgr.one_call(
        lat=lat_long[0],
        lon=lat_long[1],
        exclude="minutely, daily",
        units="imperial",
    )
    current = one_call.current
    time_start = datetime.combine(date.today(), datetime.min.time())
    time_end = datetime.combine(
        date.today() + timedelta(days=d["n_days"]), datetime.min.time()
    )

    date_range = pd.date_range(time_start, time_end, freq="H")
    forecast = one_call.forecast_hourly
    n_periods = d["n_days"] * 24 + 1

    unix_times = [int(time.mktime(t.timetuple())) for t in date_range]

    weather_calls = []
    for i in range(len(date_range)):
        if date_range[i] < datetime.now():
            weather_calls.append(
                mgr.one_call_history(
                    lat=lat_long[0], lon=lat_long[1], dt=unix_times[i]
                ).current
            )
    weather_calls.append(current)
    weather_calls += forecast[1 : n_periods - len(weather_calls) + 1]

    return weather_calls


def get_weather_daily(mgr, d, config):
    lat_long = config["lat_long"]

    one_call = mgr.one_call(
        lat=lat_long[0],
        lon=lat_long[1],
        exclude="minutely, hourly",
        units="imperial",
    )

    forecast = one_call.forecast_daily
    n_periods = d["n_days"]

    weather_calls = forecast[:n_periods]

    return weather_calls


def get_sun(d, config):
    dates = [date.today() + timedelta(days=i) for i in range(d["n_days"])]

    sun = Sun(config["lat_long"][0], config["lat_long"][1])

    sun_dict = {}
    sun_dict["sunrises"] = [sun.get_sunrise_time(date) for date in dates]
    sun_dict["sunsets"] = [sun.get_sunset_time(date) for date in dates]

    return sun_dict


def get_historical_temperatures(d, config):
    dates = [date.today() + timedelta(days=i) for i in range(d["n_days"])]

    temp_dict = {}
    page_text = requests.get(
        f"https://weather.com/weather/monthly/l/{config['loc_hash']}"
    ).text
    start_loc = re.search(r"getSunV3DailyAlmanacUrlConfig", page_text).end(0)
    search_str = page_text[start_loc : start_loc + 10000]
    for temp_obs in [
        "almanacRecordDate",
        "temperatureAverageMin",
        "temperatureAverageMax",
        "temperatureRecordMax",
        "temperatureRecordMin",
    ]:
        value_str = re.search(
            r'"{}\\":\[(.*?)\]'.format(temp_obs), search_str
        ).group(1)
        if temp_obs == "almanacRecordDate":
            temp_dict[temp_obs] = [
                datetime.strptime(
                    x.strip('"\\') + str(date.today().year), "%m%d%Y"
                ).date()
                for x in value_str.split(",")
            ]
        else:
            temp_dict[temp_obs] = [float(x) for x in value_str.split(",")]

    out_dict = {k: [] for k in temp_dict.keys()}
    for idx in range(len(temp_dict["almanacRecordDate"])):
        if temp_dict["almanacRecordDate"][idx] in dates:
            for k in temp_dict.keys():
                out_dict[k].append(temp_dict[k][idx])

    return out_dict


def Soup(url):
    print(requests.get(url))
