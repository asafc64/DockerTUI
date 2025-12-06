from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Markdown, TabbedContent, TabPane, Tabs

from views.containers_list_tab_pane import ContainersListTabPane
from views.shortcuts import Shortcuts

ROWS = [
    ("lane", "swimmer", "country", "time"),
    (4, "Joseph Schooling", "Singapore", 50.39),
    (2, "Michael Phelps", "United States", 51.14),
    (5, "Chad le Clos", "South Africa", 51.14),
    (6, "László Cseh", "Hungary", 51.14),
    (3, "Li Zhuhao", "China", 51.26),
    (8, "Mehdy Metella", "France", 51.58),
    (7, "Tom Shields", "United States", 51.73),
    (1, "Aleksandr Sadovnikov", "Russia", 51.84),
    (10, "Darren Burns", "Scotland", 51.84),
]

LETO = """
# Duke Leto I Atreides

Head of House Atreides.
"""

JESSICA = """
# Lady Jessica

Bene Gesserit and concubine of Leto, and mother of Paul and Alia.
"""

PAUL = """
# Paul Atreides

Son of Leto and Jessica.
"""


class TabbedApp(App):
    """An example of tabbed content."""

    CSS = """
        .header{
            dock: top
        }
        DataTable {
            height: 1fr;
            overflow-y: auto;
            width: 100%;
        }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("c", "show_tab('containers')", "Containers", group=Binding.Group("Navigation")),
        Binding("v", "show_tab('volumes')", "Volumes", group=Binding.Group("Navigation")),
        Binding("i", "show_tab('images')", "Images", group=Binding.Group("Navigation")),
    ]

    def compose(self) -> ComposeResult:
        """Compose app with tabbed content."""
        # Footer to show keys
        yield Footer()

        # yield Static("Hello, world!", classes="header")

        yield Shortcuts()
        # yield Header()

        # Add the TabbedContent widget
        with TabbedContent(initial="containers", classes="tabs", id="body"):
            yield ContainersListTabPane()
            with TabPane("Volumes", id="volumes"):
                yield Markdown(LETO)
            with TabPane("Images", id="images"):
                yield Markdown(PAUL)

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab

    def on_tabbed_content_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Called when a tab is activated."""
        if hasattr(event.pane, "load_data"):
            event.pane.load_data()

if __name__ == "__main__":
    app = TabbedApp()
    app.run()