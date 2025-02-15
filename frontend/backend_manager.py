from dataclasses import asdict

from PyQt6.QtCore import QThread, pyqtSignal


class BackendManager(QThread):

    signal_client_error = pyqtSignal(object)
    signal_request_progress = pyqtSignal(object)
    signal_requests_finished = pyqtSignal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def run(self):
        items = []

        def get_items(inspect_item):
            if inspect_item.hasChildren():
                for row in range(inspect_item.rowCount()):
                    child = inspect_item.child(row, 0)  # (row, column)
                    get_items(child)
            else:
                items.append(inspect_item)
        get_items(self.model.get_selected_item())

        for item in items:
            item.text()
            try:
                protocol_client = self.model.protocol_client_manager.get_handler(item=item)
                self.signal_client_error.emit("")
            except Exception as e:
                protocol_client = None
                self.signal_client_error.emit(f"Error while getting client: {e}")

            if protocol_client:
                protocol_client.connect()
                request_result = protocol_client.execute_request(**asdict(item.get_dataclass()))
            else:
                request_result = None

            self.model.update_specific_item(item=item, last_response=request_result)
            self.signal_request_progress.emit(request_result)

        self.model.protocol_client_manager.close_all_handlers()
        self.signal_requests_finished.emit()
