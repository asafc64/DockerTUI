from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container

from docker_tui.services.containers_stats_monitor import ContainersStatsMonitor
from docker_tui.services.images_provider import ImagesProvider
from docker_tui.views.modals.search_modal import SearchModal, SearchOption
from docker_tui.views.pages.container_details_page import ContainerDetailsPage
from docker_tui.views.pages.container_log_page import ContainerLogPage
from docker_tui.views.pages.containers_list_page import ContainersListPage
from docker_tui.views.pages.image_list_page import ImageListPage
from docker_tui.views.pages.page import Page
from docker_tui.views.shortcuts import Shortcuts


class DockerTuiApp(App):
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
        Binding("s", "search", "Search", group=Binding.Group("Navigation")),
        # Binding("c", "show_tab('containers')", "Containers", group=Binding.Group("Navigation")),
        # Binding("v", "show_tab('volumes')", "Volumes", group=Binding.Group("Navigation")),
        # Binding("i", "show_tab('images')", "Images", group=Binding.Group("Navigation")),
    ]

    def __init__(self):
        super().__init__()
        self.current_page: Page = None

    async def on_mount(self):
        # self.show_page(page=ContainersListPage())
        self.show_page(page=ImageListPage())
        ContainersStatsMonitor.instance().start()
        ImagesProvider.instance().start()

    async def on_shutdown(self):
        await ContainersStatsMonitor.instance().close()
        await ImagesProvider.instance().close()

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

    @work
    async def action_search(self):
        # Pages
        options = [
            SearchOption("Containers", "Page", 1, "goto_containers_list"),
            SearchOption("Images", "Page", 1, "goto_images_list"),
        ]

        # Containers
        try:
            containers = ContainersStatsMonitor.instance().get_all_containers()
        except:
            containers = []
        for c in containers:
            options.append(SearchOption(c.name, "Container > List", 2, f"goto_container_row_{c.id}", [c.id]))
            options.append(SearchOption(c.name, "Container > Info", 3, f"goto_container_info_{c.id}", [c.id, c.name]))
            options.append(SearchOption(c.name, "Container > Logs", 4, f"goto_container_logs_{c.id}", [c.id, c.name]))

        # Images
        try:
            images = ImagesProvider.instance().get_images()
        except:
            images = []
        for i in images:
            options.append(SearchOption(i.name, "Image > List", 5, f"goto_image_row_{i.id}", [i.id]))

        selected = await self.push_screen_wait(SearchModal(options=options))
        if not selected:
            return

        if selected.id == "goto_containers_list":
            self.show_page(ContainersListPage())

        if selected.id == "goto_images_list":
            self.show_page(ImageListPage())

        if selected.id.startswith("goto_container_row"):
            container_id = selected.args[0]
            self.show_page(ContainersListPage(select_container_id=container_id))

        if selected.id.startswith("goto_container_info"):
            container_id = selected.args[0]
            container_name = selected.args[1]
            self.show_page(ContainerDetailsPage(container_id=container_id, container_name=container_name))

        if selected.id.startswith("goto_container_logs"):
            container_id = selected.args[0]
            container_name = selected.args[1]
            self.show_page(ContainerLogPage(container_id=container_id, container_name=container_name))

    def show_page(self, page: Page):
        main = self.query_one("#page-host")
        main.remove_children()
        main.mount(page)
        self.query_one("#page-host").border_title = page.title
        self.current_page = page

def main():
    app = DockerTuiApp()
    app.run()

if __name__ == "__main__":
    main()