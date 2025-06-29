import os
import pathlib


from platformdirs import user_data_dir
from pathlib import Path


APP_NAME = "commsman"
PROJECT_PATH = pathlib.Path(__file__).parent.parent.resolve()
FRONTEND_PATH = os.path.join(PROJECT_PATH, "frontend")
BACKEND_PATH = os.path.join(PROJECT_PATH, "backend")
UTILS_PATH = os.path.join(PROJECT_PATH, "utils")
OUTPUTS_PATH = os.path.join(PROJECT_PATH, "outputs")


def get_data_path() -> Path:
    db_dir = Path(user_data_dir(APP_NAME))
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir
