import threading
import time
from typing import Callable, List


class BackgroundTaskManager:
    """Manages background tasks that can be executed periodically or once."""

    def __init__(self):
        self._tasks = []  # List to hold the tasks
        self._task_threads = []  # Keep track of task threads
        self._stop_event = threading.Event()  # Stop flag for the manager

    def start(self):
        """Start executing the tasks."""
        self._stop_event.clear()
        self._run_tasks_in_background()

    def stop(self):
        """Stop the manager and all running tasks."""
        self._stop_event.set()
        for thread in self._task_threads:
            thread.join()

    def _run_tasks_in_background(self):
        """Runs tasks in separate threads."""
        for task in self._tasks:
            task_thread = threading.Thread(target=self._execute_task, args=(task,), daemon=True)
            self._task_threads.append(task_thread)
            task_thread.start()

    def _execute_task(self, task: Callable):
        """Executes a task callback."""
        try:
            task()  # Run the task
        except Exception as e:
            print(f"Error executing task: {e}")

    def add_task(self, task: Callable):
        """Add a task to be executed in the background."""
        self._tasks.append(task)

    def add_periodic_task(self, task: Callable, interval_seconds: int):
        """Add a periodic task that repeats every X seconds."""

        def periodic_task():
            while not self._stop_event.is_set():
                try:
                    task()
                except Exception as e:
                    print(f"Exception in background task {task}: {e}")
                time.sleep(interval_seconds)

        self.add_task(periodic_task)

    def remove_task(self, task: Callable):
        """Remove a specific task."""
        self._tasks.remove(task)
        # Stop the task thread if it's running
        for thread in self._task_threads:
            if thread.is_alive():
                thread.join()
        self._task_threads = [t for t in self._task_threads if t.is_alive()]
