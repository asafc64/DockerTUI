from datetime import datetime, UTC

from humanize import naturaltime, naturalsize


def ago(dt: datetime) -> str:
    return naturaltime(datetime.now(UTC) - dt, )


def file_size(s: int) -> str:
    return naturalsize(s, gnu=True)
