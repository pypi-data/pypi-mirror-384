from types import SimpleNamespace
from .cli import test_command

def run_test_with_assertion(args):
    """
    运行测试并进行断言
    
    Args:
        args: SimpleNamespace对象，包含测试参数
    
    Returns:
        bool: 测试是否通过
    """
    try:
        print(f"[测试运行器] 开始运行测试")
        result = test_command(args)
        
        if result:
            print(f"[测试运行器] 测试通过")
        else:
            print(f"[测试运行器] 测试失败")
            
        return result
        
    except Exception as e:
        print(f"[测试运行器] 运行测试时出错: {e}")
        return False