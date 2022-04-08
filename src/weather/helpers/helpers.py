fields = ["wind", "precip", "hum", "temp", "feel", "sun", "temp_history"]

attr_map = {
    "desc": ["wxPhraseLong"],
    "wind": ["windDirectionCardinal", "windSpeed"],
    "rain": ["precipType", "precipChance"],
    "hum": ["relativeHumidity"],
    "temp": ["temperature"],
    "feel": ["temperatureFeelsLike"],
    "sun": ["sunriseTimeLocal", "sunsetTimeLocal"],
    "temp_history": [
        "temperatureAverageMin",
        "temperatureAverageMax",
        "temperatureRecordMin",
        "temperatureRecordMax",
    ],
}
