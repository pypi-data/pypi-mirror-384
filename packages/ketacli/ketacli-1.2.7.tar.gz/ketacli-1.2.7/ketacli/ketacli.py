import argcomplete
from mando import main

# 导入所有插件模块
from ketacli.plugins import auth
from ketacli.plugins import asset
from ketacli.plugins import search
from ketacli.plugins import visualization
from ketacli.plugins import data
from ketacli.plugins import config
from ketacli.plugins import interactive
from ketacli.plugins import metric

# 导入mock模块中的函数
from ketacli.plugins.mock import mock_data, mock_log, mock_metrics, generate_and_upload

# 导入测试模块
from ketacli.sdk.test.cli import test_command

# 导入AI模块
from ketacli.plugins.ai_search import *


def start():
    # 确保main被正确初始化
    import argcomplete
    argcomplete.autocomplete(main.parser)
    try:
        argcomplete.autocomplete(main.parser)
        main()
    except Exception:
        from rich.console import Console
        console = Console()
        console.print_exception()


if __name__ == "__main__":
    start()
