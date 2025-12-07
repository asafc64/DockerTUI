from typing import List

import aiodocker

from docker.models import Container, ContainerDetails


async def list_containers() -> List[Container]:
    async with aiodocker.Docker() as docker:
        containers = await docker.containers.list(all=True)
        return [Container(c) for c in containers]

async def get_container(id: str) -> ContainerDetails:
    async with aiodocker.Docker() as docker:
        container = await docker.containers.get(container_id=id)
        c = ContainerDetails(container)
        stats = await container.stats(stream=False)
        return c