import copy
import time
from dataclasses import asdict

from PyQt6.QtCore import QThread, pyqtSignal, QTimer

from backend.handlers.collection_handler import CollectionHandler
from backend.repository import *
from backend.handlers.protocol_client_manager import ProtocolClientManager
from backend.repository.sqlite_repository import SQLiteRepository


class BackendManager(QThread):

    signal_request_finished = pyqtSignal(object)
    signal_finish = pyqtSignal()

    def __init__(self, repository: BaseRepository = None):
        super().__init__()
        if repository:
            self.repository = repository
        else:
            self.repository = SQLiteRepository()
        self.running = False
        self.collection_handler = CollectionHandler(self.repository)
        self.protocol_client_manager = ProtocolClientManager(self.repository)

        self.signal_finish.connect(self.stop)

    def run_requests(self, item, parent_result_item=None, main_parent_result_item=None):
        # Stop signal:
        if not self.running:
            return

        if item.item_handler == "Collection":
            result = self.collection_handler.get_collection_result(item=item,
                                                                   parent_id=getattr(parent_result_item, "item_id", None))
            # Update item on repository:
            self.repository.add_item_from_dataclass(result)

            # Update collections tree:
            if parent_result_item:
                self.collection_handler.add_collection(parent_result_item, result)

        else:
            # Get client:
            protocol_client = self.protocol_client_manager.get_client_handler(item=item)

            # Error
            if isinstance(protocol_client, str):
                error_message = f"Error while doing request: {protocol_client}"
                result = self.protocol_client_manager.get_request_failed_result(item=item,
                                                                                parent_id=getattr(parent_result_item, "item_id", None),
                                                                                error_message=error_message)
            # Do request:
            else:
                protocol_client.connect()
                result = protocol_client.execute_request(**asdict(item), parent_result_id=getattr(parent_result_item, "item_id", None))

            # Update item on repository:
            self.repository.add_item_from_dataclass(item=result)

            # Update collections tree:
            if parent_result_item:
                self.collection_handler.add_request(parent_result_item, result)

            # Wait polling interval:
            time.sleep(item.run_options.polling_interval)

        # Update view:
        if not main_parent_result_item:
            main_parent_result_item = result
        self.signal_request_finished.emit(main_parent_result_item)

        # Iterate over children in case of collections:
        if item.item_handler == "Collection":
            for item_child in item.children:
                self.run_requests(item_child, result, main_parent_result_item)

        return result

    def run(self):
        self.running = True

        selected_item = self.repository.get_selected_item()
        self.signal_request_finished.emit(None)

        # Get requests tree:
        requests_tree = self.repository.get_items_request_tree(selected_item)[0]

        # Delayed start:
        time.sleep(selected_item.run_options.delayed_start)

        result = self.run_requests(requests_tree)

        self.protocol_client_manager.close_all_handlers()

        # Update view:
        self.signal_request_finished.emit(result)
        self.signal_finish.emit()
        self.running = False

    def stop(self):
        self.running = False


if __name__ == "__main__":
    backend_manager_obj = BackendManager()
    backend_manager_obj.repository.set_selected_item({"item_id": 1, "item_handler": "Collection"})
    backend_manager_obj.run()
