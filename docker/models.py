from datetime import datetime

from aiodocker.containers import DockerContainer


class Container:
    def __init__(self, data: DockerContainer):
        self.id = data["Id"]
        self.name = data["Names"][0]
        self.image = data["Image"]
        self.state = data["State"]
        self.status = data["Status"]
        self.created_at = datetime.fromtimestamp(data["Created"])
