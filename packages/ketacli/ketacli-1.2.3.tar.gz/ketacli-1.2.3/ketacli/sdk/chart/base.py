from rich.jupyter import JupyterMixin
from rich.ansi import AnsiDecoder
from rich.console import Group
from rich.panel import Panel
from rich.text import Text


class BaseChart:
    title = ""
    subtitle = ""
    border_style = ""

    def keyboard_handler(self, key):
        return key

    def nodata_panel(self, console, options):
        width = options.max_width or console.width
        height = options.height or console.height
        texts = ((f"No data for chart \"{self.title}\"", "bold yellow"),)
        padding = (height - 4) // 2
        panel = Panel(Text.assemble(*texts, justify="center"), expand=True, padding=padding,
                      title=self.title, height=height, border_style=self.border_style,
                      subtitle=Text(self.subtitle, justify="center", style="#808080"), )

        return panel


class BasePanelChart(Panel):
    def keyboard_handler(self, key):
        return key


class PlotextMixin(BaseChart):
    def __init__(self, phase=0, title="", make_plot=None):
        self.decoder = AnsiDecoder()
        self.phase = phase
        self.title = title
        self.make_plot = make_plot
        self.subtitle = ""

    def __rich_console__(self, console, options):
        self.width = options.max_width or console.width
        self.height = options.height or console.height
        canvas = self.make_plot(self.width, self.height)
        if not canvas:
            yield self.nodata_panel(console, options)
            return
        self.rich_canvas = Group(*self.decoder.decode(canvas))
        yield self.rich_canvas
