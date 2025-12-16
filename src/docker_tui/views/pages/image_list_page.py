from dataclasses import dataclass

from ago import human
from aiodocker import DockerError
from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable

from docker_tui.apis.docker_api import delete_image
from docker_tui.services.containers_stats_monitor import ContainersStatsMonitor
from docker_tui.services.images_provider import ImagesProvider
from docker_tui.views.modals.action_verification_modal import ActionVerificationModal
from docker_tui.views.modals.dockerhub_search_modal import DockerhubSearchModal
from docker_tui.views.pages.page import Page


class ImageListPage(Page):
    @dataclass
    class SelectedImage:
        id: str
        name: str

    DEFAULT_CSS = """
            #images-table {
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
            }
        """

    BINDINGS = [
        Binding("p", "pull", "Pull", group=Binding.Group("Actions")),
        Binding("delete", "delete", "Delete", group=Binding.Group("Actions")),
    ]

    last_selected_image_id = None

    def __init__(self, select_image_id: str = None):
        super().__init__("Images")
        self.table = DataTable(cursor_type='row', id="images-table")
        self.table.add_columns("", "Name", "Tag", "Id", "Created At", "Size")
        self.default_selected_image_id = select_image_id

    def compose(self) -> ComposeResult:
        yield self.table

    @work
    async def on_mount(self) -> None:
        super().on_mount()
        self.table.loading = True
        await ContainersStatsMonitor.instance().force_fetch()
        await ImagesProvider.instance().force_fetch()
        self.refresh_table_data()
        self.set_interval(5, self.refresh_table_data)

    @work
    async def action_pull(self):
        selected = await self.app.push_screen_wait(DockerhubSearchModal())
        if not selected:
            return

    @work
    async def action_delete(self):
        if not self.selected_image:
            return
        approved = await self.app.push_screen_wait(ActionVerificationModal(
            title=f"Are you sure you want to delete image '{self.selected_image.name}'?",
            button_text="Delete Container",
            button_variant="error"
        ))
        if not approved:
            return
        try:
            await delete_image(id=self.selected_image.id)
        except DockerError as ex:
            self.notify(ex.message, title="Error", severity="error")
            return
        self.notify(f"Container '{self.selected_image.name}' was deleted")
        self.refresh_table_data()

    @property
    def selected_image(self) -> SelectedImage | None:
        if not self.table.rows:
            return None

        selected_key = list(self.table.rows)[self.table.cursor_row].value
        id, name = selected_key.split(";", 2)
        return ImageListPage.SelectedImage(id=id, name=name)

    def refresh_table_data(self) -> None:
        try:
            containers = ContainersStatsMonitor.instance().get_all_containers()
            images = ImagesProvider.instance().get_images()
        except Exception as ex:
            self.table.loading = False
            self.notify(title="Docker is down", message=str(ex), severity="error")
            return

        in_use_image_ids = set([c.image_id for c in containers])

        # The row to select is either the default one or the current one
        # [!] Note that we can use the default only once
        image_id_to_select = self.default_selected_image_id or \
                             (self.selected_image.id if self.selected_image else None)
        self.default_selected_image_id = None

        if self.table.loading:
            self.table.loading = False

        self.table.clear()

        for image in images:
            is_active = image.id in in_use_image_ids
            icon = '●' if is_active else '○'
            icon_style = "green" if is_active else ""
            self.table.add_row(Text(icon, style=icon_style),
                               Text(image.name),
                               Text(image.tag),
                               Text(image.short_id),
                               Text(human(image.created_at, precision=1)),
                               Text(f"{image.size:.2f} MB"),
                               key=f"{image.id};{image.name}")
            if image.id == image_id_to_select:
                self.table.move_cursor(row=len(self.table.rows))

        self.table.focus()
