import time
from dataclasses import asdict

from PyQt6.QtCore import QThread, pyqtSignal

from backend.handlers.collection_handler import CollectionHandler
from backend.repository import *
from backend.handlers.protocol_client_manager import ProtocolClientManager
from backend.repository.sqlite_repository import SQLiteRepository


class BackendManager(QThread):

    signal_request_finished = pyqtSignal()
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

    def run_requests(self, item, parent_result_item=None):
        # Stop signal:
        if not self.running:
            return

        if item.item_type == "Collection":
            collection_result = self.collection_handler.get_collection_result(item=item,
                                                                              parent_id=getattr(parent_result_item, "id", None))

            # Update item on repository:
            self.repository.create_item_from_dataclass(collection_result)

            if parent_result_item:
                self.collection_handler.add_collection(parent_result_item, collection_result)

            for item_child_uuid in item.children:
                item_child = self.repository.get_item(item_child_uuid)
                self.run_requests(item_child, collection_result)

        else:
            # Get client:
            protocol_client = self.protocol_client_manager.get_client_handler(item=item)

            # Error
            if isinstance(protocol_client, str):
                error_message = f"Error while doing request: {protocol_client}"
                request_result = self.protocol_client_manager.get_request_failed_result(item=item,
                                                                                        parent_id=getattr(parent_result_item, "id", None),
                                                                                        error_message=error_message)
            # Do request:
            else:
                protocol_client.connect()
                request_result = protocol_client.execute_request(**asdict(item), parent_result_id=getattr(parent_result_item, "id", None))

            # Update item on repository:
            self.repository.create_item_from_dataclass(item=request_result)

            # Update collection:
            if parent_result_item:
                self.collection_handler.add_request(parent_result_item, request_result)

            # Update collection:
            if parent_result_item:
                self.collection_handler.update_request(parent_result_item, request_result)

            # Wait polling interval:
            time.sleep(item.run_options.polling_interval)

        # Update view:
        self.signal_request_finished.emit()

    def run(self):
        self.running = True

        selected_item = self.repository.get_selected_item()

        # Delayed start:
        time.sleep(selected_item.run_options.delayed_start)

        self.run_requests(selected_item)

        self.protocol_client_manager.close_all_handlers()

        # Update view:
        self.signal_request_finished.emit()
        self.signal_finish.emit()
        self.running = False

    def stop(self):
        self.running = False


if __name__ == "__main__":
    backend_manager_obj = BackendManager()
    backend_manager_obj.repository.set_selected_item({"item_id": 7, "item_handler": "ModbusRequest"})
    backend_manager_obj.run()
