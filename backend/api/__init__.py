from backend.api.runner import bp as runner_bp, init_runner_routes
from backend.api.repository import bp as repository_bp, init_repository_routes


def register_routes(app, repository_manager, backend_manager):
    init_runner_routes(backend_manager)
    init_repository_routes(repository_manager)

    app.register_blueprint(runner_bp)
    app.register_blueprint(repository_bp)
