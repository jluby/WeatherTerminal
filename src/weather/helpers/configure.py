import os
import time
from pathlib import Path

PKG_PATH = Path(__file__).parents[1]
config_path = f"{PKG_PATH}/.config/config.json"


def timed_sleep(t=1):
    time.sleep(t)

halftab = " " * 4

def reformat(string: str, input_type=None):
    """Reformat text inputs depending on type."""
    string = string.replace(". ", ".@")
    sentences = [f"{halftab}{s}" for s in string.split(sep="@")]
    newstring = "\n"
    for s in sentences:
        newstring += f"{s}\n"
    if input_type == "input":
        newstring += "\t"
    return newstring

def set_entry_size_manual(height, width):
    """Set terminal window size."""
    os.system("printf '\e[3;0;0t'")
    os.system(f"printf '\e[8;{height};{width}t'")