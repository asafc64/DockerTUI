from datetime import datetime
from typing import List, Dict, Any

from aiodocker.containers import DockerContainer


class Container:
    def __init__(self, data: DockerContainer):
        self.id = data["Id"]
        self.name = data["Names"][0].lstrip('/')
        self.image = data["Image"]
        self.state = data["State"]
        self.status = data["Status"]
        self.created_at = datetime.fromtimestamp(data["Created"])
        self.project = data["Labels"].get("com.docker.compose.project")
        self.service = data["Labels"].get("com.docker.compose.service")

class ContainerDetails:
    def __init__(self, data: DockerContainer):
        self.id: str = data["Id"]
        self.path: str = data["Path"]
        self.args: List[str] = data["Args"]
        self.env: List[str] = data["Config"]["Env"]
        self.image: str = data["Config"]["Image"]
        self.volumes: List[str] = list(data["Config"]["Volumes"].keys())

        if data["State"]["Running"]:
            self.status: str = "Running"
            self.status_at: datetime = datetime.fromisoformat(data["State"]["StartedAt"])
        else:
            self.status: str = "Exited"
            self.status_at: datetime = datetime.fromisoformat(data["State"]["FinishedAt"])

        self.ports = []
        for (local, host) in data["NetworkSettings"]["Ports"].items():
            if not host:
                continue
            local_port = local.split("/")[0]
            host_port = host[0]["HostPort"]
            self.ports.append((local_port, host_port))
