from dataclasses import asdict

from backend.handlers.base_handler import BaseHandler
from backend.handlers.custom_modbus_handler import CustomModbusTcpClient, CustomModbusRtuClient
from backend.models.base import BaseItem


class ProtocolClientManager:
    def __init__(self, model):
        self.model = model
        self.handlers: dict[str, BaseHandler] = {}  # Key: handler ID, Value: handler

    def get_handler(self, item: BaseItem) -> BaseHandler:
        """Get or create a handler for the specified protocol."""

        def find_item_client(item: BaseItem, base_item: BaseItem) -> BaseItem:
            if item.client_type == "No connection":
                raise Exception(f"Current request does not have client")
            elif item.client_type == "Inherit from parent":
                parent = self.model.get_item(item.parent)
                return find_item_client(parent, base_item)
            elif item.client:
                if item.client.item_type == base_item.item_type:
                    return item.client
                else:
                    raise Exception(f"Current request client protocol is not correct: expected {base_item.item_type} - found {item.item_type}")
            else:
                raise Exception(f"FATAL ERROR - Could not resolve item client: {item.client} - {item}")

        item_client = find_item_client(item=item, base_item=item)
        client_data = asdict(item_client)

        handler_id = self._generate_handler_id(**client_data)
        if handler_id not in self.handlers:
            if item_client.item_handler == "ModbusTcpClient":
                self.handlers[handler_id] = CustomModbusTcpClient(**client_data)
            elif item_client.item_handler == "ModbusRtuClient":
                self.handlers[handler_id] = CustomModbusRtuClient(**client_data)
            else:
                raise ValueError(f"Unsupported Modbus client type: {item_client.item_handler}")
        return self.handlers[handler_id]

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
