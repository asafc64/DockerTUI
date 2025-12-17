from typing import List, AsyncGenerator

import aiodocker

from docker_tui.apis.models import Container, ContainerDetails, ImageListItem, PullingStatus


async def list_containers() -> List[Container]:
    async with aiodocker.Docker() as docker:
        containers = await docker.containers.list(all=True)
        return [Container(c) for c in containers]


async def get_container_details(id: str) -> ContainerDetails:
    async with aiodocker.Docker() as docker:
        container = await docker.containers.get(container_id=id)
        c = ContainerDetails(container)
        return c


async def get_container_logs(id: str) -> list[str]:
    async with aiodocker.Docker() as docker:
        container = await docker.containers.get(container_id=id)
        logs = await container.log(stdout=True, stderr=True, timestamps=True)
        return logs


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
