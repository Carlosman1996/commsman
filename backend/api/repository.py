from flask import Blueprint, request

from backend.api.utils import make_response
from backend.repository.base_repository import BaseRepository


bp = Blueprint("repository", __name__)
repository: BaseRepository = None


def init_repository_routes(repository_manager):
    global repository
    repository = repository_manager


@bp.route('/items/request', methods=['POST'])
def create_item_request_from_handler():
    data = request.json
    try:
        item_name = data['item_name']
        item_handler = data['item_handler']
        parent = data.get('parent')
        result = repository.create_item_request_from_handler(item_name, item_handler, parent)
        return make_response(result), 201
    except KeyError as e:
        return make_response({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        return make_response({'error': str(e)}), 500


@bp.route('/items/client', methods=['POST'])
def create_client_item():
    data = request.json
    try:
        item_name = data['item_name']
        item_handler = data['item_handler']
        parent_item_id = data['parent_item_id']
        result = repository.create_client_item(item_name, item_handler, parent_item_id)
        return make_response(result), 201
    except KeyError as e:
        return make_response({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        return make_response({'error': str(e)}), 500


@bp.route('/items/run_options', methods=['POST'])
def create_run_options_item():
    data = request.json
    try:
        item_name = data['item_name']
        item_handler = data['item_handler']
        parent_item_id = data['parent_item_id']
        result = repository.create_run_options_item(item_name, item_handler, parent_item_id)
        return make_response(result), 201
    except KeyError as e:
        return make_response({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        return make_response({'error': str(e)}), 500


@bp.route('/items/<int:item_id>/request', methods=['GET'])
def get_item_request(item_id):
    try:
        item = repository.get_item_request(item_id)
        if item is None:
            return make_response({'error': 'Item not found'}), 404
        return make_response(item), 200
    except Exception as e:
        return make_response({'error': str(e)}), 500


@bp.route('/items/<int:item_id>/last_result_tree', methods=['GET'])
def get_item_last_result_tree(item_id):
    try:
        result = repository.get_item_last_result_tree(item_id)
        return make_response(result), 200
    except Exception as e:
        return make_response({'error': str(e)}), 500


@bp.route('/items/request_tree', methods=['GET'])
def get_items_request_tree():
    try:
        result = repository.get_items_request_tree()
        print(result[0].children)
        return make_response(result), 200
    except Exception as e:
        return make_response({'error': str(e)}), 500

@bp.route('/items/<int:item_id>', methods=['PUT'])
def update_item_from_handler(item_id):
    data = request.json
    try:
        item_handler = data['item_handler']
        kwargs = data.get('kwargs', {})
        repository.update_item_from_handler(item_id, item_handler, **kwargs)
        return make_response({'message': 'Item updated successfully'}), 200
    except KeyError as e:
        return make_response({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        return make_response({'error': str(e)}), 500


@bp.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    try:
        repository.delete_item(item_id)
        return make_response({'message': 'Item deleted successfully'}), 200
    except Exception as e:
        return make_response({'error': str(e)}), 500
