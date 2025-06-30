import json
import os
import pathlib
import socket

from platformdirs import user_data_dir
from pathlib import Path


APP_NAME = "commsman"
PROJECT_PATH = pathlib.Path(__file__).parent.parent.resolve()
FRONTEND_PATH = os.path.join(PROJECT_PATH, "frontend")
BACKEND_PATH = os.path.join(PROJECT_PATH, "backend")
UTILS_PATH = os.path.join(PROJECT_PATH, "utils")
OUTPUTS_PATH = os.path.join(PROJECT_PATH, "outputs")
CONFIG_FILE = os.path.join(PROJECT_PATH, "config.json")


def get_data_path() -> Path:
    db_dir = Path(user_data_dir(APP_NAME))
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir


def find_free_port(start_port=5000, max_tries=100):
    """Find an available port starting from `start_port`."""
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available port found in range {start_port}-{start_port + max_tries}")


def load_app_config():
    with open(CONFIG_FILE) as f:
        config = json.load(f)
        config["api"]["port"] = find_free_port()
        return config
