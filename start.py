# start.py
import socket
import sys
from datetime import datetime
import os
import subprocess
import time
import json
import requests
import argparse

from utils.common import PROJECT_PATH, get_data_path, load_app_config

TIMESTAMP = int(datetime.now().timestamp())
LOG_PATH = os.path.join(get_data_path(), f"logs/logs_{TIMESTAMP}")
LOG_BACKEND_PATH = os.path.join(LOG_PATH, "backend")
LOG_FRONTEND_PATH = os.path.join(LOG_PATH, "frontend")
DB_FILE = os.path.join(PROJECT_PATH, "commsman.db")
ALEMBIC_INI = os.path.join(PROJECT_PATH, "alembic.ini")


def run_alembic_migrations():
    print("🛠️  Running Alembic migrations...")
    subprocess.run(["alembic", "-c", str(ALEMBIC_INI), "upgrade", "head"], cwd=PROJECT_PATH)


def rebuild_database():
    if os.path.exists(DB_FILE):
        print("⚠️  Removing existing database...")
        os.remove(DB_FILE)
    run_alembic_migrations()


def start_backend(config):
    print("🚀 Starting backend server...")

    if not os.path.exists(LOG_BACKEND_PATH):
        os.makedirs(LOG_BACKEND_PATH)
    log_file = open(str(LOG_BACKEND_PATH) + "/logs.txt", "w")

    return subprocess.Popen(
        [sys.executable, "-m", "backend.main", f"--debug={config["db"]["url"]}", f"--host={config["api"]["host"]}", f"--port={config["api"]["port"]}"],
        cwd=PROJECT_PATH,
        stdout=log_file,
        stderr=subprocess.STDOUT
    )


def wait_for_backend(config, timeout=10):

    api_url = f"http://{config["api"]["host"]}:{config["api"]["port"]}"

    print(f"⏳ Waiting for backend to become available at {api_url}...")
    for _ in range(timeout):
        try:
            r = requests.get(f"{api_url}/ping", timeout=1)
            if r.status_code == 200:
                print("✅ Backend is live.")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    print("❌ Backend did not respond in time.")
    return False


def start_frontend(config):
    print("🖥️ Starting frontend application...")

    if not os.path.exists(LOG_FRONTEND_PATH):
        os.makedirs(LOG_FRONTEND_PATH)
    log_file = open(str(LOG_FRONTEND_PATH) + "/logs.txt", "w")

    return subprocess.Popen(
        [sys.executable, "-m", "frontend.main_window", f"--host={config["api"]["host"]}", f"--port={config["api"]["port"]}"],
        cwd=PROJECT_PATH,
        stdout=log_file,
        stderr=subprocess.STDOUT
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Start frontend and backend.")
    parser.add_argument("--rebuild-db", action="store_true", help="Recreate the database before launching.")
    parser.add_argument("--test", action="store_true", help="Dry run without launching apps.")
    return parser.parse_args()


def main():
    args = parse_args()

    print(f"📁 Logs path: {LOG_PATH}")

    config = load_app_config()

    # Rebuild DB if requested
    if args.rebuild_db:
        rebuild_database()
    elif not os.path.exists(DB_FILE):
        run_alembic_migrations()

    if args.test:
        print("✅ Test mode: config loaded, DB check passed. No apps launched.")
        return

    backend_proc = start_backend(config)

    if wait_for_backend(config):
        frontend_proc = start_frontend(config)

        try:
            while True:
                if frontend_proc.poll() is not None:
                    print("🖥️ Frontend closed.")
                    break
                if backend_proc.poll() is not None:
                    print("🌐 Backend terminated.")
                    break
                time.sleep(0.5)

        except KeyboardInterrupt:
            print("🛑 Keyboard interrupt received.")

        finally:
            # Terminate both safely
            if frontend_proc.poll() is None:
                print("🛑 Terminating frontend...")
                frontend_proc.terminate()
                frontend_proc.wait()

            if backend_proc.poll() is None:
                print("🛑 Terminating backend...")
                backend_proc.terminate()
                backend_proc.wait()

    else:
        print("💥 Backend not available, aborting.")
        backend_proc.terminate()
        backend_proc.wait()


if __name__ == "__main__":
    main()
