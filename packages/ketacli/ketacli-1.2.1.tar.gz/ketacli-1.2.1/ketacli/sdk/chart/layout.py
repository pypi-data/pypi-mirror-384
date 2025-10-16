import sys
import time

from rich import print
from rich.layout import Layout
from ketacli.sdk.chart.base import PlotextMixin
from ketacli.sdk.chart.plot import Plot
from ketacli.sdk.chart.single_value import SingleValueChart
from ketacli.sdk.chart.table import KTable
from .base import BasePanelChart
from rich.console import Console
from rich.live import Live
from rich.text import Text
from ketacli.sdk.base.getch import get_key_sequence

console = Console()


class LayoutChart:

    def __init__(self, configs):
        if isinstance(configs, dict):
            self.configs = [configs]
        elif isinstance(configs, list):
            self.configs = configs
        self.layouts = []
        self.create_layout()
        self.index = 0
        self.last_panel_attr = {}
        self.is_showed = False
        self.child_layout_handler = False

    def create_layout(self):
        for config in self.configs:
            root = Layout(name=config.get("name", "root"), visible=True)
            layout_config = config.get("layout", {})
            rows = layout_config.get("rows", 1)
            cols = layout_config.get("columns", 1)
            configs = layout_config.get("configs", {})

            row_layouts = []
            for i in range(rows):
                row_layout = Layout(name=f"row{i}", **configs.get(f'row{i}', {}))
                row_layouts.append(row_layout)
                column_layouts = []
                for j in range(cols):
                    col_config = configs.get(f'row{i}-col{j}', {})
                    if col_config:
                        size = col_config.get("size", None)
                        ratio = col_config.get("ratio", None)
                        if not size and not ratio:
                            continue
                    column_layout = Layout(name=f"row{i}-col{j}", **col_config)
                    column_layouts.append(column_layout)
                row_layout.split_row(*column_layouts)
            root.split_column(*row_layouts)
            self.layouts.append(root)

    @staticmethod
    def create_chart(chart_config, theme=None):
        chart_type = chart_config.get("type", "table")
        if theme:
            chart_config.update(theme=theme)
        if chart_config.get('child'):
            subtitle = "Press SPACE for chart details"
        else:
            subtitle = "Press the SPACE to enlarge this chart"
        chart_config.update(subtitle=subtitle)
        chart = None

        if chart_type in ["line", "bar", "scatter"]:
            title = chart_config.get("title", "")
            plot = Plot(chart_config)
            chart = BasePanelChart(PlotextMixin(make_plot=plot.build), title=title,
                                   subtitle=Text(subtitle, justify="center", style="#808080"), )
        elif chart_type == "single":
            chart = SingleValueChart(chart_config)
        elif chart_type == "table":
            chart = KTable(chart_config)
            chart.search()
        return chart

    def refresh_layout(self, config, layout, live=None, theme=None):
        chart_configs = config.get("charts", [])
        layout_config = config.get("layout", {})
        for chart_config in chart_configs:
            if not theme:
                theme = config.get("theme", layout_config.get("theme", "dark"))
            chart = self.create_chart(chart_config, theme=theme)
            position = chart_config.get("position")
            if not position:
                raise ValueError("position is required")
            layout[position].update(chart)
            if live:
                live.refresh()
        layout.is_showed = True
        return layout

    def get_chart_for_layout(self, layout, name):
        for layout in layout._children:
            if layout._children and name in [ly.name for ly in layout._children]:
                return self.get_chart_for_layout(layout, name)
            if layout.name == name:
                return layout

    def highlight_chart(self, live, layout, configs, theme):
        new_layout = None
        while True:

            if not hasattr(layout, 'is_showed') or not layout.is_showed:
                # 首次进来先刷新仪表盘上的图表
                self.refresh_layout(configs, layout, live, theme)
                self.index = 0
                self.last_panel_attr = {}
                continue
            positions = [x['position'] for x in configs['charts']]

            key = get_key_sequence()
            with open('s.txt', 'w')as f:
                f.write(key)
            if new_layout:
                # 当存在子图表时，键盘事件交给子图表处理
                panel = new_layout.renderable
                key = panel.keyboard_handler(key)
                live.update(new_layout)
                self.child_layout_handler = True
            else:
                # 键盘事件交给仪表盘处理

                panel = self.get_chart_for_layout(layout, positions[self.index]).renderable
                key = panel.keyboard_handler(key)
                live.update(layout)
            if key is None:
                live.refresh()
                continue
            # panel = self.get_chart_for_layout(layout, positions[self.index]).renderable
            if key == '\t':
                # 切换选中图表
                last_panel = self.get_chart_for_layout(layout, positions[self.index - 1]).renderable
                last_panel.border_style = self.last_panel_attr.get('border_style', "none")
                if hasattr(last_panel, 'border_style'):
                    last_panel.border_style = self.last_panel_attr.get('border_style', "none")
                last_panel.title = self.last_panel_attr.get('title', last_panel.title)

                self.last_panel_attr['border_style'] = panel.border_style
                self.last_panel_attr['title'] = panel.title

                if panel is None:
                    print("No more charts")
                    return
                if hasattr(panel, 'border_style'):
                    panel.border_style = "red"
                panel.title = f"{panel.title} (Selected)"
                console.print("Highlight chart: ", positions[self.index])
                layout[positions[self.index]].update(panel)
                self.index += 1
            elif key == "\x03":
                live.stop()
                sys.exit()
            elif not self.child_layout_handler and (key == '\n' or key == '\r'):
                # 切换到下一个仪表盘
                break
            elif not self.child_layout_handler and key == " ":
                # 显示子图表或者放大图表
                panel = self.get_chart_for_layout(layout, positions[self.index - 1]).renderable
                if hasattr(panel, 'child') and panel.child:
                    panel = self.create_chart(panel.child, theme=theme)
                if hasattr(panel, 'subtitle'):
                    self.last_panel_attr['subtitle'] = panel.subtitle
                    panel.subtitle = "Press the ESC to return"
                new_layout = Layout(name="new_layout")
                new_layout.update(panel)
                live.update(new_layout)
            elif key == '\x1b\x1b':
                if new_layout:
                    # 退出子图表
                    panel = self.get_chart_for_layout(layout, positions[self.index - 1]).renderable
                    if hasattr(panel, 'subtitle'):
                        panel.subtitle = self.last_panel_attr.get('subtitle', panel.subtitle)
                    live.update(layout)
                    new_layout = None
                    self.child_layout_handler = False
                elif not new_layout and self.child_layout_handler:
                    self.child_layout_handler = False

                else:
                    live.stop()
                    sys.exit()

            if self.index == len(positions):
                self.index = 0
            live.refresh()

    def live(self, theme=None, interval=30, disable_auto_refresh=False):
        i = 0
        while True:
            with Live(self.layouts[i], refresh_per_second=1, auto_refresh=False) as _live:
                try:
                    # 使用 keyboard 库监听键盘事件
                    layout = self.layouts[i]
                    config = self.configs[i]
                    if disable_auto_refresh:
                        self.highlight_chart(_live, layout, config, theme)
                    else:
                        config = self.configs[i]
                        layout = self.layouts[i]
                        self.refresh_layout(config, layout, _live, theme)
                        time.sleep(interval)

                    i += 1
                    if i == len(self.configs):
                        i = 0
                except KeyboardInterrupt:
                    _live.stop()
                    sys.exit()


if __name__ == '__main__':
    configs = {
        "row0": {"size": 0, "ratio": 2},
        "row4": {"size": 0, "ratio": 3},
        "row0-col0": {"size": 0, "ratio": 2},
        "row1-col1": {"size": 0, "ratio": 1},
    }
