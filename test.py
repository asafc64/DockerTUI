import asyncio
from datetime import datetime
from typing import List

import aiodocker
from aiodocker.containers import DockerContainer

from docker.api import get_container


async def main():
    await get_container(id="042e561fd0b5986aeda994240379b52cc572677462a3cd0a33646f1e589099e0")


if __name__ == "__main__":
    asyncio.run(main())