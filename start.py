# start.py
import sys
import os
import time
import requests
import argparse
from multiprocessing import Process
from config import PROJECT_PATH, load_app_config, ALEMBIC_INI, DB_FILE, LOG_BACKEND_PATH, LOG_FRONTEND_PATH, LOG_PATH


from backend import main as backend_main
from frontend import main_window as frontend_main


def run_alembic_migrations():
    print("🛠️  Running Alembic migrations...")
    from subprocess import run
    run(["alembic", "-c", str(ALEMBIC_INI), "upgrade", "head"], cwd=PROJECT_PATH)


def rebuild_database():
    if os.path.exists(DB_FILE):
        print("⚠️  Removing existing database...")
        os.remove(DB_FILE)
    run_alembic_migrations()


def run_backend(host, port, db_url):
    if not os.path.exists(LOG_BACKEND_PATH):
        os.makedirs(LOG_BACKEND_PATH)
    with open(str(LOG_BACKEND_PATH) + "/logs.txt", "w") as f:
        sys.stdout = f
        sys.stderr = f
        backend_main.run(debug=False, database_url=db_url, host=host, port=port)


def run_frontend(host, port):
    if not os.path.exists(LOG_FRONTEND_PATH):
        os.makedirs(LOG_FRONTEND_PATH)
    with open(str(LOG_FRONTEND_PATH) + "/logs.txt", "w") as f:
        sys.stdout = f
        sys.stderr = f
        frontend_main.run(host=host, port=port)


def wait_for_backend(config, timeout=10):
    api_url = f"http://{config['api']['host']}:{config['api']['port']}"
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


def parse_args():
    parser = argparse.ArgumentParser(description="Start frontend and backend.")
    parser.add_argument("--rebuild-db", action="store_true", help="Recreate the database before launching.")
    parser.add_argument("--test", action="store_true", help="Dry run without launching apps.")
    return parser.parse_args()


def main():
    args = parse_args()

    print(f"📁 Logs path: {LOG_PATH}")

    config = load_app_config()

    if args.rebuild_db:
        rebuild_database()
    elif not os.path.exists(DB_FILE):
        run_alembic_migrations()

    if args.test:
        print("✅ Test mode: config loaded, DB check passed. No apps launched.")
        return

    backend_proc = Process(target=run_backend, args=(config["api"]["host"], config["api"]["port"], config["db"]["url"]))
    backend_proc.start()

    if wait_for_backend(config):
        frontend_proc = Process(target=run_frontend, args=(config["api"]["host"], config["api"]["port"]))
        frontend_proc.start()

        try:
            while True:
                if not frontend_proc.is_alive():
                    print("🖥️ Frontend closed.")
                    break
                if not backend_proc.is_alive():
                    print("🌐 Backend terminated.")
                    break
                time.sleep(0.5)

        except KeyboardInterrupt:
            print("🛑 Keyboard interrupt received.")

        finally:
            if frontend_proc.is_alive():
                print("🛑 Terminating frontend...")
                frontend_proc.terminate()
                frontend_proc.join()

            if backend_proc.is_alive():
                print("🛑 Terminating backend...")
                backend_proc.terminate()
                backend_proc.join()

    else:
        print("💥 Backend not available, aborting.")
        backend_proc.terminate()
        backend_proc.join()


if __name__ == "__main__":
    main()
