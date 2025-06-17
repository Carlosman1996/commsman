from dataclasses import asdict
from datetime import datetime

import tzlocal

from backend.core.handlers.base_handler import BaseHandler
from backend.core.handlers.custom_modbus_handler import CustomModbusTcpClient, CustomModbusRtuClient
from backend.models import BaseRequest, ModbusResponse


class ProtocolClientManager:
    def __init__(self, repository):
        self.repository = repository
        self.handlers: dict[str, BaseHandler] = {}  # Key: handler ID, Value: handler

    def get_client_handler(self, item: BaseRequest) -> BaseHandler | str:
        """Get or create a handler for the specified protocol."""

        def find_item_client(item, base_item):
            if item.client_type == "No connection":
                return "Current request does not have client"
            elif item.client_type == "Inherit from parent":
                parent = self.repository.get_item_request(item.parent_id)
                return find_item_client(parent, base_item)
            elif item.client:
                if item.client.item_type == base_item.item_type:
                    return item.client
                else:
                    return f"Current request client protocol is not correct: expected {base_item.item_type} - found {item.item_type}"
            else:
                return f"FATAL ERROR - Could not resolve item client: {item.client} - {item}"

        item_client = find_item_client(item=item, base_item=item)

        # Client not found:
        if isinstance(item_client, str):
            return item_client

        client_data = asdict(item_client)

        handler_id = self._generate_handler_id(**client_data)
        if handler_id not in self.handlers:
            if item_client.item_handler == "ModbusTcpClient":
                self.handlers[handler_id] = CustomModbusTcpClient(**client_data)
            elif item_client.item_handler == "ModbusRtuClient":
                self.handlers[handler_id] = CustomModbusRtuClient(**client_data)
            else:
                raise ValueError(f"Unsupported client type: {item_client.item_handler}")
        return self.handlers[handler_id]

    def get_request_failed_result(self, item: BaseRequest, parent_id: int, execution_session_id: int, error_message: str):
        if item.item_response_handler == "ModbusResponse":
            response = ModbusResponse(
                name=item.name,
                client_type=item.client_type,
                request_id=item.item_id,
                execution_session_id=execution_session_id,
                parent_id=parent_id,
                result="Failed",
                elapsed_time=0,
                timestamp=datetime.now(tzlocal.get_localzone()),
                error_message=error_message
            )
        else:
            raise ValueError(f"Unsupported response type: {item.item_response_handler}")
        return response

    def close_handler(self, protocol: str, **kwargs):
        """Close a handler for the specified protocol."""
        kwargs["protocol"] = protocol
        handler_id = self._generate_handler_id(**kwargs)
        if handler_id in self.handlers:
            self.handlers[handler_id].disconnect()
            del self.handlers[handler_id]

    def close_all_handlers(self):
        """Close a handler for the specified protocol."""
        for handler_client in self.handlers.values():
            handler_client.disconnect()

    def _generate_handler_id(self, **kwargs) -> str:
        """Generate a unique handler ID based on protocol and connection parameters."""
        handler_id = ""
        for key, value in kwargs.items():
            handler_id += f"{key}_{value}_"
        return handler_id[:-1]

    def validate_handler(self,  **kwargs) -> bool:
        """Check if a handler is valid (connected)."""
        handler_id = self._generate_handler_id(**kwargs)
        if handler_id in self.handlers:
            return self.handlers[handler_id].is_connected()
        return False

    def reconnect_handler(self, **kwargs):
        """Reset a handler if it’s invalid."""
        handler_id = self._generate_handler_id(**kwargs)
        if handler_id in self.handlers:
            self.handlers[handler_id].disconnect()
            del self.handlers[handler_id]
        return self.get_handler(**kwargs)
