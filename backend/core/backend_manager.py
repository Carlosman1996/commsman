import threading

from backend.core.background_task_manager import BackgroundTaskManager
from backend.repository import BaseRepository
from backend.repository.sqlite_repository import SQLiteRepository
from backend.core.runner import Runner


class BackendManager:
    """ Manages multiple backend worker threads """

    def __init__(self, repository: BaseRepository = None):
        super().__init__()
        self.repository = repository if repository else SQLiteRepository()
        self.running_threads = {}  # Track active threads
        self.running = False

        # Setup background task manager:
        self.background_task_manager = BackgroundTaskManager()
        self.background_task_manager.add_periodic_task(self.repository.delete_old_results, 600)
        self.background_task_manager.start()

    @property
    def running(self):
        return bool(self.get_running_threads())

    def get_running_threads(self):
        running_threads = {}
        for item, value in self.running_threads.items():
            if value.is_alive():
                running_threads[item] = value
        self.running_threads = running_threads
        return list(self.running_threads.keys())

    def start(self, item_id):
        """ Starts a new thread for a given item_id """
        if item_id in self.running_threads:
            raise ValueError(f"Item ID {item_id} is already running.")

        print(f"Starting process for Item ID {item_id}")

        thread = Runner(repository=self.repository, item_id=item_id, daemon=True)

        self.running_threads[item_id] = thread
        thread.start()

    def stop(self, item_id):
        """Stops a specific worker thread gracefully."""
        def stop_thread(item_id):
            self.running_threads[item_id].stop()  # Set running flag to False
            self.running_threads[item_id].join()  # Wait for completion
            self._remove_thread(item_id)
            print(f"Stopped process for Item ID {item_id}")

        if item_id in self.running_threads:
            stop_thread(item_id)
        if item_id == 0:
            items_id = list(self.running_threads.keys())
            [stop_thread(item_id) for item_id in items_id]

    def _remove_thread(self, item_id):
        """Removes the finished thread from the tracking dictionary."""
        if item_id in self.running_threads:
            self.running_threads.pop(item_id)

    @running.setter
    def running(self, value):
        self._running = value


if __name__ == "__main__":
    backend_manager = BackendManager()
    backend_manager.repository.set_selected_item(item_id=1)
    backend_manager.start(item_id=1)  # Start first request
    # backend_manager.start(item_id=2)  # Start another request (independent)
