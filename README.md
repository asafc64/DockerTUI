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

- Quick search-and-navigate to anywhere in the app.
- Container views: list, logs, details, and stats.
- Container actions: exec, stop, restart, delete.
- Image views: list.
- Image actions: delete, easy-pull wizard.

## 2-Steps to get it running

Install:

```bash
pip install docker-tui
```

Run:

```bash
dtui
```