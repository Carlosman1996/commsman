import json
from utils.logger import CustomLogger
from backend.protocols.protocol_factory import ProtocolFactory


class BackendManager:
    def __init__(self, project_file_path: str):
        self._logger = CustomLogger(name=__name__)
        self.clients = {}

        with open(project_file_path) as file:
            self.project_file = json.load(file)

    def _process_project_file(self, folder: dict):
        for element, data in folder.items():
            if data["type"] == "folder":
                self._process_project_file(data["elements"])
            elif data["type"] == "connection":
                self.clients[data["client"]] = ProtocolFactory.get_handler(name=element,
                                                                           protocol=data["protocol"],
                                                                           **data["values"])
                self.clients[data["client"]].connect()
            elif data["type"] == "disconnection":
                self.clients[data["client"]].disconnect()
            elif data["type"] == "request":
                request = ProtocolFactory.get_request(name=element, protocol=data["protocol"], **data["values"])
                request_result = self.clients[request.client].execute_request(request)
                self._logger.info(f"Request {request} result: {request_result}")

    def run(self, element: str):
        self._process_project_file(self.project_file[element])


if __name__ == "__main__":
    backend_manager = BackendManager("inputs/project.json")
    backend_manager.run("project_1")
