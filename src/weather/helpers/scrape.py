import re
from datetime import date, datetime, timedelta

import pandas as pd
import requests
from parse import *
import warnings

import noaa_coops as nc

hour_attrs = [
    "validTimeLocal",
    "precipType",
    "temperature",
    "temperatureFeelsLike",
    "windDirectionCardinal",
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
    "windDirectionCardinal",
]


def clean_hour(hour_str):
    return hour_str.replace(" ", ":00 ").upper()


def pad(s, l=8):
    if len(s) < l:
        return s + " " * (l - len(s))
    else:
        return s

def get_weather_hourly(soup):
    # get loc where time in list and append all values to obs
    start_loc = re.search(r"{}".format("getSunV3HourlyForecastWithHeadersUrlConfig"), soup).end(0)
    search_str = soup[start_loc : start_loc + 15000]
    weather_dict = {k: None for k in hour_attrs}
    for a in hour_attrs:
        match = re.search(r'"{}\\":\[(.*?)\],'.format(a), search_str)
        if match:
            obs_list = [x.strip('"\\') for x in match.group(1).split(",")]
            if a not in ["validTimeLocal", "precipType", "windDirectionCardinal"]:
                obs_list = [float(x) for x in obs_list]
            weather_dict[a] = obs_list
    weather_dict["validTimeLocal"] = [
        datetime.strptime(x[:19], "%Y-%m-%dT%H:%M:%S")
        for x in weather_dict["validTimeLocal"]
    ]
    
    return weather_dict

def get_weather_hourly_h(soup):
    time_start = datetime.combine(date.today(), datetime.min.time())
    time_end = datetime.combine(
        date.today() + timedelta(days=2), datetime.min.time()
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
    start_loc = re.search(
        r"getSunV3DailyForecastWithHeadersUrlConfig", soup
    ).end(0)
    search_str = soup[start_loc : start_loc + 30000]
    obs = {k: None for k in day_attrs}
    for a in day_attrs:
        match = re.findall(r'"{}\\":\[(.*?)\],'.format(a), search_str)
        if match:
            obs_list = [x.strip('"\\') for x in match[1].split(",")]
            if a not in ["precipType", "windDirectionCardinal"]:
                obs_list = [float(x) if x != "null" else x for x in obs_list]
            if a not in ["calendarDayTemperatureMax", "calendarDayTemperatureMin"]:
                obs_list = obs_list[::2]
            obs[a] = obs_list
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
                if a in ["validTimeLocal", "precipType", "windDirectionCardinal"]
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
        ][:3]

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

def get_tides(tide_station, d):
    station = nc.Station(tide_station)
    try:
        df_water_levels = station.get_data(
            begin_date=date.today().strftime("%Y%m%d"),
            end_date= (date.today() + timedelta(days=d["days"])).strftime("%Y%m%d"),
            product="water_level",
            datum="MLLW",
            units="metric",
            time_zone="gmt")
    except:
        warnings.warn(f"No valid datum value for MLLW ***station={tide_station}")
        return {}
    print(df_water_levels)
    exit()

def Soup(url):
    print(requests.get(url))
