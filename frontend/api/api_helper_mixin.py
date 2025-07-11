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
        self._self_weak = weakref.ref(self)  # Allows checking if view is alive

    def call_api(self, api_method, callback=None, error_callback=None, *args, **kwargs):
        request = ApiRequest(self.api_client, api_method, *args, **kwargs)

        # Wrap the real callbacks to ensure the view is still alive
        def safe_callback(result):
            self_ref = self._self_weak()
            if self_ref:
                callback(result)

        def safe_error_callback(error):
            self_ref = self._self_weak()
            if self_ref and error_callback:
                error_callback(error)

        if callback:
            request.finished.connect(safe_callback)
        if error_callback:
            request.error.connect(safe_error_callback)

        self._api_requests.append(request)
        request.send()

    def closeEvent(self, event):
        self._api_requests.clear()
        super().closeEvent(event)
