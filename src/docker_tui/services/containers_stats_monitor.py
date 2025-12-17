from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict

import aiodocker

from docker_tui.apis.docker_api import list_containers
from docker_tui.apis.models import Container
from docker_tui.utils.async_background import AsyncBackground
from docker_tui.utils.async_background_loop import AsyncBackgroundLoop


@dataclass
class DataPoint:
    timestamp: datetime
    value: float


@dataclass
class ContainerStats:
    container_id: str
    cpu_usage: List[DataPoint]
    memory_usage: List[DataPoint]


class ContainersStatsMonitor(AsyncBackgroundLoop):
    _instance = None

    def __init__(self):
        super().__init__()
        self._containers: List[Container] = []
        self._listeners: Dict[str, ContainerStatsListener] = {}
        self._last_exception: Exception | None = None

    @classmethod
    def instance(cls) -> 'ContainersStatsMonitor':
        if not cls._instance:
            cls._instance = ContainersStatsMonitor()
        return cls._instance

    def get_all_containers(self) -> List[Container]:
        if self._last_exception:
            raise self._last_exception

        return self._containers

    def get_all_stats(self) -> List[ContainerStats]:
        if self._last_exception:
            raise self._last_exception

        return [l.get_stats() for l in self._listeners.values()]

    def get_stats(self, container_id: str) -> ContainerStats | None:
        if self._last_exception:
            raise self._last_exception

        listener = self._listeners.get(container_id, None)
        if not listener:
            return None

        return listener.get_stats()

    async def force_fetch(self):
        await self._run_in_loop()

    async def _run_in_loop(self):
        self._last_exception = None
        try:
            # Clear dead listeners
            for (id, listener) in list(self._listeners.items()):
                if not listener.is_running():
                    self._listeners.pop(id)

            # Create new listeners if needed
            self._containers = await list_containers()
            for c in self._containers:
                if c.state == "running" and c.id not in self._listeners:
                    new_listener = ContainerStatsListener(container_id=c.id)
                    new_listener.start()
                    self._listeners[c.id] = new_listener

            # Delete existing listeners  if needed
            for c in self._containers:
                if c.state != "running" and c.id in self._listeners:
                    old_listener = self._listeners.pop(c.id)
                    await old_listener.close()

        except Exception as ex:
            self._last_exception = ex


class ContainerStatsListener(AsyncBackground):

    def __init__(self, container_id):
        super().__init__()
        self.container_id = container_id

        self.cpu_usage = deque(maxlen=60)
        self.memory_usage = deque(maxlen=60)

        now = self.get_now_by_seconds()
        for i in range(60, 0, -1):
            self.cpu_usage.append(DataPoint(now - timedelta(seconds=i), 0.0))
            self.memory_usage.append(DataPoint(now - timedelta(seconds=i), 0.0))

    @staticmethod
    def get_now_by_seconds() -> datetime:
        return datetime.now().replace(microsecond=0)

    def get_stats(self) -> ContainerStats:
        return ContainerStats(container_id=self.container_id,
                              cpu_usage=list(self.cpu_usage),
                              memory_usage=list(self.memory_usage))

    async def _run(self):
        async with aiodocker.Docker() as docker:
            try:
                container = await docker.containers.get(container_id=self.container_id)
                prev_stats = None

                async for new_stats in container.stats():
                    if not prev_stats:
                        prev_stats = new_stats
                        continue

                    self.cpu_usage.append(DataPoint(timestamp=self.get_now_by_seconds(),
                                                    value=self._calc_cpu_percent(prev_stats, new_stats)))
                    self.memory_usage.append(DataPoint(timestamp=self.get_now_by_seconds(),
                                                       value=self._calc_memory_usage(new_stats)))

                    # print(self.container_id)
                    # print(f"CPU Usage:    {self.cpu_usage:.2f}%")
                    # print(f"Memory Usage: {self.memory_usage:.2f} MB")
                    prev_stats = new_stats

            except Exception as ex:
                print(str(ex))

    @staticmethod
    def _calc_cpu_percent(prev, curr):
        if curr["cpu_stats"]["cpu_usage"]["total_usage"] == 0 or \
                "system_cpu_usage" not in prev["cpu_stats"]:
            return 0.0

        cpu_delta = curr["cpu_stats"]["cpu_usage"]["total_usage"] - \
                    prev["cpu_stats"]["cpu_usage"]["total_usage"]

        system_delta = curr["cpu_stats"]["system_cpu_usage"] - \
                       prev["cpu_stats"]["system_cpu_usage"]

        online_cpus = curr["cpu_stats"].get("online_cpus", 1)

        if system_delta > 0 and cpu_delta > 0:
            return (cpu_delta / system_delta) * online_cpus * 100.0
        return 0.0

    @staticmethod
    def _calc_memory_usage(stats) -> float:
        if stats['memory_stats']:
            return stats['memory_stats']['usage'] / (1024 * 1024)
        return 0.0
