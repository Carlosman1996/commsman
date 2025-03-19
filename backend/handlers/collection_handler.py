import time
from datetime import timezone, datetime

from backend.models import BaseResult, Collection, CollectionResult


class CollectionHandler:
    """Handles execution and real-time updates of requests and collections."""
    def __init__(self, repository):
        self.repository = repository

    @staticmethod
    def get_collection_result(item: Collection, parent_id: int) -> CollectionResult:
        return CollectionResult(
            name=item.name,
            client_type=item.client_type,
            request_id=item.item_id,
            parent_id=parent_id,
            result="OK",
            elapsed_time=0,
            timestamp=datetime.now(timezone.utc),
            error_message=""
        )

    def count_results(self, collection_result: CollectionResult):
        """Count OK, Failed, and Pending requests in a collection and its collections."""
        total_ok = 0
        total_failed = 0
        total_pending = 0

        if collection_result.children:
            children = collection_result.children
        else:
            children = []

        for item_child in children:
            child = self.repository.get_item_result(**item_child)

            if child.item_handler == "CollectionResult":
                # Recursively count results for sub-collections
                ok, failed, pending = self.count_results(child)
                total_ok += ok
                total_failed += failed
                total_pending += pending
            else:
                # Count results for requests
                if child.result == "OK":
                    total_ok += 1
                elif child.result == "Failed":
                    total_failed += 1
                elif child.result == "Pending":
                    total_pending += 1

        return total_ok, total_failed, total_pending

    def update_collection_result(self, collection_result: CollectionResult):
        """Update collection status based on its requests and collections."""
        collection_result.total_ok, collection_result.total_failed, collection_result.total_pending = self.count_results(collection_result)

        if collection_result.total_pending > 0:
            collection_result.result = "Running"
        elif collection_result.total_failed > 0:
            collection_result.result = "Failed"
        else:
            collection_result.result = "OK"

        # Calculate elapsed time
        collection_result.elapsed_time = (datetime.now(timezone.utc) - datetime.fromisoformat(collection_result.timestamp)).total_seconds()

        # Update repository
        self.repository.create_item_from_dataclass(item=collection_result)

        # Propagate status update to parent
        if collection_result.parent_id:
            collection_parent = self.repository.get_item_result(item_handler="CollectionResult", item_id=collection_result.parent_id)
            self.update_collection_result(collection_parent)
