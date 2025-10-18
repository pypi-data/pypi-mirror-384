"""
配置相关命令模块
"""
import importlib.metadata
from mando import command, arg
from rich.console import Console
from ketacli.sdk.base.config import list_clusters, set_default_cluster, delete_cluster
from ketacli.sdk.request.asset_map import get_resources
from ketacli.sdk.output.output import list_output, rs_output_all, rs_output_one
from ketacli.sdk.output.format import format_table

console = Console()


@command
@arg('type', type=str, completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
def rs(type=None, format="table"):
    """Show resource info

    :param -t, --type: The target asset type, such as repo, sourcetype ...
    :param -f, --format: The output format, text, json ...
    """
    resources = get_resources()
    if type is None:
        table = rs_output_all(resources)
    else:
        table = rs_output_one(type, resources.get(type))
    console.print(format_table(table, format=format), overflow="fold")


@command
@arg('name', '-n', '--name', type=str,
     completer=lambda prefix, **kwd: [x['name'] for x in list_clusters() if x['name'].startswith(prefix)])
@arg('operation', type=str,
     completer=lambda prefix, **kwd: [x for x in ['list-clusters', 'set-default', 'delete-cluster'] if
                                      x.startswith(prefix)])
def config(operation, name=None):
    """Show keta cluster info

    :param operation: The target operation, such as list-clusters, set-default, delete-cluster
    :param -n, --name: setting or delete default cluster
    """
    resp = []
    if operation not in ["list-clusters", "set-default", "delete-cluster"]:
        console.print(f"Please specify operation, such as list-clusters, set-default, delete-cluster", style="red")
        return
    if operation == "list-clusters":
        resp = list_clusters()
    elif operation == "set-default":
        resp = set_default_cluster(name)
    elif operation == "delete-cluster":
        resp = delete_cluster(name)
    if not resp:
        console.print("No response")
        exit()
    table = list_output('cluster', [], resp=resp)
    console.print(format_table(table, "table"), overflow="fold")


@command
def version():
    _version = importlib.metadata.version('ketacli')
    console.print(_version, overflow="fold")