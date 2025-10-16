"""
数据操作功能的Function Call包装器
"""

import json
from typing import Union, List, Dict, Any
from ketacli.sdk.ai.function_call import function_registry
from ketacli.sdk.base.client import request_post
from ketacli.plugins.mock import mock_log as _mock_log, mock_metrics as _mock_metrics


# @function_registry.register(
#     name="insert_data",
#     description="向指定仓库插入数据",
#     parameters={
#         "type": "object",
#         "properties": {
#             "repository": {
#                 "type": "string",
#                 "description": "目标数据仓库名称"
#             },
#             "data": {
#                 "type": "string",
#                 "description": "要插入的数据（JSON格式字符串）"
#             },
#             "data_format": {
#                 "type": "string",
#                 "description": "数据格式（目前支持json）",
#                 "default": "json"
#             }
#         },
#         "required": ["repository", "data"]
#     }
# )
# def insert_data(repository: str, data: str, data_format: str = "json") -> str:
#     """向指定仓库插入数据"""
#     try:
#         # 解析JSON数据
#         if data_format == "json":
#             parsed_data = json.loads(data)
#         else:
#             return f"不支持的数据格式: {data_format}"
        
#         # 构建查询参数
#         query_params = {
#             "repo": repository,
#         }
        
#         # 发送请求
#         resp = request_post("data", parsed_data, query_params).json()
#         return json.dumps(resp, ensure_ascii=False, indent=2)
        
#     except json.JSONDecodeError as e:
#         return f"JSON数据解析失败: {str(e)}"
#     except Exception as e:
#         return f"插入数据失败: {str(e)}"


# @function_registry.register(
#     name="batch_insert_data",
#     description="批量向指定仓库插入多条数据",
#     parameters={
#         "type": "object",
#         "properties": {
#             "repository": {
#                 "type": "string",
#                 "description": "目标数据仓库名称"
#             },
#             "data_list": {
#                 "type": "string",
#                 "description": "要插入的数据列表（JSON数组格式字符串）"
#             }
#         },
#         "required": ["repository", "data_list"]
#     }
# )
# def batch_insert_data(repository: str, data_list: str) -> str:
#     """批量向指定仓库插入数据"""
#     try:
#         # 解析JSON数据列表
#         parsed_data_list = json.loads(data_list)
#         if not isinstance(parsed_data_list, list):
#             return "data_list必须是JSON数组格式"
        
#         results = []
#         for i, data_item in enumerate(parsed_data_list):
#             try:
#                 query_params = {
#                     "repo": repository,
#                 }
#                 resp = request_post("data", data_item, query_params).json()
#                 results.append({
#                     "index": i,
#                     "success": True,
#                     "result": resp
#                 })
#             except Exception as e:
#                 results.append({
#                     "index": i,
#                     "success": False,
#                     "error": str(e)
#                 })
        
#         return json.dumps(results, ensure_ascii=False, indent=2)
        
#     except json.JSONDecodeError as e:
#         return f"JSON数据解析失败: {str(e)}"
#     except Exception as e:
#         return f"批量插入数据失败: {str(e)}"


@function_registry.register(
    name="mock_log",
    description="生成模拟日志数据并插入到指定仓库",
    parameters={
        "type": "object",
        "properties": {
            "repo": {
                "type": "string",
                "description": "目标数据仓库名称",
                "default": "default"
            },
            "number": {
                "type": "integer",
                "description": "生成数据条数",
                "default": 1
            },
            "log_type": {
                "type": "string",
                "description": "日志类型，支持: nginx, java, linux",
                "default": "nginx"
            },
            "batch": {
                "type": "integer",
                "description": "批处理大小",
                "default": 2000
            },
            # "workers": {
            #     "type": "integer",
            #     "description": "并发工作线程数",
            #     "default": 1
            # }
        },
        "required": ["repo"]
    }
)
def mock_log(repo: str = "default", number: int = 1, log_type: str = "nginx", 
             batch: int = 2000, workers: int = 1) -> str:
    """生成模拟日志数据并插入到指定仓库"""
    try:
        # 调用原始的mock_log函数
        _mock_log(
            repo=repo,
            number=number,
            log_type=log_type,
            batch=batch,
            workers=workers,
            output_type="server",
            render=True
        )
        return f"成功生成并插入 {number} 条 {log_type} 类型的日志数据到仓库 '{repo}'"
    except Exception as e:
        return f"生成模拟日志数据失败: {str(e)}"


@function_registry.register(
    name="mock_metrics",
    description="生成模拟指标数据并插入到指定仓库",
    parameters={
        "type": "object",
        "properties": {
            "repo": {
                "type": "string",
                "description": "目标数据仓库名称",
                "default": "metrics_keta"
            },
            "number": {
                "type": "integer",
                "description": "生成数据条数",
                "default": 1
            },
            "batch": {
                "type": "integer",
                "description": "批处理大小",
                "default": 2000
            },
            "workers": {
                "type": "integer",
                "description": "并发工作线程数",
                "default": 1
            }
        },
        "required": ["repo"]
    }
)
def mock_metrics(repo: str = "metrics_keta", number: int = 1, 
                 batch: int = 2000, workers: int = 1) -> str:
    """生成模拟指标数据并插入到指定仓库"""
    try:
        # 调用原始的mock_metrics函数
        _mock_metrics(
            repo=repo,
            number=number,
            batch=batch,
            workers=workers,
            output_type="server",
            render=True
        )
        return f"成功生成并插入 {number} 条指标数据到仓库 '{repo}'"
    except Exception as e:
        return f"生成模拟指标数据失败: {str(e)}"