import os
from dataclasses import dataclass

from aiodocker import DockerError
from rich.text import Text
from textual import work, on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable

from docker_tui.docker.api import list_containers, stop_container, restart_container, delete_container
from docker_tui.services.containers_stats_monitor import ContainersStatsMonitor
from docker_tui.views.modals.action_verification_modal import ActionVerificationModal
from docker_tui.views.pages.page import Page


class ContainersListPage(Page):

    @dataclass
    class SelectedContainer:
        id: str
        name: str

    DEFAULT_CSS = """
        #containers-table {
            height: 1fr;
            overflow-y: auto;
            width: 100%;
            background: transparent;
            
            .datatable--header{
                background: transparent;
            }
            .datatable--hover, .datatable--cursor{
                text-style: none;
            }
            #containers-table .column--name {
                width: 100;
            }
        }
    """

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
    last_selected_row_key = None

    def __init__(self):
        super().__init__("Containers")
        self.table = DataTable(cursor_type='row', id="containers-table")
        self.table.add_columns("", "Name", "Id", "Image", "CPU", "Memory", "Status")

    def compose(self) -> ComposeResult:
        yield self.table

    def on_mount(self) -> None:
        super().on_mount()
        self.refresh_table_data()
        self.set_interval(5, self.refresh_table_data)

    @property
    def selected_container(self) -> SelectedContainer | None:
        if self.last_selected_row_key:
            id, name = self.last_selected_row_key.split(";", 2)
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
        if not self.selected_container:
            return
        try:
            await restart_container(id=self.selected_container.id)
        except DockerError as ex:
            self.notify(ex.message, title="Error", severity="error")
            return
        self.notify(f"Container '{self.selected_container.name}' was restarted")
        self.refresh_table_data()

    @work
    async def action_delete(self):
        if not self.selected_container:
            return
        approved = await self.app.push_screen_wait(ActionVerificationModal(
            title=f"Are you sure you want to delete container '{self.selected_container.name}'?",
            button_text="Delete Container",
            button_variant="error"
        ))
        if not approved:
            return
        try:
            await delete_container(id=self.selected_container.id)
        except DockerError as ex:
            self.notify(ex.message, title="Error", severity="error")
            return
        self.notify(f"Container '{self.selected_container.name}' was deleted")
        self.refresh_table_data()

    @on(DataTable.RowSelected)
    def handle_row_selected(self, event: DataTable.RowSelected) -> None:
        if not self.selected_container:
            return
        from docker_tui.views.pages.container_details_page import ContainerDetailsPage
        self.nav_to(page=ContainerDetailsPage(container_name=self.selected_container.name,
                                              container_id=self.selected_container.id))

    @on(DataTable.RowHighlighted)
    def handle_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key.value.startswith(self.PROJECT_ROW_KEY_PREFIX):
            ContainersListPage.last_selected_row_key = None
        else:
            ContainersListPage.last_selected_row_key = event.row_key.value


    @work
    async def refresh_table_data(self) -> None:
        containers = await list_containers()
        containers_stats = {s.container_id:s for s in ContainersStatsMonitor.instance().get_all_stats()}

        self.table.clear()

        projects = {}
        for c in containers:
            projects.setdefault(c.project, []).append(c)

        for (project_name, project_containers) in projects.items():
            grouped = False
            if project_name:
                grouped = True
                self.table.add_row(Text('P', style="bold blue"), Text(project_name),
                                   key=self.PROJECT_ROW_KEY_PREFIX+project_name)

            for i,c in enumerate(project_containers):
                stats = containers_stats.get(c.id)
                name = c.name if not grouped \
                       else ("├─ " if i < len(project_containers)-1 else '└─ ')+c.service
                row_key = f"{c.id};{c.name}"
                if c.state == 'exited':
                    self.table.add_row(
                        Text('○', style="#888888"),
                        Text(name, style="#888888"),
                        Text(c.id[:12], style="#888888"),
                        Text(c.image, style="#888888"),
                        Text("", style="#888888"),
                        Text("", style="#888888"),
                        Text(c.status, style="#888888"),
                        key=row_key)
                else:
                    self.table.add_row(
                        Text('●', style="green"),
                        Text(name),
                        Text(c.id[:12]),
                        Text(c.image),
                        Text(f"{stats.cpu_usage[-1].value:.2f}%" if stats else ""),
                        Text(f"{stats.memory_usage[-1].value:.2f} MB" if stats else ""),
                        Text(c.status),
                        key=row_key)

                if row_key == ContainersListPage.last_selected_row_key:
                    self.table.move_cursor(row=len(self.table.rows))

        self.table.focus()