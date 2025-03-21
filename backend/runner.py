import copy
import time
import threading
from dataclasses import asdict

from PyQt6.QtCore import QThread, pyqtSignal, QObject
from backend.handlers.collection_handler import CollectionHandler
from backend.repository import *
from backend.handlers.protocol_client_manager import ProtocolClientManager
from backend.repository.sqlite_repository import SQLiteRepository


class Runner(QThread):
    """ Worker that runs the requests in a separate Python thread inside a QThread """

    signal_request_finished = pyqtSignal(int, object)

    def __init__(self, repository, item_id):
        super().__init__()
        self.item_id = item_id
        self.repository = repository
        self.update_items_queue = []
        self.collection_handler = CollectionHandler(self.update_items_queue)
        self.protocol_client_manager = ProtocolClientManager(self.repository)
        self.running = True  # Control flag for stopping

    def run_requests(self, item, parent_result_item=None, main_result=None):
        """ Recursively processes requests """
        # Stop signal:
        if not self.running:
            return

        if item.item_handler == "Collection":
            result = self.collection_handler.get_collection_result(
                item=item,
                parent_id=getattr(parent_result_item, "item_id", None)
            )

            # Update collections tree:
            if parent_result_item:
                self.collection_handler.add_collection(parent_result_item, result)
        else:
            # Get client:
            protocol_client = self.protocol_client_manager.get_client_handler(item=item)

            # Error
            if isinstance(protocol_client, str):
                result = self.protocol_client_manager.get_request_failed_result(
                    item=item,
                    parent_id=getattr(parent_result_item, "item_id", None),
                    error_message=f"Error: {protocol_client}"
                )
            # Do request:
            else:
                protocol_client.connect()
                result = protocol_client.execute_request(
                    **asdict(item),
                    parent_result_id=getattr(parent_result_item, "item_id", None)
                )

            # Update collections tree:
            if parent_result_item:
                self.collection_handler.add_request(parent_result_item, result)

            # Wait polling interval:
            time.sleep(item.run_options.polling_interval)

        # Update view:
        if not main_result:
            main_result = result

        # Save in database:
        self.update_items_queue.append(result)
        while self.update_items_queue:
            result = self.update_items_queue.pop(0)
            self.signal_request_finished.emit(result.request_id, result)
            self.repository.add_item_from_dataclass(item=result)

        # Iterate over children in case of collections:
        if item.item_handler == "Collection":
            for child in item.children:
                self.run_requests(child, result, main_result)

        return main_result

    def run(self):
        """Main execution function."""
        selected_item = self.repository.get_selected_item()

        self.signal_request_finished.emit(selected_item.item_id, None)

        # Get requests tree:
        requests_tree = self.repository.get_items_request_tree(selected_item)[0]

        # Delayed start:
        time.sleep(selected_item.run_options.delayed_start)

        result = self.run_requests(item=requests_tree)

        self.protocol_client_manager.close_all_handlers()

        # Update view:
        self.signal_request_finished.emit(selected_item.item_id, result)

        return

    def stop(self):
        """Gracefully stop the thread."""
        self.running = False
