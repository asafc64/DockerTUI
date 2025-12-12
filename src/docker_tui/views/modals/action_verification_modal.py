from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Label, Button
from textual.widgets._button import ButtonVariant


class ActionVerificationModal(ModalScreen[bool]):
    DEFAULT_CSS = """
        ActionVerificationModal {
            align: center middle;
        }

        #dialog {
            grid-size: 2;
            grid-gutter: 1 2;
            grid-rows: 1fr 3;
            padding: 1 1;
            width: 60;
            height: 11;
            background: $surface;
        }

        #question {
            column-span: 2;
            height: 1fr;
            width: 1fr;
            content-align: center middle;
        }

        #yes, #no {
            content-align: center middle;
            width: 1fr;
            margin: 0 3;
        }
    """

    BINDINGS = [
        Binding("escape", "cancel", show=False),
        Binding("left", "swap_focus", show=False),
        Binding("right", "swap_focus", show=False),
    ]

    def __init__(self, title: str, button_text: str, button_variant: ButtonVariant):
        super().__init__()
        self.button_variant = button_variant
        self.button_text = button_text
        self.title = title

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.title, id="question"),
            Button(self.button_text, variant=self.button_variant, id="yes"),
            Button("Cancel", variant="default", id="no"),
            id="dialog",
        )

    def action_cancel(self):
        self.dismiss(False)

    def action_swap_focus(self):
        if self.query_one("#yes").has_focus:
            self.query_one("#no").focus()
        else:
            self.query_one("#yes").focus()

    def action_right_arrow(self):
        self.scroll_down()

    @on(Button.Pressed, "#yes")
    def handle_yes(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#no")
    def handle_no(self) -> None:
        self.dismiss(False)