from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from textual import work
from textual.app import ComposeResult
from textual.widget import Widget
from textual_plotext import PlotextPlot


class TimeSeriesPlot(Widget):

    DEFAULT_CSS = """
            TimeSeriesPlot{
                border: blank $primary;
                border-title-style: bold;
                # background: $surface;
            }
        """

    def __init__(self, *, id: str | None = None, classes: str | None = None,):
        super().__init__(id=id, classes=classes)
        self.plotext = PlotextPlot(id="plot-host")
        self.plt = self.plotext.plt
        self.plt.canvas_color("none")
        self.plt.axes_color("none")
        self.plt.ticks_color("none")
        self.plt.date_form("d/m/Y H:M:S", output_form="H:M:S")

    def compose(self) -> ComposeResult:
        yield self.plotext

    def on_mount(self) -> None:
        self.add_data()
        self.set_interval(1, self.add_data)

    def add_data(self):
        self.plt.clear_data()

        (xs,ys) = self.get_data()

        self.plt.plot([y.strftime("%d/%m/%Y %H:%M:%S") for y in ys], [x for x in xs])
        self.plotext.refresh()

    @abstractmethod
    def get_data(self) -> (List[float], List[datetime]):
        raise NotImplementedError()