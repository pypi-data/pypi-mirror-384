"""
资产管理功能的Function Call包装器
"""

import json
from typing import Optional, List
from ketacli.sdk.ai.function_call import function_registry
from ketacli.sdk.request.list import list_assets_request
from ketacli.sdk.request.get import get_asset_by_id_request
from ketacli.sdk.request.create import create_asset_request
from ketacli.sdk.request.delete import delete_asset_request
from ketacli.sdk.output.output import list_output, get_asset_output, rs_output_all
from ketacli.sdk.output.format import format_table
from ketacli.sdk.util import parse_url_params
from ketacli.sdk.base.client import request_get, request_post, request_delete, request_put
from ketacli.sdk.request.asset_map import get_resources



@function_registry.register(
    name="list_assets",
    description="列出指定类型的资产，涉及到有数量字段的资产类型时，默认按数量字段排序， 比如列出repo时，请将sort设置为docTotal，需要搜索时可指定prefix参数",
    parameters={
        "type": "object",
        "properties": {
            "asset_type": {
                "type": "string",
                "description": "资产类型，如：repo, sourcetype, metric, targets等"
            },
            "page_size": {
                "type": "integer",
                "description": "每页数量",
                "default": 100
            },
            "page_no": {
                "type": "integer",
                "description": "页码",
                "default": 1
            },
            "prefix": {
                "type": "string",
                "description": "关键字过滤"
            },
            "sort": {
                "type": "string",
                "description": "排序字段",
                "default": "updateTime"
            },
            "order": {
                "type": "string",
                "description": "排序顺序：desc或asc",
                "default": "desc"
            },
            "fields": {
                "type": "string",
                "description": "显示字段，用逗号分隔"
            },
            "format_type": {
                "type": "string",
                "description": "text, json, csv",
                "default": "csv"
            }
        },
        "required": ["asset_type", "prefix"]
    }
)
def list_assets(asset_type: str, page_size: int = 100, page_no: int = 1,
                prefix: str = "", sort: str = "updateTime", order: str = "desc",
                fields: str = "", format_type: str = "csv", show_all_fields: bool = False) -> str:
    """列出指定类型的资产"""
    try:
        # 构建请求参数
        params = {
            "pageSize": page_size,
            "pageNo": page_no,
            "prefix": prefix,
            "sort": sort,
            "order": order
        }
        
        # 发送请求
        req = list_assets_request(asset_type, **params)
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
        return format_table(table, format_type)
        
    except Exception as e:
        return f"列出资产失败: {str(e)}"


@function_registry.register(
    name="get_asset_detail",
    description="获取指定资产的详细信息",
    parameters={
        "type": "object",
        "properties": {
            "asset_type": {
                "type": "string",
                "description": "资产类型"
            },
            "asset_id": {
                "type": "string",
                "description": "资产ID或名称"
            }
        },
        "required": ["asset_type", "asset_id"]
    }
)
def get_asset_detail(asset_type: str, asset_id: str) -> str:
    """获取资产详细信息"""
    try:
        req = get_asset_by_id_request(asset_type, asset_id)
        resp = request_get(req["path"], req["query_params"],
                           req["custom_headers"]).json()
        result_output = get_asset_output(resp)
        return result_output.get_formatted_string("text")
    except Exception as e:
        return f"获取资产详情失败: {str(e)}"


@function_registry.register(
    name="create_asset",
    description="创建新的资产，当",
    parameters={
        "type": "object",
        "properties": {
            "asset_type": {
                "type": "string",
                "description": "资产类型"
            },
            "asset_name": {
                "type": "string",
                "description": "资产名称"
            },
            "asset_data": {
                "type": "string",
                "description": "资产数据（JSON格式字符串）"
            }
        },
        "required": ["asset_type", "asset_name", "asset_data"]
    }
)
def create_asset(asset_type: str, asset_name: str, asset_data: str) -> str:
    """创建新的资产"""
    try:
        # 解析资产数据
        data = json.loads(asset_data)
        
        # 发送创建请求
        req = create_asset_request(asset_type, asset_name, data)
        resp = request_post(req["path"], data=req["data"], 
                            query_params=req["query_params"], 
                            custom_headers=req["custom_headers"]).json()
        return str(resp)
        
    except json.JSONDecodeError as e:
        return f"资产数据解析失败: {str(e)}"
    except Exception as e:
        return f"创建资产失败: {str(e)}"


@function_registry.register(
    name="delete_asset",
    description="删除指定的资产",
    parameters={
        "type": "object",
        "properties": {
            "asset_type": {
                "type": "string",
                "description": "资产类型"
            },
            "asset_name": {
                "type": "string",
                "description": "资产名称"
            }
        },
        "required": ["asset_type", "asset_name"]
    }
)
def delete_asset(asset_type: str, asset_name: str) -> str:
    """删除指定的资产"""
    try:
        req = delete_asset_request(asset_type, asset_name)
        resp = request_delete(req["path"], req["query_params"],
                              req["custom_headers"]).json()
        return resp.text
    except Exception as e:
        return f"删除资产失败: {str(e)}"


@function_registry.register(
    name="list_queryable",
    description="获取所有可查询的资产类型列表，显示资产类型、描述、API路径和支持的方法",
    parameters={
        "type": "object",
        "properties": {}
    }
)
def list_queryable() -> str:
    """
    获取所有可查询的资产类型列表
    
    Args:
        format_type: 输出格式，支持 text, json, csv
        
    Returns:
        str: 格式化的资产类型列表
    """
    try:
        # 获取所有资源配置
        resources = get_resources()
        # 使用rs_output_all函数生成表格
        table = rs_output_all(resources)
        
        return format_table(table, "csv")
        
    except Exception as e:
        return f"获取可查询资产列表失败: {str(e)}"