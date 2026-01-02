from typing import List, AsyncGenerator, Sequence

import aiodocker
from aiohttp import ClientTimeout

from docker_tui.apis.models import Container, ContainerDetails, ImageListItem, PullingStatus, Version, \
    ContainerFsChange, ContainerFsChangeKind, ExecResult


async def get_version() -> Version:
    async with aiodocker.Docker() as docker:
        v = await docker.version()
        return Version(data=v)


async def list_containers() -> List[Container]:
    async with aiodocker.Docker() as docker:
        containers = await docker.containers.list(all=True)
        return [Container(c) for c in containers]


async def get_container_details(id: str) -> ContainerDetails:
    async with aiodocker.Docker() as docker:
        container = await docker.containers.get(container_id=id)
        c = ContainerDetails(container)
        return c


async def get_container_logs(id: str) -> AsyncGenerator[str, None]:
    async with aiodocker.Docker() as docker:
        container = await docker.containers.get(container_id=id)
        stream = container.log(stdout=True, stderr=True, timestamps=True, follow=True)
        async for line in stream:
            yield line


async def get_container_changes(id: str) -> List[ContainerFsChange]:
    async with aiodocker.Docker() as docker:
        data = await docker._query_json(f"containers/{id}/changes", method="GET")
        changes = [ContainerFsChange(kind=ContainerFsChangeKind(i["Kind"]), path=i["Path"]) for i in data or []]
        return changes


async def exec_container(id: str, cmd: str | Sequence[str]) -> ExecResult:
    async with aiodocker.Docker() as docker:
        container = await docker.containers.get(container_id=id)
        c_exec = await container.exec(cmd=cmd)
        stdout = ""
        stderr = ""
        async with c_exec.start(timeout=ClientTimeout(1)) as stream:
            while True:
                msg = await stream.read_out()
                if msg is None:
                    break
                if msg.stream == 1:
                    stdout += msg.data.decode()
                if msg.stream == 2:
                    stderr += msg.data.decode()

        ins = await c_exec.inspect()
        return ExecResult(stdout=stdout, stderr=stderr, exit_code=ins["ExitCode"])


async def stop_container(id: str):
    async with aiodocker.Docker() as docker:
        container = await docker.containers.get(container_id=id)
        await container.stop()


async def restart_container(id: str):
    async with aiodocker.Docker() as docker:
        container = await docker.containers.get(container_id=id)
        await container.restart()


async def delete_container(id: str):
    async with aiodocker.Docker() as docker:
        container = await docker.containers.get(container_id=id)
        await container.delete()


async def list_images() -> List[ImageListItem]:
    async with aiodocker.Docker() as docker:
        images = await docker.images.list()
        return [ImageListItem(i) for i in images]


async def delete_image(id: str):
    async with aiodocker.Docker() as docker:
        await docker.images.delete(name=id)  # id is also ok


async def pull_image(namespace: str, repo: str, tag: str) -> AsyncGenerator[PullingStatus, None]:
    async with aiodocker.Docker() as docker:
        stream = docker.images.pull(from_image=f"{namespace}/{repo}", tag=tag, stream=True)
        async for item in stream:
            yield PullingStatus(item)
