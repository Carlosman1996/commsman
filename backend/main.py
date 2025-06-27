from flask import Flask
from backend.repository.sqlite_repository import SQLiteRepository
from backend.core.backend_manager import BackendManager
from backend.api import register_routes


def create_app():
    app = Flask(__name__)

    repository_manager = SQLiteRepository()
    backend_manager = BackendManager(repository=repository_manager)

    register_routes(app, repository_manager, backend_manager)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
