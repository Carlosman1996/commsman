import time
from dataclasses import asdict
from datetime import datetime

from backend._old_models.base import BaseResult
from backend._old_models.collection import CollectionResult


class CollectionHandler:
    """Handles execution and real-time updates of requests and collections."""
    def __init__(self, model):
        self.model = model

    def add_request(self, collection: CollectionResult, request: BaseResult):
        """Add a request to a collection and update its status."""
        collection.children.append(request.uuid)  # Add to the children list
        self.model.update_item(item_uuid=request.uuid, parent=collection.uuid)
        self.model.update_item(item_uuid=collection.uuid, children=collection.children)
        self.update_status(collection)

    def update_request(self, collection: CollectionResult, request: BaseResult):
        """Add a request to a collection and update its status."""
        collection.children[-1] = request.uuid  # Add to the children list
        self.model.update_item(item_uuid=request.uuid, parent=collection.uuid)
        self.model.update_item(item_uuid=collection.uuid, children=collection.children)
        self.update_status(collection)

    def add_collection(self, parent: CollectionResult, collection: CollectionResult):
        """Add a collection and update its status."""
        parent.children.append(collection.uuid)  # Add to the children list
        self.model.update_item(item_uuid=collection.uuid, parent=parent.uuid)
        self.model.update_item(item_uuid=parent.uuid, children=parent.children)
        self.update_status(parent)

    def count_results(self, collection: CollectionResult):
        """Count OK, Failed, and Pending requests in a collection and its collections."""
        total_ok = 0
        total_failed = 0
        total_pending = 0

        for child_uuid in collection.children:
            child = self.model.get_item(child_uuid)

            if child.item_handler == "Collection":
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

    def update_status(self, collection: CollectionResult):
        """Update collection status based on its requests and collections."""
        collection.total_ok, collection.total_failed, collection.total_pending = self.count_results(collection)

        if collection.total_pending > 0:
            collection.result = "Running"
        elif collection.total_failed > 0:
            collection.result = "Failed"
        else:
            collection.result = "OK"

        # Calculate elapsed time
        collection.elapsed_time = time.time() - datetime.strptime(collection.timestamp, "%Y-%m-%d %H:%M:%S").timestamp()

        # Update repository
        self.model.replace_item(item_uuid=collection.uuid, new_item=collection)

        # Propagate status update to parent
        if collection.parent:
            collection_parent = self.model.get_item(collection.parent)
            self.update_status(collection_parent)
