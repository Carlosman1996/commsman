# build.py
import sys
import platform
from pathlib import Path
import PyInstaller.__main__

from config import PROJECT_PATH


APP_NAME = "Commsman"
ENTRY_SCRIPT = "start.py"
DIST_PATH = str(PROJECT_PATH) + "/dist"


def build_add_data_args(items, sep):
    args = []
    for item in items:
        path = Path(item)
        if not path.exists():
            continue
        if path.is_file():
            args.append(f"--add-data={path}{sep}.")
        elif path.is_dir():
            args.append(f"--add-data={path}{sep}{path}")
    return args


def run_pyinstaller():
    print(f"Building {APP_NAME}...")

    system = platform.system()
    name = {
        "Windows": f"{APP_NAME}.exe",
        "Darwin": f"{APP_NAME}-mac",
        "Linux": f"{APP_NAME}-linux"
    }.get(system, APP_NAME)

    items_to_include = [
        "config.json",
        "alembic.ini",
        "README.md",
        "LICENSE.txt",
        "frontend/fixtures",
        "alembic"
    ]
    sep = ";" if sys.platform.startswith("win") else ":"

    add_data_args = build_add_data_args(items_to_include, sep)

    # Essential PyInstaller arguments
    args = [
        "--name", name,
        "--icon=frontend/fixtures/icons/commsman.ico",
        # "--onedir", # Test mode
        "--onefile",
        # "--console",  # Test mode
        "--windowed",
        "--clean",
        "--noconfirm",
        "--hidden-import=logging.config",
        *add_data_args,
        ENTRY_SCRIPT
    ]

    # Filter out multiprocessing arguments that might interfere
    print("Running PyInstaller with args:", args)
    PyInstaller.__main__.run(args)

    print(f"Build complete. Executable in: dist/{name}")


if __name__ == "__main__":
    run_pyinstaller()
