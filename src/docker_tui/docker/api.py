from typing import List

import aiodocker

from docker_tui.docker.models import Container, ContainerDetails


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