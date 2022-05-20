# WeatherTerminal

WeatherTerminal is a package which provides command line tools for local weather plotting in Terminal.

Weather can be plotted at an **hourly** level...

<img width="1175" alt="hourly" src="https://user-images.githubusercontent.com/43190780/167226591-baf987ee-9d98-403e-a1a8-e896c4eac098.png">

or a **daily** level...

<img width="1186" alt="daily" src="https://user-images.githubusercontent.com/43190780/167226580-4a7c4f17-e8a2-4773-aaa4-e2ad74ff8bcc.png">

for any `n_days` specified by the user (hourly forecasts are available for 48 hours and daily forecasts for 14 days).

## Repository Structure

-   `/src/weather_terminal` package, contains CLI scripts and helpers.

## Package Installation

 To install the `weather` package:

1.  Clone this repository. 
2.  From the base directory, run `pip install .` from the command line.

## Usage

This project seeks to provide CLI utilites for local weather. 
Plotting your local weather will require the following:

1.  `weather -add_location`: Add your local weather by providing an alias and a weather.com link from which weather data will be scraped.
2.  `weather N_DAYS ALIAS`: Plot local weather for whatever number of days you like. `n_days` &lt;= 2 will be plotted at the hourly level, while `n_days` > 2 will be plotted at the daily level. If no `alias` is provided, the default location will be used (To change your default location, run `weather -set_location`).
3.  Optionally, you may specify a tide station for a location, such that tidal forecasts will be displayed alongside base weather forecasts. To add a tide station, run `weather -add_tides`.

## Current Maintainers

-   Jack Luby, UChicago Booth Center for Applied AI - jack.o.luby@gmail.com
