from PyQt6.QtCore import QObject, pyqtSignal


class ApiRequest(QObject):
    finished = pyqtSignal(object)  # Success response
    error = pyqtSignal(object)     # Error response

    def __init__(self, api_client, api_method, *args, **kwargs):
        super().__init__()
        self.api_client = api_client
        self.api_method = api_method
        self.args = args
        self.kwargs = kwargs

    def send(self):
        def callback(response):
            self.finished.emit(response)

        def error_handler(response):
            self.error.emit(response)

        getattr(self.api_client, self.api_method)(
            callback=callback,
            *self.args,
            **self.kwargs
        )

        # self.api_client._send_request(
        #     method=self.method,
        #     endpoint=self.endpoint,
        #     data=self.data,
        #     request_id=id(self),  # use id(self) as unique
        #     callback=callback,
        #     error_callback=error_handler
        # )
