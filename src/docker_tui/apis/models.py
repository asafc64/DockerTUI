from datetime import datetime
from typing import List, Dict, Any

from aiodocker.containers import DockerContainer


class Container:
    def __init__(self, data: DockerContainer):
        self.id = data["Id"]
        self.name = data["Names"][0].lstrip('/')
        self.image = data["Image"]
        self.image_id = data["ImageID"]
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
        self.volumes: List[str] = list((data["Config"].get("Volumes", None) or {}).keys())

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


class ImageListItem:
    def __init__(self, data: Dict[str, Any]):
        self.name, self.tag = data["RepoTags"][0].split(":", maxsplit=1)
        self.id = data["Id"]
        self.size = data["Size"] / (1024 * 1024)  # MB
        self.created_at = datetime.fromtimestamp(data["Created"])

    @property
    def short_id(self) -> str:
        return self.id.split(":")[1][:12]


class DockerHubRepo:
    def __init__(self, data: Dict[str, Any]):
        self.display_name = data["repo_name"]
        if "/" in self.display_name:
            self.namespace, self.repo_name = self.display_name.split("/", maxsplit=1)
        else:
            self.namespace = "library"
            self.repo_name = self.display_name
        self.description = data["short_description"]
        self.is_official = data["is_official"]
        self.stars = data["star_count"]
        self.downloads = data["pull_count"]


class DockerHubTag:
    class Image:
        def __init__(self, data: Dict[str, Any]):
            self.architecture = data["architecture"]
            self.digest = data["digest"]
            self.os = data["os"]
            self.variant = data["variant"]
            self.size = data["size"]  # Bytes

        def __str__(self):
            if self.os == "unknown":
                return ''

            return "/".join([x for x in [self.os, self.architecture, self.variant] if x])

    def __init__(self, data: Dict[str, Any]):
        self.images = [DockerHubTag.Image(i) for i in data["images"]]
        self.name = data["name"]
        self.full_size = data["full_size"]
        self.digest = data.get("digest", None)
        self.last_updated = datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00"))


class PullingStatus:
    # {}
    # {'current': 1048576, 'total': 1835502}
    # {'hidecounts': True}
    # {'current': 1, 'units': 's'}
    class ProgressDetail:
        def __init__(self, data: Dict[str, Any]):
            self.current: int | None = data.get("current", None)
            self.total: str | None = data.get("total", None)
            self.hide_counts: bool | None = data.get("hidecounts", None)
            self.unit: str | None = data.get("unit", None)

    def __init__(self, data: Dict[str, Any]):
        self.id: str | None = data.get("id", None)
        self.status: str = data["status"]
        self.progress_detail = PullingStatus.ProgressDetail(data.get("progressDetail", {}))
