import os

halftab = " " * 4


def reformat(string: str, input_type=None):
    """Reformat text inputs depending on type."""
    string = string.replace(". ", ".@")
    sentences = [f"{halftab}{s}" for s in string.split(sep="@")]
    newstring = "\n"
    for s in sentences:
        newstring += f"{s}\n"
    if input_type == "input":
        newstring += "\n\t"
    return newstring


def set_entry_size_manual(height, width):
    """Set terminal window size."""
    os.system("printf '\e[3;0;0t'")
    os.system(f"printf '\e[8;{height};{width}t'")


def print_weather(weather_dict, sun_dict, historical_temp_dict, d):
    pass
