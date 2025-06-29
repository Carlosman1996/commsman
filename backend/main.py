import json

from flask import Flask
from backend.repository.sqlite_repository import SQLiteRepository
from backend.core.backend_manager import BackendManager
from backend.api import register_routes
from utils.common import PROJECT_PATH


def create_app(database):
    app = Flask(__name__)

    repository_manager = SQLiteRepository()
    backend_manager = BackendManager(repository=repository_manager)

    register_routes(app, repository_manager, backend_manager)

    return app


if __name__ == "__main__":
    with open(f"{PROJECT_PATH}/config.json") as f:
        config_file = json.load(f)

    app = create_app(database=config_file["db"]["url"])
    app.run(debug=config_file["api"]["debug"], host=config_file["api"]["host"], port=config_file["api"]["port"])
