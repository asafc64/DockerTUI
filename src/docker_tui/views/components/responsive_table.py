import re
from dataclasses import dataclass
from typing import List, Dict

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.layouts.horizontal import HorizontalLayout
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Static, DataTable

from docker_tui.utils.input_helpers import TypeToSelect


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

    def __getitem__(self, key) -> Cell:
        return next((r for r in self.cells if r.col_key == key))


@dataclass
class Data:
    rows: List[Row]

    def __getitem__(self, key) -> Row:
        return next((r for r in self.rows if r.row_key == key))


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

    def __init__(self, id: str, columns: list[ColumnDefinition], type_to_select_column_key: str):
        super().__init__(id=id)
        self.type_to_select_column_key = type_to_select_column_key
        self._data: Data = Data(rows=[])
        self.columns = columns
        self.visible_columns_keys: List[str] = []
        self.table = DataTable(id="inner-table", cursor_type='row')
        self.type_to_select = TypeToSelect()
        self.marked_cells: Dict[str, Dict[str, Text]] = {}
        self.unmark_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield self.table

    def on_mount(self):
        self._recompute_columns()

    def on_resize(self, event: events.Resize):
        self._recompute_columns()

    def _on_focus(self, event: events.Focus) -> None:
        self.table.focus()

    def on_key(self, event: events.Key) -> None:
        if not event.character:
            return

        sequence = self.type_to_select.register_key_press(key=event.character).lower()

        from_idx = self.table.cursor_row + 1
        reordered_rows = self._data.rows[from_idx:] + self._data.rows[:from_idx]

        next_match_row_key = next((r.row_key
                                   for r in reordered_rows
                                   if self._find_in_cell(cell=r[self.type_to_select_column_key], sequence=sequence)),
                                  None)
        if next_match_row_key:
            self.select_row(row_key=next_match_row_key)

        self._invalidate_table()

        if self.unmark_timer:
            self.unmark_timer.stop()
        self.unmark_timer = self.set_timer(0.5, self._unmark_all_rows)

    def _unmark_all_rows(self):
        self.unmark_timer = None
        self.type_to_select.force_reset()
        self._invalidate_table()

    @staticmethod
    def _find_in_cell(cell: Cell, sequence: str) -> re.Match | None:
        text = cell.value.plain.lower()
        pattern = rf"(?<![A-Za-z0-9]){re.escape(sequence)}"
        return re.search(pattern, text)

    def _get_cell_widget(self, cell: Cell) -> Text:
        if cell.col_key != self.type_to_select_column_key:
            return cell.value

        typed_sequence = self.type_to_select.get_sequence()
        if not typed_sequence:
            return cell.value

        match = self._find_in_cell(cell=cell, sequence=typed_sequence)
        if not match:
            return cell.value

        new_widget = cell.value.copy()
        new_widget.stylize("underline", match.start(), match.end())
        return new_widget

    def update_table(self, data: Data):
        self._data = data
        self._invalidate_table(update_selection=True)

    def _invalidate_table(self, update_selection=False):
        for row in self._data.rows:
            relevant_sorted_cells = self._get_cells_to_insert(cells=row.cells)

            # update existing rows
            if self._is_row_in_table(row_key=row.row_key):
                for cell in relevant_sorted_cells:
                    widget = self._get_cell_widget(cell=cell)
                    current_widget = self.table.get_cell(row_key=row.row_key, column_key=cell.col_key)
                    if widget == current_widget:
                        continue
                    self.table.update_cell(row_key=row.row_key, column_key=cell.col_key, value=widget)

            # add missing rows
            else:
                self.table.add_row(*(self._get_cell_widget(cell=c) for c in relevant_sorted_cells), key=row.row_key)

        # remove unwanted rows
        rows_keys_to_remove = set([k.value for k in self.table.rows.keys()]) - set([r.row_key for r in self._data.rows])
        for row_key in rows_keys_to_remove:
            self.table.remove_row(row_key=row_key)

        # update selected row
        if update_selection:
            selected_row_key = next((r.row_key for r in self._data.rows if r.selected), None)
            if selected_row_key is not None:
                self.select_row(row_key=selected_row_key)

    def get_selected_row_index(self) -> int:
        return self.table.cursor_row

    def get_selected_row_key(self) -> str | None:
        if not self._data.rows:
            return None
        selected_key = self._data.rows[self.table.cursor_row].row_key
        return selected_key

    def select_row(self, row_key: str):
        row_idx = self.table.get_row_index(row_key=row_key)
        self.table.move_cursor(row=row_idx)

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
