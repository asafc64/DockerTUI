import io
import tarfile
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List

import aiodocker

from docker_tui.apis.docker_api import exec_container


@dataclass
class FsEntry:
    path: str
    mode: str
    user: str
    group: str
    size: int
    modified: datetime

    @property
    def name(self) -> str:
        return self.get_name(path=self.path)

    @property
    def is_directory(self) -> bool:
        return self.mode.startswith("d")

    @property
    def is_file(self) -> bool:
        return not self.is_directory

    @staticmethod
    def get_name(path: str):
        return path.split("/")[-1]


async def list_container_files(container_id: str, path: str) -> List[FsEntry]:
    cmd = ["sh", "-c", f"stat -c '%A\t%U\t%G\t%s\t%y\t%n' {path}/.[!.]* {path}/* 2>/dev/null"]
    stdout = ""
    entries = []
    async for item in exec_container(id=container_id, cmd=cmd):
        stdout += item

    for line in stdout.split("\n"):
        if not line:
            continue
        parts = line.split("\t", maxsplit=6)
        entry = FsEntry(
            mode=parts[0],
            user=parts[1],
            group=parts[2],
            size=int(parts[3]),
            modified=_parse_datetime(parts[4]),
            path=parts[5].replace("//", "/")
        )
        entries.append(entry)
        print(line)
    return entries


def _parse_datetime(s: str) -> datetime:
    date_part, frac_tz = s.split(".")
    frac, tz = frac_tz.split(" ")
    s_fixed = f"{date_part}.{frac[:6]} {tz}"
    dt = datetime.strptime(s_fixed, "%Y-%m-%d %H:%M:%S.%f %z")
    return dt


async def read_container_file(container_id: str, path: str) -> bytes:
    dir_path, filename = path.rsplit("/", 1)
    async with aiodocker.Docker() as docker:
        container = docker.containers.container(container_id=container_id)
        with await container.get_archive(path=path) as tar:
            file = tar.extractfile(filename)
            return file.read()


async def write_container_file(container_id: str, path: str, content: bytes):
    async with aiodocker.Docker() as docker:
        container = docker.containers.container(container_id)

        # Split path into directory + filename
        dir_path, filename = path.rsplit("/", 1)

        # Create tar archive in memory
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(content)
            tarinfo.mtime = int(time.time())
            tarinfo.mode = 0o644

            tar.addfile(tarinfo, io.BytesIO(content))

        tar_stream.seek(0)

        # Upload archive
        await container.put_archive(
            path=dir_path,
            data=tar_stream.read(),
        )
