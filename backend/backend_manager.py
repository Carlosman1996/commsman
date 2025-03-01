import json
import time
from dataclasses import asdict

from PyQt6.QtCore import QThread, pyqtSignal

from backend.handlers.collection_handler import CollectionHandler
from backend.model import Model
from backend.models.base import BaseResult
from backend.models.collection import CollectionResult
from backend.protocol_client_manager import ProtocolClientManager


class BackendManager(QThread):

    signal_request_finished = pyqtSignal()
    signal_finish = pyqtSignal()

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.running = False
        self.collection_handler = CollectionHandler(self.model)
        self.protocol_client_manager = ProtocolClientManager(self.model)

        self.signal_finish.connect(self.stop)

    def run_requests(self, item, parent_result=None):
        # Stop signal:
        if not self.running:
            return

        start_time = time.time()
        request_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))

        if item.item_type == "Collection":
            collection_result = CollectionResult(name=item.name,
                                                 result="OK",
                                                 elapsed_time=0,
                                                 timestamp=request_timestamp)

            # Update item on model:
            self.model.add_item(collection_result)
            self.model.update_item(item_uuid=item.uuid, last_result=collection_result.uuid)

            if parent_result:
                self.collection_handler.add_collection(parent_result, collection_result)

            for item_child_uuid in item.children:
                item_child = self.model.get_item(item_child_uuid)
                self.run_requests(item_child, collection_result)

        else:
            time.sleep(item.run_options.polling_interval)

            # Set Running status:
            request_result = BaseResult(name=item.name,
                                        item_type="Modbus",
                                        result="Pending",
                                        elapsed_time=0,
                                        timestamp=request_timestamp)
            request_result_uuid = request_result.uuid

            # Update item on model:
            self.model.add_item(request_result)
            self.model.update_item(item_uuid=item.uuid, last_result=request_result_uuid)

            # Update collection:
            if parent_result:
                self.collection_handler.add_request(parent_result, request_result)

            # Update view:
            self.signal_request_finished.emit()

            # Do request:
            try:
                protocol_client = self.protocol_client_manager.get_handler(item=item)
                protocol_client.connect()
                request_result = protocol_client.execute_request(**asdict(item))
            except Exception as e:
                request_result = BaseResult(name=item.name,
                                            item_type="Modbus",
                                            result="Failed",
                                            elapsed_time=0,
                                            timestamp=request_timestamp,
                                            error_message=f"Error while getting client: {e}")
            request_result.uuid = request_result_uuid

            # Update item on model:
            self.model.update_item(item_uuid=request_result_uuid, **asdict(request_result))

            # Update collection:
            if parent_result:
                self.collection_handler.update_request(parent_result, request_result)

        # Update view:
        self.signal_request_finished.emit()

    def run(self):
        self.running = True

        selected_item = self.model.get_selected_item()

        # Initialize Collection:
        self.model.update_item(item_uuid=selected_item.uuid, last_result=None)
        self.signal_request_finished.emit()

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
    model_obj = Model()
    model_obj.load_from_json()
    backend_manager_obj = BackendManager(model_obj)
    model_obj.set_selected_item("uuid_1e65f48c-dcef-4def-b0c4-7dc3c129ffb0")
    backend_manager_obj.run()

    with open(model_obj.json_file_path_save, 'r') as file:
        data = json.load(file)
        json_str = json.dumps(data, indent=4)
        print(json_str)
