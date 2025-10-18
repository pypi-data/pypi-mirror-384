"""
Function Call 功能模块

提供AI大模型的function call功能，支持动态注册和调用ketacli的各种功能。
"""

import json
import inspect
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from rich.console import Console

console = Console(markup=False)


@dataclass
class FunctionSchema:
    """函数模式定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable


class FunctionRegistry:
    """函数注册表"""
    
    def __init__(self):
        self._functions: Dict[str, FunctionSchema] = {}
    
    def register(self, name: str, description: str, parameters: Dict[str, Any] = None):
        """注册函数装饰器"""
        def decorator(func: Callable):
            if parameters is None:
                # 自动从函数签名生成参数模式
                sig = inspect.signature(func)
                auto_params = self._generate_parameters_from_signature(sig)
            else:
                auto_params = parameters
            
            schema = FunctionSchema(
                name=name,
                description=description,
                parameters=auto_params,
                function=func
            )
            self._functions[name] = schema
            return func
        return decorator
    
    def _generate_parameters_from_signature(self, sig: inspect.Signature) -> Dict[str, Any]:
        """从函数签名自动生成参数模式"""
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name.startswith('_'):  # 跳过私有参数
                continue
                
            param_info = {
                "type": "string"  # 默认类型
            }
            
            # 根据类型注解推断参数类型
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_info["type"] = "integer"
                elif param.annotation == float:
                    param_info["type"] = "number"
                elif param.annotation == bool:
                    param_info["type"] = "boolean"
                elif param.annotation == list:
                    param_info["type"] = "array"
                elif param.annotation == dict:
                    param_info["type"] = "object"
            
            # 如果没有默认值，则为必需参数
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
            else:
                param_info["default"] = param.default
            
            properties[param_name] = param_info
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def get_function(self, name: str) -> Optional[FunctionSchema]:
        """获取注册的函数"""
        return self._functions.get(name)
    
    def list_functions(self) -> List[FunctionSchema]:
        """列出所有注册的函数"""
        return list(self._functions.values())
    
    def get_openai_tools_format(self) -> List[Dict[str, Any]]:
        """获取OpenAI tools格式的函数定义"""
        tools = []
        for func_schema in self._functions.values():
            tool = {
                "type": "function",
                "function": {
                    "name": func_schema.name,
                    "description": func_schema.description,
                    "parameters": func_schema.parameters
                }
            }
            tools.append(tool)
        return tools


class FunctionCallExecutor:
    """函数调用执行器"""
    
    def __init__(self, registry: FunctionRegistry):
        self.registry = registry
        self.executor = ThreadPoolExecutor(max_workers=4)  # 线程池用于异步执行
    
    def execute(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """执行函数调用"""
        func_schema = self.registry.get_function(function_name)
        if not func_schema:
            raise ValueError(f"未找到函数: {function_name}")
        
        try:
            # 执行函数
            result = func_schema.function(**arguments)
            return {
                "success": True,
                "result": result,
                "function_name": function_name
            }
        except Exception as e:
            console.print(f"[red]执行函数 {function_name} 时出错: {e}[/red]")
            return {
                "success": False,
                "error": str(e),
                "function_name": function_name
            }
    
    def execute_from_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从AI模型的tool_calls执行函数"""
        results = []
        for tool_call in tool_calls:
            if tool_call.get("type") == "function":
                function_info = tool_call.get("function", {})
                function_name = function_info.get("name")
                arguments_str = function_info.get("arguments", "{}")
                
                try:
                    arguments = json.loads(arguments_str)
                    result = self.execute(function_name, arguments)
                    result["tool_call_id"] = tool_call.get("id")
                    results.append(result)
                except json.JSONDecodeError as e:
                    results.append({
                        "success": False,
                        "error": f"参数解析错误: {e}",
                        "function_name": function_name,
                        "tool_call_id": tool_call.get("id")
                    })
        
        return results
    
    # ==================== 异步方法 ====================
    
    async def execute_async(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """异步执行函数调用"""
        func_schema = self.registry.get_function(function_name)
        if not func_schema:
            raise ValueError(f"未找到函数: {function_name}")
        
        try:
            # 在线程池中执行函数，避免阻塞主线程
            loop = asyncio.get_event_loop()
            
            # 创建一个包装函数来正确传递参数
            def execute_with_args():
                return func_schema.function(**arguments)
            
            result = await loop.run_in_executor(
                self.executor, 
                execute_with_args
            )
            return {
                "success": True,
                "result": result,
                "function_name": function_name
            }
        except Exception as e:
            console.print(f"[red]异步执行函数 {function_name} 时出错: {e}[/red]")
            return {
                "success": False,
                "error": str(e),
                "function_name": function_name
            }
    
    async def execute_from_tool_calls_async(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """异步从AI模型的tool_calls执行函数"""
        tasks = []
        
        for tool_call in tool_calls:
            if tool_call.get("type") == "function":
                function_info = tool_call.get("function", {})
                function_name = function_info.get("name")
                arguments_str = function_info.get("arguments", "{}")
                
                try:
                    arguments = json.loads(arguments_str)
                    # 创建异步任务
                    task = self._execute_single_tool_call_async(
                        function_name, arguments, tool_call.get("id")
                    )
                    tasks.append(task)
                except json.JSONDecodeError as e:
                    # 对于解析错误，创建一个返回错误的协程
                    async def create_error_result():
                        return {
                            "success": False,
                            "error": f"参数解析错误: {e}",
                            "function_name": function_name,
                            "tool_call_id": tool_call.get("id")
                        }
                    tasks.append(create_error_result())
        
        # 并发执行所有工具调用
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # 处理异常结果
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    processed_results.append({
                        "success": False,
                        "error": str(result),
                        "function_name": "unknown"
                    })
                else:
                    processed_results.append(result)
            return processed_results
        
        return []
    
    async def _execute_single_tool_call_async(self, function_name: str, arguments: Dict[str, Any], tool_call_id: str) -> Dict[str, Any]:
        """异步执行单个工具调用"""
        result = await self.execute_async(function_name, arguments)
        result["tool_call_id"] = tool_call_id
        return result


# 全局函数注册表
function_registry = FunctionRegistry()
function_executor = FunctionCallExecutor(function_registry)