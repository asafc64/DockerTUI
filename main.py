from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Static, TabbedContent, Footer

from views.pages.containers_list_page import ContainersListPage
from views.pages.page import Page, HomePage
from views.shortcuts import Shortcuts


class TabbedApp(App):
    """An example of tabbed content."""

    CSS = """
        .header{
            dock: top;
        }
        #page-title{
            dock: top;
            text-style: bold;
            color: ansi_bright_blue;
            border: solid ansi_bright_blue;
            padding: 0 1;
        }
        DataTable {
            height: 1fr;
            overflow-y: auto;
            width: 100%;
        }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", group=Binding.Group("Navigation")),
        Binding("escape", "back", "Back", group=Binding.Group("Navigation")),
        Binding("c", "show_tab('containers')", "Containers", group=Binding.Group("Navigation")),
        Binding("v", "show_tab('volumes')", "Volumes", group=Binding.Group("Navigation")),
        Binding("i", "show_tab('images')", "Images", group=Binding.Group("Navigation")),
    ]

    def __init__(self):
        super().__init__()
        self.current_page: Page = None

    def on_mount(self):
        self.show_page(page=ContainersListPage())

    def compose(self) -> ComposeResult:
        yield Shortcuts()
        with Container():
            yield Static(id="page-title")
            yield Container(id="page-host")

    def on_page_nav(self, nav: Page.Nav):
       self.show_page(page=nav.page)

    def action_back(self):
        if self.current_page.is_root_page:
            self.action_help_quit()
        else:
            self.current_page.nav_back()

    def show_page(self, page: Page):
        main = self.query_one("#page-host")
        main.remove_children()
        main.mount(page)
        self.query_one("#page-title").update("> "+page.title)
        self.current_page = page

if __name__ == "__main__":
    app = TabbedApp()
    app.run()