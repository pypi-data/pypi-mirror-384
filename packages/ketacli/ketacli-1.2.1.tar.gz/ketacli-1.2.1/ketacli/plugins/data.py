"""
数据操作相关命令模块
"""
import json
from mando import command
from rich.console import Console
from ketacli.sdk.base.client import request_post

console = Console()


@command
def insert(repo="default", data=None, file=None):
    """Upload data to specified repo

    :param --repo: The target repo
    :param --data: The json string data [{"raw":"this is text", "host": "host-1"}]
    :param --file: Upload json text from file path.
    """
    if repo is None:
        console.print(f"Please specify target repo with --repo")
        return
    if data is None and file is None:
        console.print(f"Please use --data or --file to specify data to upload")
        return

    if file is not None:
        f = open(file, encoding="utf-8")
        data = f.read()

    query_params = {
        "repo": repo,
    }
    resp = request_post("data", json.loads(data), query_params).json()
    console.print(resp, overflow="fold", markup=False)