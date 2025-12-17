from dataclasses import dataclass
from typing import List, Any

from rapidfuzz import fuzz, utils
from rapidfuzz.distance import ScoreAlignment
from rich.columns import Columns
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList
from textual.widgets._option_list import Option


@dataclass
class SearchOption:
    text: str
    group: str
    group_priority: int
    id: str
    args: List[Any] = None


class SearchModal(ModalScreen[SearchOption]):
    @dataclass
    class OptionsGroup:
        name: str
        priority: int
        options: List[SearchOption]

    @dataclass
    class Match:
        option: SearchOption
        score: float
        start_idx: int
        end_idx: int

    DEFAULT_CSS = """
        SearchModal {
            align: center top;
        }
        #search-box {
            border: none;
            padding: 1 2;
        }
        #search-results {
            border: none;
            padding: 0;
            padding-top: 1;
        }
        #body {
            margin: 3;
            width: 60;
            layout: grid;
            grid-size: 1;
            grid-rows: auto 1fr;
        }
    """
    MAX_RESULTS = 100

    def __init__(self, options: List[SearchOption]):
        super().__init__()
        self.input = Input(id="search-box", placeholder="Search...")
        self.list_view = OptionList(id="search-results")
        self.list_view.can_focus = False
        self.all_options = options
        self.grouped_options = SearchModal.get_sorted_grouped_options(options)

    def compose(self) -> ComposeResult:
        with Container(id="body"):
            yield self.input
            yield self.list_view

    async def on_mount(self):
        await self.update_results("")

    @staticmethod
    def get_sorted_grouped_options(options: List[SearchOption]) -> List[OptionsGroup]:
        groups = {}
        for option in options:
            group = groups.get(option.group, None)
            if not group:
                group = SearchModal.OptionsGroup(name=option.group,
                                                 priority=option.group_priority,
                                                 options=[])
                groups[option.group] = group

            group.options.append(option)

        sorted_groups = list(sorted(groups.values(), key=lambda g: g.priority))
        return sorted_groups

    @on(Input.Changed)
    async def on_input_changed(self, event: Input.Changed) -> None:
        await self.update_results(event.value)

    async def update_results(self, text: str):
        grouped_matches: List[List[SearchModal.Match]] = []
        available_spots = self.MAX_RESULTS

        for group in self.grouped_options:
            matches = []
            for option in group.options:
                score_align = fuzz.partial_ratio_alignment(text, option.text, processor=utils.default_process,
                                                           score_cutoff=70) \
                    if text else ScoreAlignment(100, 0, 0, 0, 0)
                if score_align:
                    matches.append(SearchModal.Match(option=option, score=score_align.score,
                                                     start_idx=score_align.dest_start, end_idx=score_align.dest_end))
            if matches:
                matches_to_add = list(sorted(matches, key=lambda m: m.score))[:available_spots]
                grouped_matches.append(matches_to_add)
                available_spots -= len(matches_to_add)
            if available_spots <= 0:
                break

        renderable_options = []

        for matches in grouped_matches:
            for m in matches:
                primary = Text(" " + m.option.text, overflow="ellipsis")
                primary.stylize(style="blue", start=m.start_idx + 1, end=m.end_idx + 1)
                secondary = Text(m.option.group + " ", style="#888888", justify="right")
                renderable_options.append(Option(Columns([primary, secondary], expand=True), id=m.option.id))

            renderable_options.append(None)

        async with self.list_view.batch():
            self.list_view.clear_options()
            self.list_view.add_options(renderable_options)
            self.list_view.highlighted = 0

    def on_key(self, event: Key) -> None:
        if event.key == "down":
            self.list_view.highlighted += 1
        if event.key == "up":
            self.list_view.highlighted -= 1
        if event.key == "enter" and self.list_view.highlighted_option:
            option_id = self.list_view.highlighted_option.id
            # self.input.option_id = ""
            # self.input.insert_text_at_cursor(self.list_view.highlighted_option.id)
            event.prevent_default()
            event.stop()
            self.dismiss(next((o for o in self.all_options if o.id == option_id)))
        if event.key == "escape":
            event.prevent_default()
            event.stop()
            self.dismiss(None)
