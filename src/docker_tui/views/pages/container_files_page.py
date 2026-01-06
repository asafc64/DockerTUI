from typing import Dict, List

from rich.text import Text
from textual import work, on, events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.reactive import Reactive
from textual.widgets import DataTable, Label

from docker_tui.apis.docker_api import get_container_changes, get_container_details
from docker_tui.apis.models import ContainerFsChangeKind
from docker_tui.services.container_filesystem_explorer import list_container_files, FsEntry, read_container_file, \
    write_container_file, delete_container_file
from docker_tui.utils.external_files_editor import edit_text
from docker_tui.utils.formating import file_size, ago
from docker_tui.views.components.responsive_table import ResponsiveTable, ColumnDefinition, Data, Row, Cell
from docker_tui.views.modals.action_verification_modal import ActionVerificationModal
from docker_tui.views.pages.page import Page


class ContainerFilesPage(Page):
    DEFAULT_CSS = """
        #current-path-label{
            margin: 1;
            width: 1fr;
            dock: top;
            border-bottom: solid $secondary;
            text-style: bold;
        }
    """

    BINDINGS = [
        Binding("f5", "refresh", "Refresh", group=Binding.Group("Actions")),
        Binding("f2", "edit_file", "Edit", group=Binding.Group("Actions")),
        Binding("delete", "delete_file", "Delete", group=Binding.Group("Actions"))
    ]

    path: Reactive[str] = Reactive("/")

    def __init__(self, container_name: str, container_id: str):
        super().__init__(title=f"Containers > {container_name} > Files")
        self.container_id = container_id
        self.path_label = Label("/", id="current-path-label")
        self.table = ResponsiveTable(
            id="files-table",
            columns=[
                ColumnDefinition("mode", "Mode", "11", 1),
                ColumnDefinition("name", "Name", "3fr", 0, min_width=50),
                ColumnDefinition("tag", "Tag", "1fr", 2, min_width=5),
                ColumnDefinition("size", "Size", "1fr", 3),
                ColumnDefinition("modified", "Modified", "1fr", 4),
                ColumnDefinition("user", "User", "1fr", 5),
                ColumnDefinition("group", "Group", "1fr", 6),
            ],
            type_to_select_column_key="name"
        )
        self.changes: Dict[str, ContainerFsChangeKind] | None = None
        self.volumes: List[str] | None = None
        self.files: Dict[str, FsEntry] = {}

    def compose(self) -> ComposeResult:
        yield self.path_label
        yield self.table

    def on_mount(self) -> None:
        self.table.loading = True
        self._populate_table()

    def nav_back(self):
        from docker_tui.views.pages.containers_list_page import ContainersListPage
        self.nav_to(page=ContainersListPage())

    @on(DataTable.RowSelected)
    def handle_row_selected(self, event: DataTable.RowSelected) -> None:
        file = self.files[event.row_key.value]
        if file.is_directory:
            self.path = file.path

    @work
    async def action_refresh(self):
        self._populate_table()

    @work
    async def action_edit_file(self):
        file = self.files[self.table.get_selected_row_key()]
        if not file.is_file:
            self.notify("Only regular files are editable", severity="warning")
            return

        file_bytes = await read_container_file(container_id=self.container_id, path=file.path)
        new_txt = edit_text(file_bytes.decode(), file.name)
        new_file_bytes = new_txt.encode()
        if new_file_bytes != file_bytes:
            await write_container_file(container_id=self.container_id, path=file.path, content=new_file_bytes)
            self.notify("File Saved")

    @work
    async def action_delete_file(self):
        file = self.files[self.table.get_selected_row_key()]
        f_type = file.file_type
        approved = await self.app.push_screen_wait(ActionVerificationModal(
            title=f"Are you sure you want to delete {f_type.lower()} '{file.path}'?",
            button_text="Delete",
            button_variant="error"
        ))
        if not approved:
            return

        try:
            await delete_container_file(container_id=self.container_id, path=file.path)
            self.notify(title="Deletion Succeeded", message=f"{f_type} '{file.path}' was successfully deleted")
            self._populate_table()
        except Exception as ex:
            self.notify(title="Deletion Failed", message=str(ex), severity="error")

    def watch_path(self, old_value: str, new_value: str):
        self.path_label.update(new_value)
        self._populate_table(select_file=old_value)

    def on_key(self, event: events.Key) -> None:
        if (event.key == "escape" or event.key == "backspace") and not self._is_root():
            self.path = self._get_parent_path(self.path)
            event.prevent_default()
            event.stop()

    def _is_root(self):
        return self.path == "/"

    @staticmethod
    def _get_parent_path(path: str):
        parent = path[:path.rindex("/")]
        return parent if parent != "" else "/"

    @work(exclusive=True)
    async def _populate_table(self, select_file: str = None):
        self.table.loading = True
        try:
            await self._fetch_changes_if_needed()
            await self._fetch_volumes_if_needed()
            entries = await list_container_files(container_id=self.container_id,
                                                 path=self.path)
            self.files = {e.path: e for e in entries}
        except Exception as ex:
            self.table.loading = False
            self.notify(title="Failed to list files", message=str(ex), severity="error")
            # rollback path value in case navigation failed
            self.path = self._get_parent_path(next(iter(self.files.keys())))
            return

        select_file = select_file or self.table.get_selected_row_key()

        data = Data(rows=[])

        for entry in entries:
            data.rows.append(Row(
                cells=[
                    Cell("mode", Text(entry.mode)),
                    Cell("name", Text(entry.name)),
                    Cell("tag", self._get_tag(entry.path)),
                    Cell("size", Text(file_size(entry.size)) if not entry.is_directory else Text("")),
                    Cell("modified", Text(ago(entry.modified))),
                    Cell("user", Text(entry.user)),
                    Cell("group", Text(entry.group))
                ],
                row_key=entry.path,
                selected=select_file == entry.path
            ))

        for path, kind in self.changes.items():
            if self._get_parent_path(path) == self.path and kind == ContainerFsChangeKind.Deleted:
                name = FsEntry.get_name(path=path)
                data.rows.append(Row(
                    cells=[
                        Cell("mode", Text("---")),
                        Cell("name", Text(name)),
                        Cell("tag", self._get_tag(path))
                    ],
                    row_key=path
                ))

        data.rows = sorted(data.rows, key=lambda e: e.row_key)

        self.table.update_table(data=data)
        self.table.loading = False

    def _get_tag(self, path: str) -> Text:
        # folder is mapped to volume
        if any((v == path for v in self.volumes)):
            return Text("Volume", style="purple")

        # contains folder that is mapped to volume
        if any((v.startswith(path) for v in self.volumes)):
            return Text("Contains Volume", style="purple")

        # folder is inside a mapped volume
        if any((path.startswith(v) for v in self.volumes)):
            return Text("Inside Volume", style="purple")

        change = self.changes.get(path, None)
        if change == ContainerFsChangeKind.Added:
            return Text("Added", style="green")
        if change == ContainerFsChangeKind.Modified:
            return Text("Modified", style="dark_goldenrod")
        if change == ContainerFsChangeKind.Deleted:
            return Text("Deleted", style="red")

        return Text("")

    async def _fetch_changes_if_needed(self):
        if self.changes is None:
            changes = await get_container_changes(id=self.container_id)
            self.changes = {c.path: c.kind for c in changes}

    async def _fetch_volumes_if_needed(self):
        if self.volumes is None:
            details = await get_container_details(id=self.container_id)
            self.volumes = details.volumes
