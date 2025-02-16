import time
from dataclasses import asdict

from PyQt6.QtCore import QThread, pyqtSignal


class BackendManager(QThread):

    signal_client_error = pyqtSignal(object)
    signal_request_finished = pyqtSignal(object)
    signal_finish = pyqtSignal()

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.running = False

        self.signal_finish.connect(self.stop)

    def run(self):
        self.running = True
        items = []
        request_item = self.model.get_selected_item()

        def get_items(inspect_item):
            if inspect_item.hasChildren():
                for row in range(inspect_item.rowCount()):
                    child = inspect_item.child(row, 0)  # (row, column)
                    get_items(child)
            else:
                items.append(inspect_item)
        get_items(request_item)

        # Delayed start:
        time.sleep(request_item.run_options.delayed_start)

        for item in items:

            # Stop signal:
            if not self.running:
                break

            try:
                protocol_client = self.model.protocol_client_manager.get_handler(item=item)
                self.signal_client_error.emit("")
            except Exception as e:
                protocol_client = None

                # Update only item displayed:
                if item == self.model.get_selected_item():
                    self.signal_client_error.emit(f"Error while getting client: {e}")

            if protocol_client:
                protocol_client.connect()
                request_result = protocol_client.execute_request(**asdict(item.get_dataclass()))
            else:
                request_result = None

            self.model.update_specific_item(item=item, last_response=request_result)

            # Update only item displayed:
            if item == self.model.get_selected_item():
                self.signal_request_finished.emit(request_result)

            # Polling interval:
            time.sleep(request_item.run_options.polling_interval)

        self.model.protocol_client_manager.close_all_handlers()
        self.signal_finish.emit()
        self.running = False

    def stop(self):
        self.running = False
