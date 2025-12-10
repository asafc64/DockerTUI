from abc import ABC
from dataclasses import dataclass
from itertools import groupby
from typing import List, Callable, Any

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
    type: str
    type_priority: int
    id: str
    args: List[Any] = None

class SearchModal(ModalScreen[SearchOption]):
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
        }
        #body {
            margin: 3;
            width: 60;
            layout: grid;
            grid-size: 1;
            grid-rows: auto 1fr;
        }
    """

    def __init__(self, options: List[SearchOption]):
        super().__init__()
        self.input = Input(id="search-box", placeholder="Search...")
        self.list_view = OptionList(id="search-results")
        self.list_view.can_focus = False
        self.options = options

    def compose(self) -> ComposeResult:
        with Container(id="body"):
            yield self.input
            yield self.list_view

    @dataclass
    class Match:
        option: SearchOption
        score: ScoreAlignment

    @on(Input.Changed)
    async def on_input_changed(self, event: Input.Changed) -> None:

        matches: List[SearchModal.Match] = []

        for option in self.options:
            score_align = fuzz.partial_ratio_alignment(event.value, option.text, processor=utils.default_process, score_cutoff=70)
            if score_align:
                matches.append(SearchModal.Match(option=option, score=score_align))

        matches_by_type = {}
        for m in matches:
            matches_by_type.setdefault(m.option.type_priority, []).append(m)

        renderable_options = []

        for (_, grouped_matches) in sorted(matches_by_type.items(), key=(lambda g: g[0])):
            for m in grouped_matches:
                primary = Text(" " + m.option.text, overflow="ellipsis")
                primary.stylize(style="blue", start=m.score.dest_start + 1, end=m.score.dest_end + 1)
                secondary = Text(m.option.type + " ", style="#888888", justify="right")
                renderable_options.append(Option(Columns([primary, secondary], expand=True), id=m.option.id))
            renderable_options.append(None)
            
        # for m in sorted(matches, key=(lambda x: x.score.score), reverse=True):
        #     primary = Text(" " + m.option.text, overflow="ellipsis")
        #     primary.stylize(style="blue", start=m.score.dest_start + 1, end=m.score.dest_end + 1)
        #     secondary = Text(m.option.type + " ", style="#888888", justify="right")
        #     renderable_options.append(Option(Columns([primary,secondary], expand=True), id=m.option.id))

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
            self.dismiss(next((o for o in self.options if o.id == option_id)))
        if event.key == "escape":
            event.prevent_default()
            event.stop()
            self.dismiss(None)