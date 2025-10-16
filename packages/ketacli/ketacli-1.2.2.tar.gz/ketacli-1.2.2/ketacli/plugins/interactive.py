"""
交互式命令模块
"""
from mando import command, arg
from rich.console import Console
from ketacli.sdk.chart.interactive_search import InteractiveSearch

console = Console()


@command
def isearch(page_size=10, overflow="fold"):
    """Interactive search

    :param --page_size: The page size of query result
    :param --overflow: The overflow mode, such as fold, crop, ellipsis, ignore
    """
    try:
        isearch = InteractiveSearch(page_size=page_size, overflow=overflow)
        isearch.run()
    except Exception as e:
        console.print_exception()