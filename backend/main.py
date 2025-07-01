import argparse

from flask import Flask
from backend.repository.sqlite_repository import SQLiteRepository
from backend.core.backend_manager import BackendManager
from backend.api import register_routes
from config import load_app_config



def create_app(database_url):
    app = Flask(__name__)

    repository_manager = SQLiteRepository(database_url=database_url)
    backend_manager = BackendManager(repository=repository_manager)

    register_routes(app, repository_manager, backend_manager)

    return app


def run(host: str, port: int, debug: bool, database_url: str):
    app = create_app(database_url=database_url)
    app.run(debug=debug, host=host, port=port)


if __name__ == "__main__":
    config = load_app_config()

    parser = argparse.ArgumentParser(description="Start backend.")
    parser.add_argument("--db", help="Database URL.", default=config["db"]["url"])
    parser.add_argument("--debug", help="API debug mode.", default=config["api"]["debug"])
    parser.add_argument("--host", help="API host.", default=config["api"]["host"])
    parser.add_argument("--port", help="API port.", default=config["api"]["port"])
    args = parser.parse_args()

    run(database_url=args.db, debug=args.debug, host=args.host, port=args.port)
