import json

from datetime import datetime
from .format import make_records_to_table, make_table, make_table, prettify_value
from ..util import is_fuzzy_key
from ..base.client import ROOT_PATH

RESP_OUTPUT_KEY = {
    "bizsystems": "items",
    "target": "items",
    "targettype": "items",
}


def find_list_field(resp=None):
    """找寻返回结果中的list类型字段，用来查找分页返回结果中应该处理字段的函数

    Args:
        resp (dict, optional): 分页返回结果. Defaults to {}.

    Returns:
        str | None: 第一个list类型字段的key，如果没有则返回None
    """
    if resp is None:
        resp = {}
    if not isinstance(resp, dict):
        return
    for k in resp:
        if isinstance(resp[k], list):
            return k
    return None


def find_result_field(asset_type, resp=None):
    # 检查白名单有无这个字段的定义，如果有，则直接使用
    if resp is None:
        resp = {}
    real_asset_key = is_fuzzy_key(asset_type, value_map=RESP_OUTPUT_KEY)
    if real_asset_key is not None:
        return RESP_OUTPUT_KEY.get(real_asset_key)

    if isinstance(resp, list):
        return None
    # 优先查看返回结果里是否有类似命名的字段
    key = is_fuzzy_key(asset_type, value_map=resp)

    # 如果最终没有找到类似的字段，则找一个list字段
    if key is None:
        key = find_list_field(resp)

    # 如果返回结果为空
    if key is None or not isinstance(resp[key], list) or len(resp[key]) <= 0:
        return None

    return key


def flatten_dict(dictionary, prefix='', result_list=None):
    if result_list is None:
        result_list = {}
    for key, value in dictionary.items():
        new_key = f"{prefix}{key}" if prefix else key
        if value and isinstance(value, dict):
            flatten_dict(value, new_key + '.', result_list)
        else:
            result_list.update({new_key: value})
    return result_list


def list_output(asset_type, output_fields=None, resp=None, field_aliases=None, field_converters=None):
    if resp is None:
        resp = {}
    if output_fields is None:
        output_fields = []
    if field_aliases is None:
        field_aliases = {}
    if field_converters is None:
        field_converters = {}
    total = 0
    if isinstance(resp, dict) and "total" in resp:
        total = resp.get("total")
    elif isinstance(resp, dict) and "total" not in resp:
        resp = [flatten_dict(resp)]
        total = len(resp)
    elif isinstance(resp, list):
        total = len(resp)

    # print(f"we have {total} {asset_type} in total")

    result_field = find_result_field(asset_type, resp)
    if result_field is None and isinstance(resp, dict):
        return None
    elif isinstance(resp, list):
        table = make_records_to_table(output_fields, resp, field_aliases, field_converters)
    else:
        table = make_records_to_table(output_fields, resp[result_field], field_aliases, field_converters)
    return table


def search_result_output(result=None, transpose=False):
    if result is None:
        result = {}
    header = []
    for f in result["fields"]:
        header.append(f["name"])
    rows = result["rows"]
    return make_table(header, rows, transpose)


def get_asset_output(resp=None, output_fields=None):
    if output_fields is None:
        output_fields = []
    if resp is None:
        resp = {}
    header = ["field", "value"]
    fields = []
    filter_field = len(output_fields) > 0
    output_fields = set(output_fields)
    for k in resp:
        if (not filter_field) or (k in output_fields):
            fields.append([k, prettify_value(k, resp[k])])
    table = make_table(header, fields)
    return table


def describe_output(asset_type, resp=None):
    """通过result字段推断这个资源返回字段的类型

    Args:
        asset_type (str): 资源的类型，如repo、dashboard等
        resp (dict, optional): 请求的返回体. Defaults to {}.

    Returns:
        PrettyTable | None: 返回格式化好的表格，或者如果没有result字段则返回None
    """
    if resp is None:
        resp = {}
    total = 0
    if isinstance(resp, dict) and "total" in resp:
        total = resp.get("total")
    elif isinstance(resp, dict) and "total" not in resp:
        resp = [flatten_dict(resp)]
        total = len(resp)
    elif isinstance(resp, list):
        total = len(resp)
    if total is None or total <= 0:
        return None

    result_field = find_result_field(asset_type, resp)
    if result_field is None:
        return None

    header = ["fields", "type"]
    fields = []
    for k in resp[result_field][0]:
        fields.append((k, str(type(resp[result_field][0][k]))))
    table = make_table(header, fields)
    return table


def rs_output_all(asset_types=None):
    if asset_types is None:
        asset_types = {}
    header = ["资源类型", "资源描述", "API路径", "支持方法"]
    rows = []

    for rs in asset_types:
        conf = asset_types.get(rs)
        methods = conf.get("methods")
        methods_str = "\n".join(methods.keys())
        rows.append([rs, conf.get("desc"), conf.get("path"), methods_str])
    return make_table(header, rows)


def rs_output_one(rs, conf=None):
    if conf is None:
        conf = {}
    header = ["字段", "值"]
    if conf is None or len(conf) <= 0:
        return make_table(header, [])
    rows = [
        ["资源类型", rs],
        ["资源描述", conf.get("desc")],
        ["API路径", "/".join([ROOT_PATH, conf.get("path")])],
    ]

    methods = ""
    if "methods" in conf:
        methods_obj = conf.get("methods")

        for m in methods_obj:
            if isinstance(methods_obj[m], dict):
                cmd = help_methods(rs, m, json.dumps(methods_obj[m].get("data", {}), ensure_ascii=False), methods_obj[m].get('description'))
            else:
                cmd = help_methods(rs, m)
            methods += f"{cmd}\n"
        if conf.get("show_describe", True):
            cmd = help_methods(rs, "describe")
            methods += f"{cmd}\n"
    if len(methods) > 0:
        rows.append(["支持方法", methods.strip()])
    mark = [
        "当 --data 参数有示例时，则此资源支持不指定 --data 和 --file 来操作，执行时将按照默认值进行操作。",
        "如果示例中包含模板变量，则可通过-e key=value,key2=value2方式指定模板变量",
    ]

    rows.append(["备注", "\n".join(mark)])

    # example = conf.get("example")
    # if example is not None and len(example) > 0:
    #     rows.append(["请求示例", example])
    return make_table(header, rows)


def rs_output_one_example(rs, conf=None):
    if conf is None:
        conf = {}
    if conf is None or len(conf) <= 0:
        return f"there is no example of resource {rs}"

    example = conf.get("example")
    if example is not None and len(example) > 0:
        return json.dumps(example, indent=2, ensure_ascii=False)
    return f"there is no example of resource {rs}"


def help_methods(rs: str, m: str = "list", example=None, description: str = ""):
    if m == "list":
        return f"列举资源：ketacli {m} {rs} [--fields FIELDS] [-f FORMAT] [--lang LANG] "
    elif m == "get":
        return f"根据id或名字查询：ketacli {m} {rs} \"resource_id_or_name\" [--fields FIELDS] [-f FORMAT]"
    elif m == "create":
        return f"创建资源：ketacli {m} {rs} --name \"resource_id_or_name\" [--data '{example}'] [--file \"/path/to/file\"]"
    elif m == "describe":
        return f"获取资源结构：ketacli {m} {rs} [--fields FIELDS] [-f FORMAT]"
    elif m == "update":
        return f"更新资源：ketacli update {rs} --name \"resource_id_or_name\" [--file \"/path/to/file\"] [--data '{example}']"
    elif m == "download":
        return f"下载资源：ketacli download {rs} [--extra key=value]"
    else:
        return f"{description}: ketacli update {rs} -o {m} [--extra key=value] [--data '{example}']"

