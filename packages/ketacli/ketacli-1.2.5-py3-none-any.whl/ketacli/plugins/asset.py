"""
资产管理相关命令模块
"""
import json
import sys
import time
from mando import command, arg
from rich.console import Console
from rich.live import Live
from ketacli.sdk.base.client import request_get, request, download_file
from ketacli.sdk.request.list import list_assets_request, list_admin_request
from ketacli.sdk.request.get import get_asset_by_id_request
from ketacli.sdk.request.create import create_asset_request
from ketacli.sdk.request.update import update_asset_request
from ketacli.sdk.request.delete import delete_asset_request
from ketacli.sdk.request.export import export_asset_request
from ketacli.sdk.request.asset_map import get_resources
from ketacli.sdk.output.output import list_output, describe_output, get_asset_output
from ketacli.sdk.output.format import format_table
from ketacli.sdk.util import parse_url_params
from ketacli.sdk.test.cli import test_command

console = Console(markup=False)


@command('list')
@arg("format", type=str,
     completer=lambda prefix, **kwd: [x for x in ["table", "text", "json", "csv", "html", "latex"] if
                                      x.startswith(prefix)])
@arg("asset_type", type=str,
     completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
def _list(asset_type, groupId=-1, order="desc", pageNo=1, pageSize=10, prefix="", sort="updateTime", fields="",
          format=None, raw=False, lang=None, extra=None, watch=False, interval=3.0, show_all_fields=False, test=False):
    """List asset (such as repo,sourcetype,metric...) from ketadb

    :param asset_type: The asset type such as repo, sourcetype, metirc, targets ...
    :param -l, --pageSize: Limit the page size.
    :param --pageNo: Limit the page number.
    :param --prefix: Fuzzy query filter.
    :param --sort: The field used to order by
    :param --order: The sort order, desc|asc
    :param --fields: The fields to display. Separate by comman, such as "id,name,type"
    :param -f, --format: The output format, text|json|csv|html|latex
    :param --groupId: The resource group id.
    :param --raw: Prettify the time field or output the raw timestamp, if specified, output the raw format
    :param --lang: Choose the language preference of return value
    :param -e, --extra: extra query filter, example: include_defaults=true,flat_settings=true
    :param -w, --watch: Watch the resource change
    :param --interval: refresh the resource change
    :param -a, --show_all_fields: all fields to display
    :param --test: Enable test mode for assertion control
    """
    extra_dict = {}
    if extra is not None:
        # 解析 url 参数为 dict
        extra_dict = parse_url_params(extra)

    def generate_table():
        req = list_assets_request(
            asset_type, groupId, order, pageNo, pageSize, prefix, sort, lang, **extra_dict)
        resp = request_get(req["path"], req["query_params"],
                           req["custom_headers"]).json()
        output_fields = req.get("default_fields", [])
        field_aliases = req.get("field_aliases", {})
        field_converters = req.get("field_converters", {})
        if show_all_fields:
            output_fields = []
        if len(fields.strip()) > 0:
            output_fields = fields.strip().split(",")
        table = list_output(asset_type, output_fields=output_fields, resp=resp, field_aliases=field_aliases, field_converters=field_converters)
        if not table:
            return None
        return format_table(table, format, not raw)

    # 测试模式逻辑
    if test:
        from types import SimpleNamespace
        args = SimpleNamespace()
        args.action = "run"
        args.asset_type = asset_type
        args.method = "list"
        args.params = {"groupId": groupId, "order": order, "pageNo": pageNo, "pageSize": pageSize, 
                      "prefix": prefix, "sort": sort, "fields": fields, "lang": lang}
        args.suite_file = None
        args.config_file = None
        args.format = "console"
        args.output = None
        test_command(args)
        return

    if watch:
        with Live(generate_table(), console=console, refresh_per_second=1) as live:
            while True:
                try:
                    table = generate_table()
                    live.update(table)
                    time.sleep(interval)
                except KeyboardInterrupt:
                    live.stop()
                    sys.exit()
    else:
        table = generate_table()
        if table is None:
            console.print(f"we cannot find any {asset_type}")
        else:
            console.print(table, overflow="fold")


@command
@arg("format", type=str,
     completer=lambda prefix, **kwd: [x for x in ["table", "text", "json", "csv", "html", "latex"] if
                                      x.startswith(prefix)])
def admin(asset_type, format="json", extra=None, watch=False, interval=3.0):
    """List asset (such as repo,sourcetype,metric...) from ketadb

    :param asset_type: The asset type such as repo, sourcetype, metirc, targets ...
    :param -f, --format: The output format, text|json|csv|html|latex
    :param -e, --extra: extra query filter, example: include_defaults=true,flat_settings=true
    :param -w, --watch: Watch the resource change
    :param --interval: refresh the resource change
    """
    extra_dict = {}
    if extra is not None:
        # 解析 url 参数为 dict
        extra_dict = parse_url_params(extra)

    def generate_table():
        req = list_admin_request(asset_type, **extra_dict)
        resp = request_get(req["path"], req["query_params"], req["custom_headers"]).json()
        output_fields = []
        table = list_output(asset_type, output_fields=output_fields, resp=resp)
        return format_table(table, format)

    if watch:
        with Live(generate_table(), console=console, refresh_per_second=1) as live:
            while True:
                try:
                    table = generate_table()
                    live.update(table)
                    time.sleep(interval)
                except KeyboardInterrupt:
                    live.stop()
                    sys.exit()
    else:
        table = generate_table()
        if table is None:
            console.print(f"we cannot find any {asset_type}")
        else:
            console.print(table)


@command
@arg("format", type=str,
     completer=lambda prefix, **kwd: [x for x in ["table", "text", "json", "csv", "html", "latex"] if
                                      x.startswith(prefix)])
@arg("asset_type", type=str,
     completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
def get(asset_type, asset_id, fields="", format=None, lang=None, extra=None):
    """Get asset detail info from ketadb

    :param asset_type: The asset type such as repo, sourcetype, metirc, targets ...
    :param asset_id: The unique id of asset. (such as id or name...)
    :param --fields: The fields to display. Separate by comman, such as "id,name,type"
    :param -f, --format: The output format, text|json|csv|html|latex
    :param --lang: Choose the language preference of return value
    :param -e, --extra: extra args, example:id=1234567890,name=test
    """
    if extra:
        extra_args_map = parse_url_params(extra)
    else:
        extra_args_map = {}
    extra_args_map['name'] = asset_id

    req = get_asset_by_id_request(
        asset_type=asset_type, asset_id=asset_id, lang=lang, **extra_args_map)
    resp = request_get(req["path"], req["query_params"],
                       req["custom_headers"]).json()
    if format == "json":
        console.print(json.dumps(resp, indent=2, ensure_ascii=False), markup=False)
        return

    output_fields = []
    if len(fields.strip()) > 0:
        output_fields = fields.strip().split(",")
    table = get_asset_output(output_fields=output_fields, resp=resp)
    table.align = "l"
    if table is None:
        console.print(f"we cannot find any {asset_type}")
    else:
        console.print(format_table(table, format), overflow="fold")


@command
@arg("format", type=str,
     completer=lambda prefix, **kwd: [x for x in ["table", "text", "json", "csv", "html", "latex"] if
                                      x.startswith(prefix)])
@arg("asset_type", type=str,
     completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
def describe(asset_type, format=None):
    """Describe the schema of asset type

    :param asset_type: The asset type such as repo, sourcetype, metirc, targets ...
    :param -f, --format: The output format, text|json|csv|html|latex
    """
    req = list_assets_request(asset_type)
    resp = request_get(req["path"], req["query_params"],
                       req["custom_headers"]).json()
    table = describe_output(asset_type, resp=resp)
    if table is None:
        console.print(f"we cannot find any {asset_type}")
    else:
        console.print(format_table(table, format), overflow="fold")


@command
@arg("asset_type", type=str,
     completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
def create(asset_type, name=None, data=None, file=None, extra=None, test=False):
    """Create asset

    :param asset_type: The target asset type, such as repo, sourcetype ...
    :param -n, --name: The target asset name
    :param --data: The json string data {...}
    :param --file: Upload json text from file path.
    :param -e, --extra: extra args, example:id=1234567890,name=test
    :param --test: Enable test mode for assertion control
    """
    if data is None and file is None:
        content = {}
    else:
        content = data
        if file is not None:
            f = open(file, encoding="utf-8")
            content = f.read()
        try:
            content = json.loads(content)
        except json.JSONDecodeError as e:
            console.print("JSON 解析错误:", e)
            return
    if extra:
        extra_args_map = parse_url_params(extra)
    else:
        extra_args_map = {}
    for k, v in extra_args_map.items():
        if str(v).startswith('@'):
            c = open(v[1:], encoding="utf-8").read().replace("\n", "\\n").replace("\"", "\\\"")
            extra_args_map[k] = c
    if 'name' in extra_args_map:
        name = extra_args_map.pop('name')
    
    # 测试模式逻辑
    if test:
        from types import SimpleNamespace
        args = SimpleNamespace()
        args.action = "run"
        args.asset_type = asset_type
        args.method = "create"
        args.params = {"name": name, "data": content}
        if extra_args_map:
            args.params.update(extra_args_map)
        args.suite_file = None
        args.config_file = None
        args.format = "console"
        args.output = None
        test_command(args)
        return

    try:
        req = create_asset_request(asset_type, name, content, **extra_args_map)
        resp = request(req["method"], req["path"], data=req['data']).json()
        console.print(json.dumps(resp, ensure_ascii=False), overflow="fold", markup=False)
    except Exception as e:
        console.print(f"create asset {name} failed, error: {e}")


def get_operation_type(prefix, **kwargs):
    operators = []
    for x in get_resources():
        if x == kwargs.get('parsed_args').asset_type:
            methods = get_resources()[x].get('methods')
            operators = methods.keys()
    operators = [x for x in operators if
                 x not in ['list', 'create', 'update', 'delete', 'download', 'get'] and x.startswith(prefix)]
    return operators


@arg("asset_type", type=str,
     completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
@command
@arg("operation", type=str, completer=get_operation_type)
def update(asset_type, name=None, operation="update", data=None, file=None, extra=None, test=False):
    """Update asset

    :param asset_type: The target asset type, such as repo, sourcetype ...
    :param -n, --name: The target asset name
    :param -d, --data: The json string data {...}
    :param -f, --file: Upload json text from file path.
    :param -o, --operation: operation type, such as open, close, update, delete
    :param -e, --extra: extra args, example:id=1234567890,name=test
    :param --test: Enable test mode for assertion control
    """
    if data is None and file is None:
        data = {}
    else:
        content = data
        if file is not None:
            f = open(file, encoding="utf-8")
            content = f.read()

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            console.print("JSON 解析错误:", e)
            return
    if extra:
        extra_args_map = parse_url_params(extra)
    else:
        extra_args_map = {}
    if 'name' in extra_args_map:
        name = extra_args_map.pop('name')
    
    # 测试模式逻辑
    if test:
        from types import SimpleNamespace
        args = SimpleNamespace()
        args.action = "run"
        args.asset_type = asset_type
        args.method = "update"
        args.params = {"name": name, "operation": operation, "data": data}
        if extra_args_map:
            args.params.update(extra_args_map)
        args.suite_file = None
        args.config_file = None
        args.format = "console"
        args.output = None
        test_command(args)
        return
    
    req = update_asset_request(asset_type, operation, name, data, **extra_args_map)
    resp = request(req["method"], req["path"], data=req['data']).json()
    console.print(resp, overflow="fold")


@command
@arg("asset_type", type=str,
     completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
def download(asset_type, extra=None, base_path="./"):
    """export file asset

    :param asset_type: The target asset type, such as repo, sourcetype ...
    :param -e, --extra: extra args, example:id=1234567890,name=test
    :param --base_path: the file save path
    """
    if extra:
        extra_args_map = parse_url_params(extra)
    else:
        extra_args_map = {}

    req = export_asset_request(asset_type, **extra_args_map)
    download_file(req["path"], save_path=base_path)


@command
@arg("asset_type", type=str,
     completer=lambda prefix, **kwd: [x for x in get_resources().keys() if x.startswith(prefix)])
def delete(asset_type, name=None, data=None, file=None, extra=None, test=False):
    """Delete asset

    :param --asset_type: The target asset type, such as repo, sourcetype ...
    :param -n, --name: The target asset name or id
    :param -d, --data: The json string data {...}
    :param -f, --file: Upload json text from file path.
    :param -e, --extra: extra args, example:id=1234567890,name=test
    :param --test: Enable test mode for assertion control
    """
    if data is None and file is None:
        data = {}
    else:
        content = data
        if file is not None:
            f = open(file, encoding="utf8")
            content = f.read()

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            console.print("JSON 解析错误:", e)
            return

    if extra:
        extra_args_map = parse_url_params(extra)
    else:
        extra_args_map = {}
    if 'name' in extra_args_map:
        name = extra_args_map.pop('name')

    # 测试模式逻辑
    if test:
        from types import SimpleNamespace
        args = SimpleNamespace()
        args.action = "run"
        args.asset_type = asset_type
        args.method = "delete"
        args.params = {"name": name, "data": data}
        if extra_args_map:
            args.params.update(extra_args_map)
        args.suite_file = None
        args.config_file = None
        args.format = "console"
        args.output = None
        test_command(args)
        return

    req = delete_asset_request(asset_type, name, data, **extra_args_map)
    resp = request(req["method"], req["path"], data=req['data']).json()
    console.print(resp, overflow="fold")