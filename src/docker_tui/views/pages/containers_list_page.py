import os
from dataclasses import dataclass
from typing import List

from aiodocker import DockerError
from rich.text import Text
from textual import work, on, messages
from textual.app import ComposeResult
from textual.binding import Binding
from textual.color import Color
from textual.widgets import DataTable

from docker_tui.apis.docker_api import stop_container, restart_container, delete_container
from docker_tui.apis.models import Container
from docker_tui.services.containers_stats_monitor import ContainersStatsMonitor, ContainerStats
from docker_tui.utils.input_helpers import MouseInputHelper
from docker_tui.views.components.responsive_table import ResponsiveTable, ColumnDefinition, Data, Row, Cell
from docker_tui.views.modals.action_verification_modal import ActionVerificationModal
from docker_tui.views.pages.page import Page


class ContainersListPage(Page):
    @dataclass
    class SelectedContainer:
        id: str
        name: str

    @dataclass
    class Row:
        cells: List[Text]
        key: str

    BINDINGS = [
        Binding("d", "show_details", "Show Details", group=Binding.Group("Inspect")),
        Binding("l", "show_logs", "Show logs", group=Binding.Group("Inspect")),
        Binding("e", "exec", "Exec", group=Binding.Group("Inspect")),
        Binding("k", "stop", "Stop", group=Binding.Group("Actions")),
        Binding("r", "restart", "Restart", group=Binding.Group("Actions")),
        Binding("delete", "delete", "Delete", group=Binding.Group("Actions")),
    ]

    PROJECT_ROW_KEY_PREFIX = "#project#row#"

    is_root_page = True
    last_selected_container_id = None

    def __init__(self, select_container_id: str = None):
        super().__init__("Containers")
        self.table = ResponsiveTable(
            id="containers-table",
            columns=[
                ColumnDefinition("icon", "", "1", 0),
                ColumnDefinition("name", "Name", "1fr", 1, min_width=20),
                ColumnDefinition("id", "Id", "1fr", 4, min_width=12),
                ColumnDefinition("image", "Image", "1fr", 3, min_width=12),
                ColumnDefinition("cpu", "CPU", "1fr", 5),
                ColumnDefinition("mem", "Memory", "1fr", 6),
                ColumnDefinition("status", "Status", "1fr", 2),
            ])
        self.default_selected_container_id = select_container_id or self.last_selected_container_id

    def compose(self) -> ComposeResult:
        yield self.table

    @work
    async def on_mount(self) -> None:
        super().on_mount()
        self.table.loading = True
        await ContainersStatsMonitor.instance().force_fetch()
        self.refresh_table_data()
        self.set_interval(5, self.refresh_table_data)

    def on_prune(self, event: messages.Prune) -> None:
        if self.selected_container:
            ContainersListPage.last_selected_container_id = self.selected_container.id

    @property
    def selected_container(self) -> SelectedContainer | None:
        selected_key = self.table.get_selected_row_key()
        if selected_key and not selected_key.startswith(self.PROJECT_ROW_KEY_PREFIX):
            id, name = selected_key.split(";", 2)
            return ContainersListPage.SelectedContainer(id=id, name=name)

        return None

    def action_show_details(self):
        if not self.selected_container:
            return
        from docker_tui.views.pages.container_details_page import ContainerDetailsPage
        self.nav_to(page=ContainerDetailsPage(container_name=self.selected_container.name,
                                              container_id=self.selected_container.id))

    def action_show_logs(self):
        if not self.selected_container:
            return
        from docker_tui.views.pages.container_log_page import ContainerLogPage
        self.nav_to(page=ContainerLogPage(container_name=self.selected_container.name,
                                          container_id=self.selected_container.id))

    def action_exec(self):
        if not self.selected_container:
            return
        with self.app.suspend():
            os.system(f"docker exec -it {self.selected_container.id} sh")

    @work
    async def action_stop(self):
        if not self.selected_container:
            return
        approved = await self.app.push_screen_wait(ActionVerificationModal(
            title=f"Are you sure you want to stop container '{self.selected_container.name}'?",
            button_text="Stop Container",
            button_variant="error"
        ))
        if not approved:
            return
        try:
            await stop_container(id=self.selected_container.id)
        except DockerError as ex:
            self.notify(ex.message, title="Error", severity="error")
            return
        self.notify(f"Container '{self.selected_container.name}' was stopped")
        self.refresh_table_data()

    @work
    async def action_restart(self):
        container = self.selected_container
        if not container:
            return
        try:
            await restart_container(id=container.id)
        except DockerError as ex:
            self.notify(ex.message, title="Error", severity="error")
            return
        self.notify(f"Container '{container.name}' was restarted")
        self.refresh_table_data()

    @work
    async def action_delete(self):
        container = self.selected_container
        if not container:
            return
        approved = await self.app.push_screen_wait(ActionVerificationModal(
            title=f"Are you sure you want to delete container '{container.name}'?",
            button_text="Delete Container",
            button_variant="error"
        ))
        if not approved:
            return
        try:
            await delete_container(id=container.id)
        except DockerError as ex:
            self.notify(ex.message, title="Error", severity="error")
            return
        self.notify(f"Container '{container.name}' was deleted")
        self.refresh_table_data()

    @on(DataTable.RowSelected)
    def handle_row_selected(self, event: DataTable.RowSelected) -> None:
        container = self.selected_container
        if not container:
            return

        if not MouseInputHelper.is_double_click():
            return

        from docker_tui.views.pages.container_details_page import ContainerDetailsPage
        self.nav_to(page=ContainerDetailsPage(container_name=container.name,
                                              container_id=container.id))

    # @on(DataTable.RowHighlighted)
    # def handle_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
    #     if event.row_key.value.startswith(self.PROJECT_ROW_KEY_PREFIX):
    #         ContainersListPage.last_selected_container_id = None
    #     else:
    #         ContainersListPage.last_selected_container_id = event.row_key.value

    def refresh_table_data(self) -> None:
        try:
            containers = ContainersStatsMonitor.instance().get_all_containers()
            containers_stats = {s.container_id: s for s in ContainersStatsMonitor.instance().get_all_stats()}
        except Exception as ex:
            self.table.loading = False
            self.notify(title="Docker is down", message=str(ex), severity="error")
            return

        if self.table.loading:
            self.table.loading = False

        projects = {}
        for c in containers:
            projects.setdefault(c.project, []).append(c)

        data = Data(rows=[])
        for (project_name, project_containers) in projects.items():
            grouped = False
            if project_name:
                cells = self._build_project_row(name=project_name, containers=project_containers)
                grouped = True
                data.rows.append(Row(cells=cells, row_key=self.PROJECT_ROW_KEY_PREFIX + project_name))

            for i, c in enumerate(project_containers):
                row_key = f"{c.id};{c.name}"
                selected = c.id == self.default_selected_container_id
                stats = containers_stats.get(c.id)
                cells = self._build_container_row(c=c, s=stats, is_grouped=grouped,
                                                  is_last_in_group=(i == len(project_containers) - 1))
                data.rows.append(Row(cells=cells, row_key=row_key, selected=selected))

        self.table.update_table(data=data)
        self.table.focus()
        self.default_selected_container_id = None

    @property
    def _normal_text_color(self):
        return Color.parse(self.app.theme_variables["foreground"]).hex

    @property
    def _muted_text_color(self):
        return "#888888"

    def _build_project_row(self, name: str, containers: List[Container]) -> List[Cell]:
        any_active = any((c.state == "running" for c in containers))
        icon_color = "blue" if any_active else self._muted_text_color
        text_style = "" if any_active else self._muted_text_color
        return [
            Cell("icon", Text('P', style=f"bold {icon_color}")),
            Cell("name", Text(name, style=text_style)),
        ]

    def _build_container_row(self, c: Container, s: ContainerStats | None, is_grouped: bool, is_last_in_group: bool) -> \
            List[Cell]:
        is_active = c.state == "running"
        icon_style = "green" if is_active else self._muted_text_color
        text_style = "" if is_active else self._muted_text_color
        icon = '●' if is_active else '○'
        name = c.name if not is_grouped else ("└─ " if is_last_in_group else "├─ ") + c.service
        cpu = f"{s.cpu_usage[-1].value:.2f}%" if s else ""
        memory = f"{s.memory_usage[-1].value:.2f} MB" if s else ""
        return [
            Cell("icon", Text(icon, style=icon_style)),
            Cell("name", Text(name, style=text_style)),
            Cell("id", Text(c.id[:12], style=text_style)),
            Cell("image", Text(c.image, style=text_style)),
            Cell("cpu", Text(cpu, style=text_style)),
            Cell("mem", Text(memory, style=text_style)),
            Cell("status", Text(c.status, style=text_style))
        ]
