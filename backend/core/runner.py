import threading
import time
from dataclasses import asdict
from datetime import datetime

import tzlocal
from PyQt6.QtCore import QThread
from backend.core.handlers.collection_handler import CollectionHandler
from backend.models.execution_session import ExecutionSession
from backend.repository import *
from backend.core.handlers.protocol_client_manager import ProtocolClientManager
from backend.repository.sqlite_repository import SQLiteRepository


class Runner(threading.Thread):
    """ Worker that runs the requests in a separate Python thread """

    def __init__(self, repository: BaseRepository, item_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository = repository
        self.update_items_queue = []
        self.collection_handler = CollectionHandler(self.update_items_queue)
        self.protocol_client_manager = ProtocolClientManager(self.repository)
        self.running = True  # Control flag for stopping
        self.item = self.repository.get_item_request(item_id=item_id)
        self.execution_session = None

    def create_execution_session(self):
        self.execution_session = ExecutionSession(
            name=self.item.name,
            request_id=self.item.item_id,
            timestamp=datetime.now(tzlocal.get_localzone())
        )
        self.repository.add_item_from_dataclass(item=self.execution_session)

    def finish_execution_session(self):
        if self.execution_session.total_failed > 0:
            self.execution_session.result = "Failed"
        else:
            self.execution_session.result = "OK"
        self.repository.add_item_from_dataclass(item=self.execution_session)

    def run_requests(self, item, parent_result_item=None, main_result=None):
        """ Recursively processes requests """
        # Stop signal:
        if not self.running:
            return

        if item.item_handler == "Collection":
            result = self.collection_handler.get_collection_result(
                item=item,
                parent_id=getattr(parent_result_item, "item_id", None),
                execution_session_id=self.execution_session.item_id
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
                    execution_session_id = self.execution_session.item_id,
                    error_message=f"Error: {protocol_client}"
                )
            # Do request:
            else:
                protocol_client.connect()
                result = protocol_client.execute_request(
                    **asdict(item),
                    parent_result_id=getattr(parent_result_item, "item_id", None),
                    execution_session_id = self.execution_session.item_id,
                )

            # Update session:
            if result.result == "OK":
                self.execution_session.total_ok += 1
            else:
                self.execution_session.total_failed += 1

            # Update collections tree:
            if parent_result_item:
                self.collection_handler.add_request(parent_result_item, result)

            # Wait polling interval:
            if self.item.run_options.polling_interval < 0.1:
                time.sleep(0.1)
            else:
                time.sleep(self.item.run_options.polling_interval)

        # Update view:
        if not main_result:
            main_result = result

        # Update session:
        self.execution_session.elapsed_time = (datetime.now(tzlocal.get_localzone()) - self.execution_session.timestamp).total_seconds()

        # Save in database:
        self.update_items_queue.append(self.execution_session)
        self.update_items_queue.append(result)
        while self.update_items_queue:
            result = self.update_items_queue.pop(0)
            self.repository.add_item_from_dataclass(item=result)

        # Iterate over children in case of collections:
        if item.item_handler == "Collection":
            for child in item.children:
                self.run_requests(child, result, main_result)

    def run(self):
        """Main execution function."""
        self.create_execution_session()

        # Get requests tree:
        requests_tree = self.repository.get_items_request_tree(self.item)[0]

        time.sleep(self.item.run_options.delayed_start)

        if self.item.run_options.continuous_monitoring:
            while self.running:
                self.run_requests(item=requests_tree)
                self.execution_session.iterations += 1
        else:
            self.run_requests(item=requests_tree)
            self.execution_session.iterations += 1

        self.finish_execution_session()

        self.protocol_client_manager.close_all_handlers()

        return

    def stop(self):
        """Gracefully stop the thread."""
        self.running = False


if __name__ == "__main__":
    runner = Runner(repository=SQLiteRepository(), item_id=1)
    runner.run()
