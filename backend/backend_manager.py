import time
from dataclasses import asdict

from PyQt6.QtCore import QThread, pyqtSignal

from backend.collection_handler import CollectionHandler
from frontend.models.base import BaseResult
from frontend.models.collection import CollectionResult


class BackendManager(QThread):

    signal_request_finished = pyqtSignal()
    signal_finish = pyqtSignal()

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.running = False
        self.collection_handler = None

        self.signal_finish.connect(self.stop)

    def get_run_items(self, item) -> list:
        collection = []

        if item.hasChildren():
            children = []
            for row in range(item.rowCount()):
                child = item.child(row, 0)  # (row, column)
                children.extend(self.get_run_items(child))
            collection.append({
                "item": item,
                "children": children
            })
        else:
            collection.append({
                "item": item
            })
        return collection

    def run_requests(self, selected_item, run_items_tree, parent=None):
        if run_items_tree is None:
            return

        for item_dict in run_items_tree:
            # Stop signal:
            if not self.running:
                break

            item = item_dict["item"]

            start_time = time.time()
            request_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))

            if item.item_type == "Collection":
                children = item_dict.get("children")

                collection_result = CollectionResult(name=item.name,
                                                     timestamp=request_timestamp)
                if parent:
                    self.collection_handler.add_collection(parent, collection_result)

                self.model.update_specific_item(item=item, last_response=collection_result)

                self.run_requests(selected_item, children, collection_result)

            else:
                # Set Running status:
                request_result = BaseResult(name=item.name, item_type=item.item_type, result="Next", elapsed_time=0, timestamp=request_timestamp)

                # Update collection:
                if parent:
                    self.collection_handler.add_request(parent, request_result)

                self.signal_request_finished.emit()

                # Polling interval:
                time.sleep(selected_item.run_options.polling_interval)

                # Do request:
                try:
                    protocol_client = self.model.protocol_client_manager.get_handler(item=item)
                    protocol_client.connect()
                    request_result = protocol_client.execute_request(**asdict(item.get_dataclass()))
                except Exception as e:
                    request_result = BaseResult(name=item.name, item_type=item.item_type, result="Failed", elapsed_time=0, timestamp=request_timestamp, error_message=f"Error while getting client: {e}")

                # Update item on model:
                self.model.update_specific_item(item=item, last_response=request_result)

                # Update collection:
                if parent:
                    self.collection_handler.update_request(parent, request_result)

            # Update view:
            self.signal_request_finished.emit()

    def run(self):
        self.running = True
        self.collection_handler = CollectionHandler(self.model)

        # TODO: include in backend refactor
        # selected_item = copy.deepcopy(self.model.get_selected_item())
        selected_item = self.model.get_selected_item()
        run_items_tree = self.get_run_items(selected_item)

        # Initialize Collection:
        if selected_item.item_type == "Collection":
            self.model.update_specific_item(item=selected_item,
                                            last_response=CollectionResult(name=selected_item.name, result="Running"))
            self.signal_request_finished.emit()

        # Delayed start:
        delayed_start = selected_item.run_options.delayed_start - selected_item.run_options.polling_interval
        time.sleep(delayed_start if delayed_start > 0 else 0)

        self.run_requests(selected_item, run_items_tree)

        self.model.protocol_client_manager.close_all_handlers()
        self.signal_finish.emit()
        self.running = False

    def stop(self):
        self.running = False
