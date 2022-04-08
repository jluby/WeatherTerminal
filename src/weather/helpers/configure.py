import json
import os
import time
from pathlib import Path

pkg_path = Path(__file__).parents[1]
config_path = f"{pkg_path}/.config/config.json"


def timed_sleep(t=1):
    time.sleep(t)


def init_config():
    if not os.path.isfile(config_path):
        config = {
            "loc_hash": None,
            "lat_lon": None,
            "n_days": 1,
            "show": ["precip", "temp", "feel", "cover"],
        }
        os.makedirs(Path(config_path).parents[0])
        json.dump(config, open(config_path, "w"))
