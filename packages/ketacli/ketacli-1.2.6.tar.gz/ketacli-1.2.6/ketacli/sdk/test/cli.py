from types import SimpleNamespace
from ..base.client import *
from ..request.asset_map import get_resources
import time
import json
import jsonpath_ng
from ..request.create import create_asset_request
from ..request.list import list_assets_request
from ..request.get import get_asset_by_id_request
from ..request.update import update_asset_request
from ..request.delete import delete_asset_request
from ..request.export import export_asset_request

def test_command(args):
    """
    测试命令函数
    
    Args:
        args: SimpleNamespace对象，包含以下属性：
            - asset_type: 资源类型
            - method: 方法名（list, create, update, delete等）
            - name: 资源名称（可选）
            - data: 数据（可选）
            - extra: 额外参数（可选）
    """
    try:
        print(f"[测试模式] 正在测试 {args.asset_type} {args.method} {args.params}")
        
        # 获取资源配置
        resources = get_resources()
        
        if args.asset_type not in resources:
            print(f"[测试模式] 错误: 未找到资源类型 '{args.asset_type}'")
            return False
        
        resource_config = resources[args.asset_type]
        
        # 检查方法是否存在
        if 'methods' in resource_config and args.method in resource_config['methods']:
            method_config = resource_config['methods'][args.method]
            
            # 获取测试配置
            test_config = method_config.get('test_config', {})

            # 执行实际的API测试
            success = execute_api_test(args, method_config, test_config)
            
            if success:
                print(f"[测试模式] ✅ 测试通过 - {args.asset_type} {args.method}")
                return True
            else:
                print(f"[测试模式] ❌ 测试失败 - {args.asset_type} {args.method}")
                return False

        else:
            print(f"[测试模式] 错误: 方法 '{args.method}' 在资源类型 '{args.asset_type}' 中不存在")
            return False
            
    except Exception as e:
        print(f"[测试模式] 执行测试时出错: {e}")
        return False


def execute_api_test(args, method_config, test_config):
    """
    执行API测试
    
    Args:
        args: 命令行参数
        method_config: 方法配置
        test_config: 测试配置
    
    Returns:
        bool: 测试是否成功
    """
    try:
        # 执行API请求
        start_time = time.time()
        response = make_api_request(args, args.method)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # 转换为毫秒
        
        print(f"[测试模式] API请求完成，响应时间: {response_time:.2f}ms")
        print(f"[测试模式] 响应状态码: {response.status_code}")
        print(f"[测试模式] 响应内容: {response.text}")
        
        # 执行断言检查
        assertions = test_config.get('assertions', [])
        for assertion in assertions:
            if not check_assertion(assertion, response, response_time):
                return False
        
        return True
        
    except Exception as e:
        print(f"[测试模式] API测试执行失败: {e}")
        return False





def make_api_request(args, method_name):
    """
    执行API请求，使用已有的组装方法
    
    Args:
        args: 命令行参数
        method_name: 方法名称（list, create, update, delete, get, export）
    
    Returns:
        requests.Response: 响应对象
    """
    asset_type = args.asset_type
    name = args.params.get('name', None)
    data = args.params.get('data', None)
    extra = args.params.get('extra', {})

    print(f"[测试模式] name: {name}")
    
    print(f"[测试模式] 使用 {method_name} 方法测试 {asset_type}")
    
    # 根据方法类型调用相应的组装函数
    if method_name == 'list':
        request_info = list_assets_request(asset_type, **extra)
    elif method_name == 'create':
        request_info = create_asset_request(asset_type, name=name, data=data, **extra)
    elif method_name == 'update':
        request_info = update_asset_request(asset_type, name=name, data=data, **extra)
    elif method_name == 'delete':
        request_info = delete_asset_request(asset_type, name=name, data=data, **extra)
    elif method_name == 'get':
         request_info = get_asset_by_id_request(asset_type, name, **extra)
    elif method_name == 'export':
        request_info = export_asset_request(asset_type, name=name, data=data, **extra)
    else:
        raise ValueError(f"不支持的方法: {method_name}")
    
    # 打印请求信息
    print(f"[测试模式] 发送 {request_info['method'].upper()} 请求到: {request_info['path']}")
    if request_info.get('data'):
        print(f"[测试模式] 请求数据: {json.dumps(request_info['data'], indent=2, ensure_ascii=False)}")
    
    # 执行请求
    return request(
        request_info['method'],
        request_info['path'],
        data=request_info.get('data'),
        query_params=request_info.get('query_params', {}),
        custom_headers=request_info.get('custom_headers', {})
    )


def check_assertion(assertion, response, response_time):
    """
    检查断言
    
    Args:
        assertion: 断言配置
        response: 响应对象
        response_time: 响应时间（毫秒）
    
    Returns:
        bool: 断言是否通过
    """
    assertion_type = assertion.get('type')
    
    try:
        if assertion_type == 'status_code':
            expected = assertion.get('expected', 200)
            actual = response.status_code
            print(f"[测试模式] 检查状态码: 期望 {expected}, 实际 {actual}")
            if actual != expected:
                print(f"[测试模式] ❌ 状态码断言失败: 期望 {expected}, 实际 {actual}")
                return False
            print(f"[测试模式] ✅ 状态码断言通过")
            
        elif assertion_type == 'response_time':
            max_time = assertion.get('max_time', 5000)
            print(f"[测试模式] 检查响应时间: 最大 {max_time}ms, 实际 {response_time:.2f}ms")
            if response_time > max_time:
                print(f"[测试模式] ❌ 响应时间断言失败: 期望 <= {max_time}ms, 实际 {response_time:.2f}ms")
                return False
            print(f"[测试模式] ✅ 响应时间断言通过")
            
        elif assertion_type == 'json_path':
            path = assertion.get('path', '$')
            expected = assertion.get('expected')
            expected_type = assertion.get('expected_type')
            
            try:
                response_json = response.json()
                # print(f'[返回数据]: {response_json}')
                print(f"[测试模式] 检查JSON路径: {path}")
                
                # 使用jsonpath提取值
                jsonpath_expr = jsonpath_ng.parse(path)
                matches = [match.value for match in jsonpath_expr.find(response_json)]
                
                if not matches:
                    print(f"[测试模式] ❌ JSON路径断言失败: 路径 {path} 未找到")
                    return False
                
                actual_value = matches[0] if len(matches) == 1 else matches
                
                # 检查期望值
                if expected is not None:
                    if actual_value != expected:
                        print(f"[测试模式] ❌ JSON路径值断言失败: 期望 {expected}, 实际 {actual_value}")
                        return False
                
                # 检查期望类型
                if expected_type:
                    actual_type = type(actual_value).__name__
                    if expected_type == 'array' and actual_type != 'list':
                        print(f"[测试模式] ❌ JSON路径类型断言失败: 期望 array, 实际 {actual_type}")
                        return False
                    elif expected_type == 'string' and actual_type != 'str':
                        print(f"[测试模式] ❌ JSON路径类型断言失败: 期望 string, 实际 {actual_type}")
                        return False
                    elif expected_type == 'number' and actual_type not in ['int', 'float']:
                        print(f"[测试模式] ❌ JSON路径类型断言失败: 期望 number, 实际 {actual_type}")
                        return False
                    elif expected_type == 'boolean' and actual_type != 'bool':
                        print(f"[测试模式] ❌ JSON路径类型断言失败: 期望 boolean, 实际 {actual_type}")
                        return False
                
                print(f"[测试模式] ✅ JSON路径断言通过: {path} = {str(actual_value)[0:50]}...")
                
            except json.JSONDecodeError:
                print(f"[测试模式] ❌ JSON路径断言失败: 响应不是有效的JSON")
                return False
            except Exception as e:
                print(f"[测试模式] ❌ JSON路径断言失败: {e}")
                return False
                
        else:
            print(f"[测试模式] ⚠️  未知断言类型: {assertion_type}")
            return True  # 未知类型不影响测试结果
        
        return True
        
    except Exception as e:
        print(f"[测试模式] ❌ 断言检查失败: {e}")
        return False