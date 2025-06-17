from flask import Blueprint, jsonify

from backend.core.backend_manager import BackendManager


bp = Blueprint("runner", __name__)
backend: BackendManager = None


def init_runner_routes(backend_manager):
    global backend
    backend = backend_manager


@bp.route("/runner/start/<int:item_id>", methods=["POST"])
def run_item(item_id):
    backend.start(item_id)
    return jsonify({"item_id": item_id, "running_threads": backend.get_running_threads()})


@bp.route("/runner/stop/<int:item_id>", methods=["POST"])
def stop_item(item_id):
    backend.stop(item_id)
    return jsonify({"item_id": item_id, "running_threads": backend.get_running_threads()})


@bp.route("/runner/running_threads", methods=["GET"])
def get_running_threads():
    return jsonify({"running_threads": backend.get_running_threads()})
