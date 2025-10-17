from rich.table import Text
from rich.panel import Panel
from .base import BaseChart


class NoDataChart(BaseChart):
    def __init__(self, title=None, **kwargs):
        self.title = title
        self.border_style = ""
        self.subtitle = kwargs.pop("subtitle", "")

    def __rich_console__(self, console, options):
        width = options.max_width or console.width
        self.height = options.height or console.height
        texts = ((f"No data for chart \"{self.title}\"", "bold yellow"),)
        padding = (self.height - 4) // 2
        panel = Panel(Text.assemble(*texts, justify="center"), expand=True, padding=padding,
                      title=self.title, height=self.height, border_style=self.border_style,
                      subtitle=Text(self.subtitle, justify="center", style="#808080"), )

        yield panel


if __name__ == '__main__':
    from rich.console import Console

    console = Console()
    console.print(NoDataChart(title="title", ))
