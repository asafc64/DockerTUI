from dataclasses import dataclass
from datetime import datetime
from typing import List

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
