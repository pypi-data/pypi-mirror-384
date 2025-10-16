"""
可视化相关命令模块
"""
import os
import yaml
from datetime import datetime
from mando import command, arg
from rich.console import Console
from ketacli.sdk.chart.layout import LayoutChart
from ketacli.sdk.util import parse_url_params
import importlib.resources as pkg_resources

console = Console()


@command
def plot(spl, start=None, end=None, limit=100, interval=3.0,
         type="line", title=None, x_label="Time", y_label="Value", x_field="_time",
         y_field="value", group_field="", extra=None, theme=None, ):
    """plot chart of a single plot.

    :param spl: The spl query
    :param --start: The start time. Time format "2024-01-02 10:10:10"
    :param --end: The start time. Time format "2024-01-02 10:10:10"
    :param -l, --limit: The limit size of query result
    :param --interval: refresh the resource change
    :param -t, --type: plot type, line|bar|scatter
    :param --title: plot title
    :param --x_label: x label
    :param --y_label: y label
    :param -x, --x_field: x field
    :param -y, --y_field: y field
    :param -g, --group_field: group field
    :param -e, --extra: extra args, example:id=1234567890,name=test
    """
    if start is not None:
        start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
    if end is not None:
        end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
    if not title:
        title = spl
    extra_args_map = {}
    if extra:
        extra_args_map = parse_url_params(extra)

    config = {
        "layout": {
            "rows": 1,
            "columns": 1
        },
        "charts": [
            {
                "type": type,
                "title": title,
                "x_label": x_label,
                "y_label": y_label,
                "x_field": x_field,
                "y_field": y_field,
                "group_field": group_field,
                "plot_type": type,
                "extra_args": extra_args_map,
                "position": "row0-col0",
                "spl": spl,
                "start": start,
                "end": end,
                "limit": limit,
                "theme": theme,
                "interval": interval
            }
        ]
    }
    chart = LayoutChart(config)
    chart.live(interval=interval, theme=theme)


@command
@arg("chart", type=str, completer=lambda prefix, **kwd: [
    x.replace('.yaml', '').replace('.yml', '')
    for x in os.listdir(str(pkg_resources.files('ketacli').joinpath('charts'))) if x.startswith(prefix)
])
@arg("theme", type=str,
     completer=lambda prefix, **kwd: [
         x for x in ["default", "dark", "clear", "pro", "matrix", "windows",
                     "retro", "elegant", "mature", "dreamland", "grandpa",
                     "salad", "girly", "serious", "sahara", 'scream'] if x.startswith(prefix)
     ])
def dashboard(chart=None, file_path=None, interval=30, theme="", disable_auto_refresh=True):
    """plot dashboard from yaml file

    :param -c, --chart: The chart name, such as monitor
    :param -f, --file_path: The file path
    :param --interval: refresh the chart change, default 30s
    :param --theme: setting the theme, such as default|dark|clear|pro|matrix|windows|retro|elegant|mature|dreamland|grandpa|salad|girly|serious|sahara|scream
    :param -d, --disable_auto_refresh: auto refresh the chart change
    """
    if file_path is None and chart is None:
        console.print(f"Please specify file path with --file or --chart")
        return
    if chart is not None:
        file_path = str(pkg_resources.files('ketacli').joinpath('charts', f"{chart}.yaml"))
    config = yaml.safe_load(open(file_path, encoding="utf-8"))
    chart = LayoutChart(config)
    chart.live(interval=interval, theme=theme, disable_auto_refresh=disable_auto_refresh)