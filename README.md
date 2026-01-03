# Docker TUI

Yet another console user interface for docker,
inspired by [k9s](https://github.com/derailed/k9s),
and based on [Textual](https://github.com/Textualize/textual).

<img src="https://raw.githubusercontent.com/asafc64/DockerTUI/refs/heads/master/assets/containers_list.png"/>

<div align="center">
    <img width="45%" src="https://raw.githubusercontent.com/asafc64/DockerTUI/refs/heads/master/assets/container_bottom_preview.png"/>
    <img width="45%" src="https://raw.githubusercontent.com/asafc64/DockerTUI/refs/heads/master/assets/container_side_preview.png"/>
</div>

## Features

### Global Navigation

- **Quick search and navigation**</br>
  Jump to any view or resource in the application using keyboard-based navigation.

- **Type-to-select lists**</br>
  All lists support incremental type-to-select (similar to file browsers), allowing quick navigation by typing an item’s
  name.

### Containers

- **Container list view**</br>
  Displays containers grouped by project, showing relevant information such as status, image, CPU usage, and memory
  usage.

- **Container logs view**</br>
  Displays logs at the project level, allowing multiple container logs to be viewed simultaneously.

- **Container files view**</br>
  Presents a filesystem view similar to ls, showing added, modified, and deleted files, with clear indication of mounted
  volumes. Supports editing text files, and deleting files and folders.

- **Container details and stats view**</br>
  Combines container configuration details with runtime statistics, including CPU and memory usage.

- **Execute commands (exec)**</br>
  Run commands or open an interactive shell inside a running container.

- **Lifecycle actions**</br>
  Stop, restart, or delete containers directly from the interface.

### Images

- **Image list view**</br>
  Lists all local Docker images along with relevant metadata.

- **Image deletion**</br>
  Remove unused or unwanted images.

- **Image pull wizard**</br>
  Pull images using a guided, interactive workflow for selecting repositories and tags.

## 2-Steps to get it running

Install:

```bash
pip install docker-tui
```

Run:

```bash
dtui
```