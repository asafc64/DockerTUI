from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Static, TabbedContent, Footer

from services.containers_stats_monitor import ContainersStatsMonitor
from views.pages.containers_list_page import ContainersListPage
from views.pages.page import Page, HomePage
from views.shortcuts import Shortcuts


class TabbedApp(App):
    """An example of tabbed content."""

    CSS = """
        .header{
            dock: top;
        }
        #page-host{
            border: round $primary;
            border-title-style: bold;
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

    async def on_mount(self):
        self.show_page(page=ContainersListPage())
        ContainersStatsMonitor.instance().start()

    async def on_shutdown(self):
        await ContainersStatsMonitor.instance().close()

    def compose(self) -> ComposeResult:
        yield Shortcuts()
        with Container():
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
        self.query_one("#page-host").border_title = page.title
        self.current_page = page

if __name__ == "__main__":
    app = TabbedApp()
    app.run()