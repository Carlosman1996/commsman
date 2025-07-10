import uuid
import weakref

from frontend.api.api_request import ApiRequest


class ApiCallMixin:
    """
    Mixin to generically handle API calls for any QWidget/subclass.
    self.api_client should be set in your __init__.
    """

    def setup_api_client(self, api_client):
        self.request_id = str(uuid.uuid4())
        self.api_client = api_client
        self._api_requests = []
        # self.api_client.dispatch_to_main.connect(self._on_dispatch_to_main)
        # self._self_weak = weakref.ref(self)

    def call_api(self, api_method, callback, error_callback=None, *args, **kwargs):
        request = ApiRequest(self.api_client, api_method, *args, **kwargs)
        request.finished.connect(callback)
        if error_callback:
            request.error.connect(error_callback)

        self._api_requests.append(request)
        request.send()

    def closeEvent(self, event):
        self._api_requests.clear()
        super().closeEvent(event)

    # def _on_dispatch_to_main(self, request_id, callback, data):
    #     """
    #     Ensures callback only runs if self is still alive (widget not deleted).
    #     Typical pattern for UI-thread safe updates in Qt threads.
    #     """
    #
    #     print(request_id, self.request_id, callback, data)
    #
    #     if request_id and request_id != self.request_id:
    #         return  # Not for this view
    #
    #     print("_on_dispatch_to_main")
    #     self_obj = self._self_weak()
    #     if self_obj is not None and callable(callback):
    #         callback(data)
    #     else:
    #         if hasattr(self, "_logger"):
    #             self._logger.debug(f"Ignore callback {callback} for {self_obj} because it is not alive anymore.")

    # def closeEvent(self, event):
    #     if hasattr(self, "timer"):
    #         self.timer.stop()
    #
    #     try:
    #         self.api_client.dispatch_to_main.disconnect(self._on_dispatch_to_main)
    #     except TypeError:
    #         pass
    #
    #     super().closeEvent(event)
