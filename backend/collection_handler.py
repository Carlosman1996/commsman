import time
from datetime import datetime

from frontend.models.base import BaseResult
from frontend.models.collection import CollectionResult


class CollectionHandler:
    """Handles execution and real-time updates of requests and collections."""
    def __init__(self, model):
        self.model = model

    def add_request(self, collection: CollectionResult, request: BaseResult):
        """Add a request to a collection and update its status."""
        collection.requests.append(request)
        self.update_status(collection)

    def add_collection(self, parent: CollectionResult, collection: CollectionResult):
        """Add a collection and update its status."""
        collection.parent = parent
        parent.collections.append(collection)
        self.update_status(parent)

    def count_results(self, collection: CollectionResult):
        """Count OK, Failed, and Pending requests in a collection and its collections."""
        total_ok = sum(1 for r in collection.requests if r.result == "Passed")
        total_failed = sum(1 for r in collection.requests if r.result == "Failed")
        total_pending = sum(1 for r in collection.requests if r.result == "Pending")

        for sub in collection.collections:
            ok, failed, pending = self.count_results(sub)
            total_ok += ok
            total_failed += failed
            total_pending += pending

        return total_ok, total_failed, total_pending

    def update_status(self, collection: CollectionResult):
        """Update collection status based on its requests and collections."""
        collection.total_ok, collection.total_failed, collection.total_pending = self.count_results(collection)

        if collection.total_pending > 0:
            collection.result = "Running"
        elif collection.total_failed > 0:
            collection.result = "Failed"
        else:
            collection.result = "Passed"

        collection.elapsed_time = time.time() - datetime.strptime(collection.timestamp, "%Y-%m-%d %H:%M:%S").timestamp()

        if collection.parent:
            self.update_status(collection.parent)
