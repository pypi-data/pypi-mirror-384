"""
AI模块使用示例

展示如何使用AI大模型请求功能。
"""

from .client import AIClient, AIRequest
from .config import AIConfig, AIModelConfig
from .validators import ResponseValidator, create_openai_validator, create_text_validator


def example_basic_chat():
    """基础聊天示例"""
    print("=== 基础聊天示例 ===")
    
    # 创建AI客户端
    client = AIClient()
    
    try:
        # 发送简单消息
        response = client.chat("你好，请介绍一下你自己")
        print(f"AI回复: {response.content}")
        print(f"使用模型: {response.model}")
        print(f"Token使用情况: {response.usage}")
        
    except Exception as e:
        print(f"请求失败: {e}")


def example_with_validator():
    """带验证器的示例"""
    print("\n=== 带验证器的示例 ===")
    
    client = AIClient()
    
    # 创建验证器
    validator = ResponseValidator()
    validator.add_length_validator(min_length=10)  # 至少10个字符
    validator.add_custom_validator(
        lambda response: "AI" in str(response) or "助手" in str(response),
        "响应中应包含'AI'或'助手'"
    )
    
    try:
        response = client.chat(
            "请用一句话介绍你是什么",
            validator=validator
        )
        print(f"验证通过，AI回复: {response.content}")
        
    except Exception as e:
        print(f"验证失败: {e}")


def example_with_callback():
    """带回调函数的示例"""
    print("\n=== 带回调函数的示例 ===")
    
    client = AIClient()
    
    def response_callback(response):
        """响应回调函数"""
        print(f"[回调] 收到响应，长度: {len(response.content)} 字符")
        print(f"[回调] 完成原因: {response.finish_reason}")
    
    try:
        response = client.chat(
            "请写一首关于春天的短诗",
            callback=response_callback
        )
        print(f"AI回复:\n{response.content}")
        
    except Exception as e:
        print(f"请求失败: {e}")


def example_stream_chat():
    """流式聊天示例"""
    print("\n=== 流式聊天示例 ===")
    
    client = AIClient()
    
    def stream_callback(content):
        """流式回调函数"""
        print(content, end='', flush=True)
    
    try:
        print("AI回复: ", end='')
        for chunk in client.stream_chat(
            "请讲一个简短的故事",
            callback=stream_callback
        ):
            pass  # 内容已在回调中处理
        print()  # 换行
        
    except Exception as e:
        print(f"流式请求失败: {e}")


def example_multiple_messages():
    """多轮对话示例"""
    print("\n=== 多轮对话示例 ===")
    
    client = AIClient()
    
    messages = [
        {"role": "user", "content": "我想学习Python编程"},
        {"role": "assistant", "content": "很好！Python是一门很棒的编程语言。你想从哪里开始学习？"},
        {"role": "user", "content": "请推荐一些适合初学者的资源"}
    ]
    
    try:
        response = client.chat(messages)
        print(f"AI回复: {response.content}")
        
    except Exception as e:
        print(f"请求失败: {e}")


def example_model_switching():
    """模型切换示例"""
    print("\n=== 模型切换示例 ===")
    
    client = AIClient()
    
    print(f"当前模型: {client.get_current_model()}")
    print(f"可用模型: {client.get_available_models()}")
    
    # 如果有多个模型，尝试切换
    available_models = client.get_available_models()
    if len(available_models) > 1:
        new_model = available_models[1] if available_models[0] == client.get_current_model() else available_models[0]
        try:
            client.switch_model(new_model)
            print(f"已切换到模型: {client.get_current_model()}")
            
            response = client.chat("你好")
            print(f"新模型回复: {response.content}")
            
        except Exception as e:
            print(f"模型切换失败: {e}")


def example_config_management():
    """配置管理示例"""
    print("\n=== 配置管理示例 ===")
    
    config = AIConfig()
    
    print(f"默认模型: {config.get_default_model()}")
    print(f"所有模型: {config.list_models()}")
    
    # 添加新模型配置
    new_model = AIModelConfig(
        name="custom_model",
        endpoint="https://api.example.com/v1/chat",
        api_key="your-api-key",
        model="custom-model-v1",
        max_tokens=2048,
        temperature=0.8
    )
    
    try:
        config.add_model(new_model)
        print(f"已添加新模型: {new_model.name}")
        print(f"更新后的模型列表: {config.list_models()}")
        
        # 删除测试模型
        config.remove_model("custom_model")
        print("已删除测试模型")
        
    except Exception as e:
        print(f"配置管理失败: {e}")


def example_advanced_validation():
    """高级验证示例"""
    print("\n=== 高级验证示例 ===")
    
    client = AIClient()
    
    # 创建复杂验证器
    validator = ResponseValidator()
    
    # JSON格式验证（如果响应是JSON）
    validator.add_json_validator(['choices'])
    
    # 正则表达式验证
    validator.add_regex_validator(r'\d+', 0)  # 必须包含数字
    
    # 长度验证
    validator.add_length_validator(min_length=20, max_length=500)
    
    # 自定义验证
    def custom_validation(response):
        """自定义验证函数"""
        content = str(response)
        return "Python" in content or "编程" in content
    
    validator.add_custom_validator(custom_validation, "响应中应包含'Python'或'编程'")
    
    try:
        response = client.chat(
            "请用50个字左右介绍Python编程语言，并提到它的版本号",
            validator=validator
        )
        print(f"验证通过，AI回复: {response.content}")
        
    except Exception as e:
        print(f"高级验证失败: {e}")


def run_all_examples():
    """运行所有示例"""
    print("AI模块使用示例")
    print("=" * 50)
    
    try:
        example_basic_chat()
        example_with_validator()
        example_with_callback()
        example_stream_chat()
        example_multiple_messages()
        example_model_switching()
        example_config_management()
        example_advanced_validation()
        
    except Exception as e:
        print(f"示例运行出错: {e}")
    
    print("\n所有示例运行完成！")


if __name__ == "__main__":
    run_all_examples()