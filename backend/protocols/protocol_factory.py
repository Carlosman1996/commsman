from backend.protocols.modbus_handler import ModbusHandler, ModbusRequest


class ProtocolFactory:
    @staticmethod
    def get_handler(name: str, protocol: str, **kwargs):
        match protocol:
            case "MODBUS":
                return ModbusHandler(name=name, client=kwargs.get("client"), host=kwargs.get("host"), port=kwargs.get("port"))
            case _:
                raise NotImplementedError(f"Protocol {protocol} not supported")

    @staticmethod
    def get_request(name: str, protocol: str, **kwargs):
        match protocol:
            case "MODBUS":
                return ModbusRequest(name=name, **kwargs)
            case _:
                raise NotImplementedError(f"Protocol {protocol} not supported")
