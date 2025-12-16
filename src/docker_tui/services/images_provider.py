from typing import List

from docker_tui.apis.docker_api import list_images
from docker_tui.apis.models import ImageListItem
from docker_tui.utils.async_background_loop import AsyncBackgroundLoop


class ImagesProvider(AsyncBackgroundLoop):
    _instance = None

    def __init__(self):
        super().__init__()
        self._images: List[ImageListItem] = []
        self._last_exception: Exception | None = None

    @classmethod
    def instance(cls) -> 'ImagesProvider':
        if not cls._instance:
            cls._instance = ImagesProvider()
        return cls._instance

    def get_images(self) -> List[ImageListItem]:
        if self._last_exception:
            raise self._last_exception

        return self._images

    async def force_fetch(self):
        await self._run_in_loop()

    async def _run_in_loop(self):
        try:
            self._images = await list_images()
        except Exception as ex:
            self._last_exception = ex
