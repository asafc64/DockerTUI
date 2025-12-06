import asyncio
from datetime import datetime
from typing import List

import aiodocker
from aiodocker.containers import DockerContainer



async def main():
    # Initialize the aiodocker client
    async with aiodocker.Docker() as docker:
        # Example: List all running containers
        containers = await docker.containers.list(all=True)
        print("Running containers:")
        for container in containers:
            c = Container(container)
            print(f"- {container._id} ({container._container['Names'][0]})")

        # # Example: Pull an image
        # print("\nPulling nginx image...")
        # await docker.images.pull("nginx")
        # print("Nginx image pulled.")
        #
        # # Example: Run a container
        # print("\nRunning a new container...")
        # config = {
        #     "Image": "nginx",
        #     "HostConfig": {"PortBindings": {"80/tcp": [{"HostPort": "8080"}]}},
        # }
        # container = await docker.containers.run(config=config)
        # print(f"Container {container._id} started.")
        #
        # # Example: Inspect the container
        # container_info = await container.show()
        # print(f"Container IP: {container_info['NetworkSettings']['IPAddress']}")
        #
        # # Example: Stop and remove the container
        # print(f"\nStopping and removing container {container._id}...")
        # await container.stop()
        # await container.delete()
        # print("Container stopped and removed.")


if __name__ == "__main__":
    asyncio.run(main())