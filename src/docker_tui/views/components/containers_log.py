import logging
from asyncio import CancelledError
from datetime import datetime
from typing import List

from rich.color import ANSI_COLOR_NAMES
from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import RichLog, Label

from docker_tui.apis.docker_api import get_container_logs
from docker_tui.services.containers_stats_monitor import ContainersStatsMonitor

logger = logging.getLogger(__name__)


class ContainersLog(Widget):
    DEFAULT_CSS = """
        ContainersLog > RichLog:blur {
            background: transparent;
        }
        .preview-title {
            text-style: bold;
        }
    """

    container_ids: Reactive[frozenset[str]] = Reactive(frozenset())

    def __init__(self, container_ids: List[str]):
        super().__init__()
        self.set_reactive(ContainersLog.container_ids, frozenset(container_ids))
        self._colors = [c for c in ANSI_COLOR_NAMES.keys() if c.startswith("light_")]

    def compose(self) -> ComposeResult:
        yield Label("Logs", classes="preview-title")
        yield RichLog(max_lines=100)

    def on_mount(self) -> None:
        self.loading = True
        containers = [c for c in ContainersStatsMonitor.instance().get_all_containers() if c.id in self.container_ids]
        for i, container in enumerate(containers):
            color = self._colors[i % len(self._colors)]
            self.start_log_fetcher(container_id=container.id, container_name=container.name, color=color,
                                   is_single=len(containers) == 1)

    @work()
    async def start_log_fetcher(self, container_id: str, container_name: str, color: str, is_single: bool) -> None:
        log = self.query_one(RichLog)
        try:
            async for line in get_container_logs(id=container_id):
                time_iso, log_line = line.split(" ", maxsplit=1)
                timestamp = datetime.fromisoformat(time_iso.replace("Z", "+00:00"))

                txt = Text(end="")
                if not is_single:
                    txt.append(container_name + " ", style=color)
                txt.append(timestamp.strftime("%Y-%m-%d %H:%M:%S") + " ", style="#888888")
                txt.append(log_line)

                # txt = Text(f"[{container_name}] {line}", style=color_name, end="")
                # txt.stylize(style=color_name, start=0, end=len(container_name) + 2)
                log.write(txt)
                # await asyncio.sleep(1)
                self.loading = False
        except CancelledError:
            pass
        except:
            logger.exception("Container log streaming failed")
