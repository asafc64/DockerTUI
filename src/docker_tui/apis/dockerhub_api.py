from typing import List

import aiohttp

from docker_tui.apis.models import DockerHubRepo

DOCKER_HUB_SEARCH_URL = "https://hub.docker.com/v2/search/repositories/"


async def search_repo(query: str, page: int = 1, page_size: int = 50) -> List[DockerHubRepo]:
    params = {
        "query": query,
        "page": page,
        "page_size": page_size,
    }
    async with aiohttp.ClientSession() as client:
        async with client.get(DOCKER_HUB_SEARCH_URL, params=params) as resp:
            resp.raise_for_status()
            response = await resp.json()
            return [DockerHubRepo(r) for r in response["results"]]
