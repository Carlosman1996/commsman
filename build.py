# build.py
import os
import sys
import subprocess
import shutil
from pathlib import Path

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
    print(f"📦 Building {APP_NAME}...")

    shutil.rmtree(DIST_PATH, ignore_errors=True)

    items_to_include = [
        "config.json",
        "alembic.ini",
        "frontend/fixtures",
    ]
    sep = ";" if sys.platform.startswith("win") else ":"
    # List any files or folders to include

    add_data_args = build_add_data_args(items_to_include, sep)

    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        *add_data_args,
        ENTRY_SCRIPT
    ]

    print("🔧 Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"✅ Build complete. Executable in: dist/{APP_NAME}")


if __name__ == "__main__":
    run_pyinstaller()
