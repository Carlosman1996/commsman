from flask import Blueprint

from backend.api.utils import make_response
from backend.core.backend_manager import BackendManager


bp = Blueprint("runner", __name__)
backend: BackendManager = None


def init_runner_routes(backend_manager):
    global backend
    backend = backend_manager


@bp.route("/ping", methods=["GET"])
def ping():
    return {"status": "ok"}, 200


@bp.route("/runner/start/<int:item_id>", methods=["PUT"])
def run_item(item_id):
    backend.start(item_id)
    return make_response({"item_id": item_id, "running_threads": backend.get_running_threads()})


@bp.route("/runner/stop/<int:item_id>", methods=["PUT"])
def stop_item(item_id):
    backend.stop(item_id)
    return make_response({"item_id": item_id, "running_threads": backend.get_running_threads()})


@bp.route("/runner/running_threads", methods=["GET"])
def get_running_threads():
    return make_response({"running_threads": backend.get_running_threads()})
