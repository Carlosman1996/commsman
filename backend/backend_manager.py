import sys
from functools import partial

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

from backend.background_task_manager import BackgroundTaskManager
from backend.repository import BaseRepository
from backend.repository.sqlite_repository import SQLiteRepository
from backend.runner import Runner


class BackendManager(QObject):
    """ Manages multiple backend worker threads """

    signal_request_finished = pyqtSignal(int, object)  # Signal emitted when request finishes
    signal_finish = pyqtSignal()

    def __init__(self, repository: BaseRepository = None):
        super().__init__()
        self.repository = repository if repository else SQLiteRepository()
        self.running_threads = {}  # Track active threads

        # Setup background task manager:
        self.background_task_manager = BackgroundTaskManager()
        self.background_task_manager.add_periodic_task(self.repository.delete_old_results, 600)
        self.background_task_manager.start()

    def start(self, item_id):
        """ Starts a new thread for a given item_id """
        if item_id in self.running_threads:
            raise ValueError(f"Item ID {item_id} is already running.")

        print(f"Starting process for Item ID {item_id}")

        thread = Runner(repository=self.repository, item_id=item_id)
        thread.finished.connect(lambda: self.remove_thread(item_id))
        thread.signal_request_finished.connect(self.signal_request_finished.emit)  # Propagate to UI
        self.running_threads[item_id] = thread
        thread.start()

    def stop(self, item_id):
        """Stops a specific worker thread gracefully."""
        def stop_thread(item_id):
            self.running_threads[item_id].stop()  # Set running flag to False
            self.running_threads[item_id].wait()  # Wait for completion
            self.remove_thread(item_id)
            print(f"Stopped process for Item ID {item_id}")

        if item_id in self.running_threads:
            stop_thread(item_id)
        if item_id == 0:
            items_id = list(self.running_threads.keys())
            [stop_thread(item_id) for item_id in items_id]

    def remove_thread(self, item_id):
        """Removes the finished thread from the tracking dictionary."""
        if item_id in self.running_threads:
            self.running_threads.pop(item_id)
        self.signal_finish.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)  # ✅ Create QApplication before using QThread

    backend_manager = BackendManager()
    backend_manager.repository.set_selected_item(item_id=1)
    backend_manager.start(item_id=1)  # Start first request
    backend_manager.start(item_id=2)  # Start another request (independent)

    sys.exit(app.exec())  # ✅ Ensures Qt event loop runs
