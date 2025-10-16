import os
import json
import importlib

# Load default config from config.py
config = importlib.import_module("config")

# Load config.json if present (or override via env var)
CONFIG_FILE = os.getenv("VIREC_CONFIG", "config.json")
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f:
            json_config = json.load(f)
        # Always add/override values dynamically
        for key, value in json_config.items():
            setattr(config, key, value)
    except Exception as e:
        print(f"⚠️ Could not load {CONFIG_FILE}: {e}")

# Dynamically expose all config variables (no manual list required)
for key in dir(config):
    if not key.startswith("__"):
        globals()[key] = getattr(config, key)


# Optional helper: safe getter with default
def get_config(key, default=None):
    return globals().get(key, default)
