"""
    We need a special function to read from a fully fledged .toml file
    No need to have write function since we are not changing the app config
    during a configuration session
"""

import tomllib

_cached_config = None

def get_config(config_path: str):
    global _cached_config
    if _cached_config is None:
        with open(config_path, "rb") as f:
            _cached_config = tomllib.load(f)
    return _cached_config
