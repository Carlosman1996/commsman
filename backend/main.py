import argparse
import json

from flask import Flask
from backend.repository.sqlite_repository import SQLiteRepository
from backend.core.backend_manager import BackendManager
from backend.api import register_routes
from utils.common import PROJECT_PATH, load_app_config


def create_app(database):
    app = Flask(__name__)

    repository_manager = SQLiteRepository()
    backend_manager = BackendManager(repository=repository_manager)

    register_routes(app, repository_manager, backend_manager)

    return app


if __name__ == "__main__":
    config = load_app_config()

    parser = argparse.ArgumentParser(description="Start backend.")
    parser.add_argument("--db", help="Database URL.", default=config["db"]["url"])
    parser.add_argument("--debug", help="API debug mode.", default=config["api"]["debug"])
    parser.add_argument("--host", help="API host.", default=config["api"]["host"])
    parser.add_argument("--port", help="API port.", default=config["api"]["port"])
    args = parser.parse_args()

    app = create_app(database=args.db)
    app.run(debug=args.debug, host=args.host, port=args.port)
