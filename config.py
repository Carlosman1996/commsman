import pathlib
import sys
from datetime import datetime
import json
import os
import socket
import platform

from pathlib import Path


APP_NAME = "commsman"


if hasattr(sys, '_MEIPASS'):
    PROJECT_PATH = Path(sys._MEIPASS)
    if platform.system() == "Windows":
        PROJECT_DATA_PATH = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "commsman"
    else:
        PROJECT_DATA_PATH = Path.home() / ".local" / "share" / "commsman"
    os.makedirs(PROJECT_DATA_PATH, exist_ok=True)
else:
    PROJECT_PATH = Path(__file__).parent.resolve()
    PROJECT_DATA_PATH = PROJECT_PATH


FRONTEND_PATH = os.path.join(PROJECT_PATH, "frontend")
BACKEND_PATH = os.path.join(PROJECT_PATH, "backend")
UTILS_PATH = os.path.join(PROJECT_PATH, "utils")
OUTPUTS_PATH = os.path.join(PROJECT_PATH, "outputs")
CONFIG_FILE = os.path.join(PROJECT_PATH, "config.json")
ALEMBIC_PATH = os.path.join(PROJECT_PATH, "alembic")
ALEMBIC_INI = os.path.join(PROJECT_PATH, "alembic.ini")


TIMESTAMP = int(datetime.now().timestamp())


LOG_PATH = os.path.join(PROJECT_DATA_PATH, f"logs/logs_{TIMESTAMP}")
LOG_BACKEND_PATH = os.path.join(LOG_PATH, "backend")
LOG_FRONTEND_PATH = os.path.join(LOG_PATH, "frontend")
DB_FILE = os.path.join(PROJECT_DATA_PATH, "commsman.db")


SQLALCHEMY_URL = f"sqlite:///{DB_FILE}"


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


def load_app_config(find_port: bool = True):
    with open(CONFIG_FILE) as f:
        config = json.load(f)
        config["db"]["url"] = SQLALCHEMY_URL
        if find_port:
            config["api"]["port"] = find_free_port()
        return config
