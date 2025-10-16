from rich import console
from ..util import is_fuzzy_key
from .asset_map import get_resources
from ..base.client import ROOT_PATH
from ..converters import apply_field_converter

console = console.Console()


def _extract_field_aliases(default_fields):
    """从default_fields配置中提取字段别名映射
    
    Args:
        default_fields: 字段配置列表，可能包含字典格式的字段定义
        
    Returns:
        dict: 字段名到别名的映射字典
    """
    field_aliases = {}
    if not default_fields:
        return field_aliases
    
    for field_config in default_fields:
        if isinstance(field_config, dict):
            # 新格式：{"name": "field_name", "alias": "别名"}
            if "name" in field_config and "alias" in field_config:
                field_aliases[field_config["name"]] = field_config["alias"]
            elif "name" in field_config:
                # 只有name没有alias，使用字段名作为别名
                field_aliases[field_config["name"]] = field_config["name"]
        elif isinstance(field_config, str):
            # 处理字符串格式，保持原样
            field_aliases[field_config] = field_config
            
    return field_aliases


def _extract_field_converters(default_fields):
    """从default_fields配置中提取字段转换器配置
    
    Args:
        default_fields: 字段配置列表，可能包含字典格式的字段定义
        
    Returns:
        dict: 字段名到转换器配置的映射字典
    """
    field_converters = {}
    if not default_fields:
        return field_converters
    
    for field_config in default_fields:
        if isinstance(field_config, dict) and "name" in field_config and "convert" in field_config:
            field_converters[field_config["name"]] = field_config["convert"]
            
    return field_converters


def apply_field_conversions(data_list, field_converters):
    """对数据列表应用字段转换
    
    Args:
        data_list: 数据列表
        field_converters: 字段转换器配置字典
        
    Returns:
        list: 转换后的数据列表
    """
    if not data_list or not field_converters:
        return data_list
    
    converted_data = []
    for item in data_list:
        if isinstance(item, dict):
            converted_item = item.copy()
            for field_name, convert_config in field_converters.items():
                if field_name in converted_item:
                    original_value = converted_item[field_name]
                    converted_value = apply_field_converter(original_value, convert_config)
                    converted_item[field_name] = converted_value
            converted_data.append(converted_item)
        else:
            converted_data.append(item)
    
    return converted_data


def list_assets_request(asset_name, groupId=-1, order="desc", pageNo=1,
                        pageSize=10, prefix="", sort="updateTime", lang=None, **kwargs):
    path = asset_name
    query_fields = []
    ASSET_MAP = get_resources()
    key = is_fuzzy_key(asset_name, value_map=ASSET_MAP)
    default_fields = []
    fields_style = {}
    if key is not None:
        path = ASSET_MAP.get(key)["path"]
        if "methods" in ASSET_MAP.get(key) and "list" in ASSET_MAP.get(key)["methods"] and isinstance(ASSET_MAP.get(key)["methods"]['list'], dict):
            methods = ASSET_MAP.get(key)["methods"]
            path = methods.get('list', {}).get('path', path)
            default_fields = methods.get('list', {}).get('default_fields', [])
            fields_style = methods.get('list', {}).get('fields_style', [])
            if "query_fields" in methods['list']:
                query_fields = methods['list']["query_fields"]
        if not query_fields and "query_fields" in ASSET_MAP.get(key):
            query_fields = ASSET_MAP.get(key)["query_fields"]
        

    use_default_query_params = ASSET_MAP.get(key, {}).get("use_default_query_params", True)

    if use_default_query_params:
        query_params = {
            "groupId": groupId,
            "order": order,
            "pageNo": pageNo,
            "pageSize": pageSize,
            "prefix": prefix,
            "sort": sort,
        }
    else:
        query_params = {}
    for finfo in query_fields:
        f = finfo["field"]
        dft = finfo["default"]
        required = finfo["required"]
        if f in kwargs:
            query_params[f] = kwargs[f]
        elif required:
            query_params[f] = dft
    query_params.update(kwargs)

    custom_headers = {}
    if lang is not None and isinstance(lang, str):
        custom_headers["X-Pandora-Language"] = lang

    req_info = {
        "path": path,
        "query_params": query_params,
        # list 操作用不到的内容
        "method": "get",
        "data": {},
        "custom_headers": custom_headers,
        "fields_style": fields_style,
        "default_fields": default_fields,
        "field_aliases": _extract_field_aliases(default_fields),
        "field_converters": _extract_field_converters(default_fields),
    }
    # console.print(req_info)
    return req_info


def list_admin_request(asset_name, **kwargs):
    path = "/".join([ROOT_PATH, "admin/internal", asset_name])
    query_fields = []
    key = is_fuzzy_key(asset_name, value_map=ASSET_MAP)
    if key is not None:
        path = ASSET_MAP.get(key)["path"]
        if "query_fields" in ASSET_MAP.get(key):
            query_fields = ASSET_MAP.get(key)["query_fields"]

    query_params = {"format": "json"}
    for finfo in query_fields:
        f = finfo["field"]
        dft = finfo["default"]
        required = finfo["required"]
        if f in kwargs:
            query_params[f] = kwargs[f]
        elif required:
            query_params[f] = dft

    custom_headers = {}

    return {
        "path": path,
        "query_params": query_params,
        # list 操作用不到的内容
        "method": "get",
        "data": {},
        "custom_headers": custom_headers,
    }
