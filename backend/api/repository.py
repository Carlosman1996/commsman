from flask import Blueprint, jsonify

from backend.repository.base_repository import BaseRepository


bp = Blueprint("repository", __name__)
repository: BaseRepository = None


def init_repository_routes(repository_manager):
    global repository
    repository = repository_manager
