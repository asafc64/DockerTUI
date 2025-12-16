from typing import List, Any

import aiodocker

from docker_tui.docker.models import Container, ContainerDetails, ImageListItem, DockerHubImage

import aiohttp
from typing import Any, Dict

DOCKER_HUB_SEARCH_URL = "https://hub.docker.com/v2/search/repositories/"


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
        await docker.images.delete(name=id) # id is also ok

async def search_dockerhub(query: str) -> List[DockerHubImage]:

    params = {
        "query": query,
        "page": 1,
        "page_size": 100,
    }

    async with aiohttp.ClientSession() as client:
        async with client.get(DOCKER_HUB_SEARCH_URL, params=params) as resp:
            resp.raise_for_status()
            response = await resp.json()
            return [DockerHubImage(r) for r in response["results"]]


