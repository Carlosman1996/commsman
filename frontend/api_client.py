from PyQt6.QtCore import QObject, pyqtSignal, QUrl, QByteArray
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import json
from typing import Optional, Dict, Any, Union, Callable

from utils.logger import CustomLogger


class ApiClient(QObject):
    """
    API Client for interacting with the repository backend
    """
    dispatch_to_main = pyqtSignal(object, object)
    response_received = pyqtSignal(object, int)  # Signal for successful responses
    error_occurred = pyqtSignal(dict, int)  # Signal for errors (message, status_code)

    def __init__(self, host: str, port: int):
        super().__init__()

        self.logger = CustomLogger(name=__name__)

        self.base_url = f"http://{host}:{port}"
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self._handle_response)
        self._callbacks = {}  # Maps QNetworkReply to user callback

    def _parse_response(self, reply: QNetworkReply) -> object:
        """Convert QNetworkReply to Python dict or list"""
        status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) or 500
        content_type = reply.header(QNetworkRequest.KnownHeaders.ContentTypeHeader) or ""

        response_data = None
        try:
            response_data = bytes(reply.readAll()).decode('utf-8')

            if not response_data.strip():
                return {"message": "Empty response", "status": status_code}

            if "application/json" in content_type:
                parsed = json.loads(response_data)
                return {"response": parsed, "status": status_code}

            return {"response": response_data, "status": status_code}

        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON response",
                "response": response_data,
                "status": status_code
            }
        except Exception as e:
            return {
                "error": f"Response parsing failed: {str(e)}",
                "response": None,
                "status": status_code
            }

    def _handle_response(self, reply: QNetworkReply):
        """Handle API responses of any type"""
        callback = None
        try:
            response_data = self._parse_response(reply)
            callback = self._callbacks.pop(reply, None)
            status_code = response_data.get("status", 500) if isinstance(response_data, dict) else 200

            self.logger.debug(f"Response received: {status_code} {response_data}. Callback: {callback}")

            if reply.error() == QNetworkReply.NetworkError.NoError:
                if callback:
                    self.dispatch_to_main.emit(callback, response_data["response"])
                else:
                    # Emit the raw parsed data (could be dict or list)
                    self.response_received.emit(response_data, status_code)
            else:
                error_data = {
                    "error": reply.errorString(),
                    "details": response_data if isinstance(response_data, dict) else {"response": response_data},
                    "status": status_code
                }
                self.logger.error(str(error_data))
                self.error_occurred.emit(error_data, status_code)

        except Exception as e:
            if not callback:
                error_data = {
                    "error": f"Unexpected error processing response: {str(e)}",
                    "status": 500
                }
                self.logger.error(str(error_data))
                self.error_occurred.emit(error_data, 500)
            else:
                raise Exception(e)
        finally:
            reply.deleteLater()

    def _send_request(self, method: str, endpoint: str, data: Optional[Dict] = None, callback: Callable = None) -> QNetworkReply:
        """Generic request sender that returns the QNetworkReply"""
        url = QUrl(f"{self.base_url}/{endpoint}")
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

        reply = None
        if data is not None:
            json_data = json.dumps(data).encode('utf-8')
            if method == "POST":
                reply = self.network_manager.post(request, QByteArray(json_data))
            elif method == "PUT":
                reply = self.network_manager.put(request, QByteArray(json_data))
        elif method == "GET":
            reply = self.network_manager.get(request)
        elif method == "DELETE":
            reply = self.network_manager.deleteResource(request)
        else:
            raise ValueError(f"Unsupported method: {method}")

        self._callbacks[reply] = callback
        return reply

    # Repository methods matching your Flask routes

    def create_item_request_from_handler(self, item_name: str, item_handler: str, parent_item_id: int | None, callback: Callable = None):
        """POST /items/request"""
        data = {
            "item_name": item_name,
            "item_handler": item_handler,
            "parent_item_id": parent_item_id
        }
        self._send_request("POST", "items/request", data, callback=callback)

    def create_client_item(self, item_name: str, item_handler: str, parent_item_id: int, callback: Callable = None):
        """POST /items/client"""
        data = {
            "item_name": item_name,
            "item_handler": item_handler,
            "parent_item_id": parent_item_id
        }
        self._send_request("POST", "items/client", data, callback=callback)

    def create_run_options_item(self, item_name: str, item_handler: str, parent_item_id: int, callback: Callable = None):
        """POST /items/run_options"""
        data = {
            "item_name": item_name,
            "item_handler": item_handler,
            "parent_item_id": parent_item_id
        }
        self._send_request("POST", "items/run_options", data, callback=callback)

    def get_item_request(self, item_id: int, callback: Callable = None):
        """GET /items/<item_id>/request"""
        self._send_request("GET", f"items/{item_id}/request", callback=callback)

    def get_item_last_result_tree(self, item_id: int, callback: Callable = None):
        """GET /items/<item_id>/last_result_tree"""
        self._send_request("GET", f"items/{item_id}/last_result_tree", callback=callback)

    def get_item_results_history(self, item_id: int, callback: Callable = None):
        """GET /items/<item_id>/results_history"""
        self._send_request("GET", f"items/{item_id}/results_history", callback=callback)

    def get_items_request_tree(self, callback: Callable = None):
        """GET /items/<item_id>/request_tree"""
        self._send_request("GET", f"items/request_tree", callback=callback)

    def update_item_from_handler(self, item_id: int, item_handler: str, callback: Callable = None, **kwargs):
        """PUT /items/<item_id>"""
        data = {
            "item_handler": item_handler,
            "kwargs": kwargs
        }
        self._send_request("PUT", f"items/{item_id}", data, callback=callback)

    def delete_item(self, item_id: int, callback: Callable = None):
        """DELETE /items/<item_id>"""
        self._send_request("DELETE", f"items/{item_id}", callback=callback)

    def run_item(self, item_id: int, callback: Callable = None):
        """PUT /runner/start/<int:item_id>"""
        self._send_request("PUT", f"runner/start/{item_id}", data={}, callback=callback)

    def stop_item(self, item_id: int, callback: Callable = None):
        """PUT /runner/stop/<int:item_id>"""
        self._send_request("PUT", f"runner/stop/{item_id}", data={}, callback=callback)

    def get_running_threads(self, callback: Callable = None):
        """GET /runner/running_threads"""
        self._send_request("GET", f"runner/running_threads", callback=callback)
