import json
from dataclasses import dataclass, asdict
from utils.logger import CustomLogger
from backend.protocols.protocol_factory import ProtocolFactory


class BackendManager:
    def __init__(self):
        self._logger = CustomLogger(name=__name__)
        self.clients = {}

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

    def run_project(self, project_file_path: str, element: str):
        with open(project_file_path) as file:
            project_file = json.load(file)
            self._process_project_file(project_file[element])

    def execute_request(self):
        pass


if __name__ == "__main__":
    backend_manager = BackendManager()
    backend_manager.run_project("inputs/project.json", "project_1")
