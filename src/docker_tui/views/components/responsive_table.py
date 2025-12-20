from dataclasses import dataclass
from typing import List

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.layouts.horizontal import HorizontalLayout
from textual.widget import Widget
from textual.widgets import Static, DataTable


@dataclass
class ColumnDefinition:
    key: str
    label: str
    width: str
    priority: int
    min_width: int = None


@dataclass
class Cell:
    col_key: str
    value: Text


@dataclass
class Row:
    cells: List[Cell]
    row_key: str
    selected: bool = False


@dataclass
class Data:
    rows: List[Row]


class MockHeader(Static):
    def __init__(self, col: ColumnDefinition):
        super().__init__(content=col.label)
        self.header_key = col.key
        self.styles.height = "auto"
        self.styles.margin = (0, 2)
        self.styles.width = col.width
        self.styles.min_width = col.min_width or len(col.label)


class ResponsiveTable(Widget):
    DEFAULT_CSS = """
        #inner-table {
            height: auto;
            overlay: screen;
            background: transparent;

            .datatable--header{
                background: transparent;
            }
            .datatable--hover, .datatable--cursor{
                text-style: none;
            }
        }
    """

    def __init__(self, id: str, columns: list[ColumnDefinition]):
        super().__init__(id=id)
        self._data: Data = Data(rows=[])
        self.columns = columns
        self.visible_columns_keys: List[str] = []
        self.table = DataTable(id="inner-table", cursor_type='row')

    def compose(self) -> ComposeResult:
        yield self.table

    def on_mount(self):
        self._recompute_columns()

    def on_resize(self, event: events.Resize):
        self._recompute_columns()

    def _on_focus(self, event: events.Focus) -> None:
        self.table.focus()

    def update_table(self, data: Data):
        self._data = data

        for row in data.rows:
            relevant_sorted_cells = self._get_cells_to_insert(cells=row.cells)

            # update existing rows
            if self._is_row_in_table(row_key=row.row_key):
                for cell in relevant_sorted_cells:
                    self.table.update_cell(row_key=row.row_key, column_key=cell.col_key, value=cell.value)

            # add missing rows
            else:
                self.table.add_row(*(c.value for c in relevant_sorted_cells), key=row.row_key)

        # remove unwanted rows
        rows_keys_to_remove = set([k.value for k in self.table.rows.keys()]) - set([r.row_key for r in data.rows])
        for row_key in rows_keys_to_remove:
            self.table.remove_row(row_key=row_key)

        # update selected row
        selected_row_index = next((i for i, r in enumerate(data.rows) if r.selected), None)
        if selected_row_index is not None:
            self.table.move_cursor(row=selected_row_index)

        self.table.focus()

    def get_selected_row_key(self) -> str | None:
        if not self._data.rows:
            return None
        selected_key = self._data.rows[self.table.cursor_row].row_key
        return selected_key

    def _get_cells_to_insert(self, cells: List[Cell]) -> List[Cell]:
        visible_cells = [cell for cell in cells if cell.col_key in self.visible_columns_keys]
        ordered_cells = sorted(visible_cells, key=lambda cell: self.table.get_column_index(column_key=cell.col_key))
        return ordered_cells

    def _is_row_in_table(self, row_key: str):
        try:
            self.table.get_row(row_key=row_key)
            return True
        except:
            return False

    def _recompute_columns(self):
        visible_columns = list(self.columns)
        placements = []

        while len(visible_columns) > 0:

            header_cells = [MockHeader(col=col) for col in visible_columns]
            placements = HorizontalLayout().arrange(self, header_cells, self.size)

            any_broken = any(
                (p.widget.styles.min_width and p.widget.styles.min_width.cells > p.region.width for p in placements))
            if not any_broken and sum([p.region.width for p in placements]) <= self.size.width:
                break

            col_to_remove = max(visible_columns, key=lambda col: col.priority)
            visible_columns.remove(col_to_remove)

        selected_row = self.table.cursor_row

        self.table.clear(columns=True)

        for placement in placements:
            header: MockHeader = placement.widget
            header_content = header.content
            header_key = header.header_key
            header_width = placement.region.width
            self.table.add_column(label=header_content, width=header_width, key=header_key)

        self.visible_columns_keys = set((col.key for col in visible_columns))

        for row in self._data.rows:
            cells = self._get_cells_to_insert(cells=row.cells)
            self.table.add_row(*(c.value for c in cells), key=row.row_key)

        self.table.move_cursor(row=selected_row)
        self.table.focus()
