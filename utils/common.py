import os
import pathlib

PROJECT_PATH = pathlib.Path(__file__).parent.parent.resolve()
FRONTEND_PATH = os.path.join(PROJECT_PATH, "frontend")
BACKEND_PATH = os.path.join(PROJECT_PATH, "backend")
UTILS_PATH = os.path.join(PROJECT_PATH, "utils")
OUTPUTS_PATH = os.path.join(PROJECT_PATH, "outputs")
