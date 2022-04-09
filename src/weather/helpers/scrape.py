import re
from datetime import date, datetime, timedelta

import pandas as pd
import requests
from parse import *

hour_attrs = [
    "validTimeLocal",
    "precipType",
    "temperature",
    "temperatureFeelsLike",
    "windDirection",
    "windSpeed",
    "relativeHumidity",
    "precipChance",
    "cloudCover",
]
day_attrs = [
    "calendarDayTemperatureMax",
    "calendarDayTemperatureMin",
    "precipChance",
    "precipType",
    "cloudCover",
    "windSpeed",
    "windDirection",
]


def clean_hour(hour_str):
    return hour_str.replace(" ", ":00 ").upper()


def pad(s, l=8):
    if len(s) < l:
        return s + " " * (l - len(s))
    else:
        return s


def get_weather_hourly(soup, d):
    time_start = datetime.combine(date.today(), datetime.min.time())
    time_end = datetime.combine(
        date.today() + timedelta(days=d["n_days"]), datetime.min.time()
    )

    time_range = pd.date_range(time_start, time_end, freq="H")

    past_times = [t.to_pydatetime() for t in time_range if t < datetime.now()]
    forecast_times = [
        t.to_pydatetime() for t in time_range if t > datetime.now()
    ]
    historical_obs = process_by_time_hourly(
        soup, "getSunV3HistoricalOneDayHourlyConditionsUrlConfig", past_times
    )
    forecast_obs = process_by_time_hourly(
        soup, "getSunV3HourlyForecastWithHeadersUrlConfig", forecast_times
    )

    weather_dict = {k: [] for k in hour_attrs}
    for k in weather_dict.keys():
        for obs_dict in [historical_obs, forecast_obs]:
            if k in obs_dict.keys() and obs_dict[k] is not None:
                weather_dict[k] += obs_dict[k]
            else:
                weather_dict[k] += [
                    None for i in range(len(obs_dict["validTimeLocal"]))
                ]

    return weather_dict


def get_weather_daily(soup):

    forecast_obs = process_by_time_daily(soup)

    return forecast_obs


def process_by_time_daily(soup):
    start_loc = re.search(
        r"getSunV3DailyForecastWithHeadersUrlConfig", soup
    ).end(0)
    search_str = soup[start_loc : start_loc + 15000]
    obs = {k: None for k in day_attrs}
    for a in day_attrs:
        match = re.search(r'"{}\\":\[(.*?)\],'.format(a), search_str)
        if match:
            list_str = match.group(1)
            obs_list = list_str.split(",")
            obs[a] = (
                [x.strip('"\\') for x in obs_list]
                if a == "precipType"
                else [float(x) if x != "null" else x for x in obs_list]
            )
    return obs


def process_by_time_hourly(soup, header, times):
    # get loc where time in list and append all values to obs
    start_loc = re.search(r"{}".format(header), soup).end(0)
    search_str = soup[start_loc : start_loc + 15000]
    unordered_obs = {k: None for k in hour_attrs}
    for a in hour_attrs:
        match = re.search(r'"{}\\":\[(.*?)\],'.format(a), search_str)
        if match:
            list_str = match.group(1)
            unordered_obs[a] = (
                [x.strip('"\\') for x in list_str.split(",")]
                if a in ["validTimeLocal", "precipType"]
                else [float(x) for x in list_str.split(",")]
            )
    unordered_obs["validTimeLocal"] = [
        datetime.strptime(x[:19], "%Y-%m-%dT%H:%M:%S")
        for x in unordered_obs["validTimeLocal"]
    ]

    ordered_obs = {k: [] for k in hour_attrs if unordered_obs[k] is not None}
    for t in times:
        if t in unordered_obs["validTimeLocal"]:
            idx = unordered_obs["validTimeLocal"].index(t)
            for a in ordered_obs.keys():
                ordered_obs[a].append(unordered_obs[a][idx])

    return ordered_obs


def process_current_weather(soup, header):
    # get loc where time in list and append all values to obs
    start_loc = re.search(r"{}".format(header), soup).end(0)
    search_str = soup[start_loc : start_loc + 15000]
    obs = {k: None for k in hour_attrs}
    for a in hour_attrs:
        match = re.search(r'"{}\\":(.*?),'.format(a), search_str)
        if match:
            match_str = match.group(1)
            obs[a] = (
                [match_str.strip('"\\')]
                if a in ["validTimeLocal", "precipType"]
                else [float(match_str)]
            )
    obs["validTimeLocal"] = [
        datetime.strptime(obs["validTimeLocal"][0][:19], "%Y-%m-%dT%H:%M:%S")
    ]

    return obs


def get_sun(soup, d):

    # get loc where time in list and append all values to obs
    start_loc = re.search(
        r"getSunV3DailyForecastWithHeadersUrlConfig", soup
    ).end(0)
    search_str = soup[start_loc : start_loc + 15000]
    attrs = ["sunriseTimeLocal", "sunsetTimeLocal"]
    sun_dict = {k: None for k in attrs}
    for a in attrs:
        match = re.search(r'"{}\\":\[(.*?)\],'.format(a), search_str)
        list_str = match.group(1)
        sun_dict[a] = [
            datetime.strptime(x.strip('"\\')[:19], "%Y-%m-%dT%H:%M:%S")
            for x in list_str.split(",")
        ][: d["n_days"]]

    return sun_dict


def get_historical_temperatures(soup, d):
    dates = [date.today() + timedelta(days=i) for i in range(d["n_days"])]
    temp_dict = {}
    start_loc = re.search(r"getSunV3DailyAlmanacUrlConfig", soup).end(0)
    search_str = soup[start_loc : start_loc + 10000]
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
