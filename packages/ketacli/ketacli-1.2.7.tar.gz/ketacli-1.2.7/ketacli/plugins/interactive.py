"""
交互式命令模块
"""
from mando import command, arg
from rich.console import Console
from ketacli.sdk.chart.interactive_search import InteractiveSearch
from textual_serve.server import Server
import sys


console = Console()


@command
def isearch(page_size=10, overflow="fold", use_web=False, host="localhost", port=8000):
    """Interactive search

    :param --page_size: The page size of query result
    :param --overflow: The overflow mode, such as fold, crop, ellipsis, ignore
    :param --use_web: Whether to use web mode
    :param --host: The host to bind
    :param --port: The port to bind
    """
    try:
        if use_web:
            command = f"{sys.executable} -m ketacli isearch"
            server = Server(command, host=host, port=port, title="KetaOps Interactive Search")
            server.serve()
        else:
            isearch = InteractiveSearch(page_size=page_size, overflow=overflow)
            isearch.run()
    except Exception as e:
        console.print_exception()