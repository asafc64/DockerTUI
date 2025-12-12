from datetime import datetime
from typing import List

from docker_tui.services.containers_stats_monitor import ContainersStatsMonitor
from docker_tui.views.components.time_series_plot import TimeSeriesPlot


class ContainerMemoryUsagePlot(TimeSeriesPlot):

    def __init__(self, *, container_id: str, id: str | None = None, classes: str | None = None,):
        super().__init__(id=id, classes=classes)
        self.container_id = container_id

    def get_data(self) -> (List[float], List[datetime]):
        try:
            stats = ContainersStatsMonitor.instance().get_stats(container_id=self.container_id)
        except:
            stats = None
        if not stats:
            self.border_title = f"Memory Usage - <No Data>%"
            return [], []

        self.border_title = f"Memory Usage - {stats.memory_usage[-1].value:.2f} MB"
        return [p.value for p in stats.memory_usage], [p.timestamp for p in stats.memory_usage]
