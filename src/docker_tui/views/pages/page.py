from abc import ABC

from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static


class Page(Widget):
    can_focus = True
    is_root_page = False
    class Nav(Message):
        def __init__(self, page: "Page"):
            self.page = page
            super().__init__()

    def __init__(self, title: str):
        super().__init__()
        self.title = title

    def on_mount(self):
        self.focus()

    def nav_to(self, page: "Page"):
        self.post_message(self.Nav(page))

    def nav_back(self):
        pass





class HomePage(Page):

    def __init__(self):
        super().__init__(title="Home")
    def compose(self):
        yield Static("🏠 Home Page", id="page")

class SettingsPage(Page):
    def compose(self):
        yield Static("⚙️ Settings Page", id="page")

