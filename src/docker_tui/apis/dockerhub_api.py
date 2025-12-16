from typing import List

import aiohttp

from docker_tui.apis.models import DockerHubRepo, DockerHubTag

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


async def search_tags(namespace: str, repo: str, query: str, page: int = None, page_size: int = None) -> List[
    DockerHubTag]:
    url = f"https://hub.docker.com/v2/namespaces/{namespace}/repositories/{repo}/tags"
    params = {
        "name": query,
        "page": page or "NaN",
        "page_size": page_size or "NaN",
        "ordering": "last_updated"
    }
    async with aiohttp.ClientSession() as client:
        async with client.get(url, params=params) as resp:
            resp.raise_for_status()
            response = await resp.json()
            return [DockerHubTag(r) for r in response["results"]]
