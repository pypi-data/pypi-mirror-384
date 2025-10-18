"""集成示例

展示如何在现有的聊天应用中集成上下文压缩功能。
"""

from typing import List, Dict, Any
from .context_manager import ContextManager, SessionContextManager, prepare_session_for_ai
from .context_compressor import CompressionConfig
from .data_models import ChatSession


class EnhancedChatApp:
    """增强的聊天应用，集成了上下文压缩功能"""
    
    def __init__(self):
        # 配置上下文压缩
        compression_config = CompressionConfig(
            max_messages=30,  # 压缩后最大消息数
            preserve_recent=8,  # 保留最近8条消息
            preserve_system=True,  # 保留系统消息
            min_importance_score=0.3,  # 最小重要性分数
            enable_summarization=True,  # 启用摘要
            max_summary_length=150  # 摘要最大长度
        )
        
        # 创建上下文管理器
        self.context_manager = ContextManager(
            compression_config=compression_config,
            auto_compress_threshold=50,  # 50条消息后自动压缩
            enable_auto_compression=True,
            compression_callback=self._on_compression_completed
        )
        
        # 创建会话上下文管理器
        self.session_manager = SessionContextManager(self.context_manager)
        
        # 当前会话
        self.current_session = None
        self.conversation_history = []
    
    def _on_compression_completed(self, stats: Dict[str, Any]):
        """压缩完成回调"""
        print(f"✅ 上下文压缩完成:")
        print(f"   消息数: {stats['original_message_count']} -> {stats['compressed_message_count']}")
        print(f"   估算token节省: {stats['estimated_original_tokens'] - stats['estimated_compressed_tokens']}")
        print(f"   压缩率: {stats['message_reduction_ratio']:.1%}")
    
    def start_new_session(self, title: str = None):
        """开始新会话"""
        self.current_session = ChatSession.create_new(title)
        self.conversation_history = []
        print(f"🆕 开始新会话: {self.current_session.get_display_title()}")
    
    def add_message(self, role: str, content: str, tool_calls: List[Dict] = None):
        """添加消息到当前会话"""
        if not self.current_session:
            self.start_new_session()
        
        message = {
            "role": role,
            "content": content
        }
        
        if tool_calls:
            message["tool_calls"] = tool_calls
        
        self.conversation_history.append(message)
        
        # 检查是否需要压缩
        if len(self.conversation_history) >= self.context_manager.auto_compress_threshold:
            print(f"📊 消息数量达到{len(self.conversation_history)}条，触发自动压缩...")
            self.conversation_history = self.context_manager.process_messages(
                self.conversation_history
            )
    
    def prepare_for_ai_request(self, max_context_tokens: int = 4000) -> List[Dict[str, Any]]:
        """为AI请求准备上下文"""
        if not self.current_session:
            return []
        
        # 更新会话消息
        self.current_session.messages = self.conversation_history.copy()
        
        # 使用会话管理器准备上下文
        prepared_messages = self.session_manager.prepare_for_ai_request(
            self.current_session, 
            max_context_tokens
        )
        
        return prepared_messages
    
    def get_compression_recommendation(self) -> Dict[str, Any]:
        """获取压缩建议"""
        return self.context_manager.get_compression_recommendation(self.conversation_history)
    
    def manual_compress(self):
        """手动压缩当前会话"""
        if not self.conversation_history:
            print("❌ 没有消息需要压缩")
            return
        
        original_count = len(self.conversation_history)
        self.conversation_history = self.context_manager.process_messages(
            self.conversation_history, 
            force_compress=True
        )
        
        print(f"🗜️ 手动压缩完成: {original_count} -> {len(self.conversation_history)} 条消息")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        if not self.conversation_history:
            return {"message_count": 0, "estimated_tokens": 0}
        
        # 估算token数
        estimated_tokens = sum(len(msg.get("content", "")) // 2 for msg in self.conversation_history)
        
        # 角色统计
        role_counts = {}
        for msg in self.conversation_history:
            role = msg.get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1
        
        return {
            "message_count": len(self.conversation_history),
            "estimated_tokens": estimated_tokens,
            "role_distribution": role_counts,
            "compression_stats": self.context_manager.get_compression_stats()
        }
    
    def configure_compression(self, **kwargs):
        """动态配置压缩参数"""
        self.context_manager.update_config(**kwargs)
        print("⚙️ 压缩配置已更新")


def demo_integration():
    """演示集成使用"""
    print("=== 上下文压缩集成演示 ===\n")
    
    # 创建增强的聊天应用
    app = EnhancedChatApp()
    
    # 开始新会话
    app.start_new_session("Python学习助手")
    
    # 模拟对话
    conversations = [
        ("system", "你是一个Python编程助手，帮助用户学习Python。"),
        ("user", "你好，我想学习Python编程。"),
        ("assistant", "你好！我很乐意帮助你学习Python。Python是一门非常适合初学者的编程语言。"),
        ("user", "我应该从哪里开始？"),
        ("assistant", "建议你从以下几个方面开始：1. 安装Python环境 2. 学习基本语法 3. 练习简单程序"),
        ("user", "如何安装Python？"),
        ("assistant", "你可以从python.org下载官方安装包，安装时记得勾选'Add Python to PATH'选项。"),
        ("user", "安装完成了，现在想写第一个程序。"),
        ("assistant", "很好！第一个程序通常是Hello World：print('Hello, World!')"),
        ("user", "成功了！接下来学什么？"),
        ("assistant", "接下来可以学习变量和数据类型，这是编程的基础。"),
    ]
    
    # 添加对话消息
    for role, content in conversations:
        app.add_message(role, content)
        print(f"[{role}]: {content[:50]}{'...' if len(content) > 50 else ''}")
    
    print(f"\n📊 当前会话统计:")
    stats = app.get_session_stats()
    print(f"   消息数量: {stats['message_count']}")
    print(f"   估算token数: {stats['estimated_tokens']}")
    print(f"   角色分布: {stats['role_distribution']}")
    
    # 获取压缩建议
    print(f"\n💡 压缩建议:")
    recommendation = app.get_compression_recommendation()
    print(f"   是否建议压缩: {recommendation['should_compress']}")
    print(f"   建议原因: {recommendation['recommendation_reason']}")
    print(f"   可节省token: {recommendation['potential_token_savings']}")
    
    # 为AI请求准备上下文
    print(f"\n🤖 为AI请求准备上下文:")
    ai_context = app.prepare_for_ai_request(max_context_tokens=2000)
    print(f"   准备的消息数: {len(ai_context)}")
    
    # 手动压缩演示
    print(f"\n🗜️ 手动压缩演示:")
    app.manual_compress()
    
    # 显示压缩后的统计
    final_stats = app.get_session_stats()
    print(f"\n📈 压缩后统计:")
    print(f"   消息数量: {final_stats['message_count']}")
    print(f"   估算token数: {final_stats['estimated_tokens']}")
    
    compression_stats = final_stats['compression_stats']
    if compression_stats['total_compressions'] > 0:
        print(f"   总压缩次数: {compression_stats['total_compressions']}")
        print(f"   平均压缩率: {compression_stats['average_message_reduction']:.1%}")
        print(f"   总节省token: {compression_stats['total_tokens_saved']}")
    
    # 动态配置演示
    print(f"\n⚙️ 动态配置演示:")
    app.configure_compression(
        max_messages=20,
        preserve_recent=5,
        auto_compress_threshold=30
    )
    
    print("\n✅ 集成演示完成！")


def demo_advanced_usage():
    """演示高级用法"""
    print("\n=== 高级用法演示 ===\n")
    
    # 自定义压缩配置
    custom_config = CompressionConfig(
        max_messages=25,
        preserve_recent=6,
        preserve_system=True,
        min_importance_score=0.4,  # 更高的重要性阈值
        similarity_threshold=0.7,  # 更低的相似度阈值，更容易合并
        enable_summarization=True,
        max_summary_length=100
    )
    
    # 自定义回调函数
    def custom_callback(stats):
        print(f"🔔 自定义回调: 压缩完成，节省了{stats['estimated_original_tokens'] - stats['estimated_compressed_tokens']}个token")
    
    # 创建自定义应用
    app = EnhancedChatApp()
    app.context_manager = ContextManager(
        compression_config=custom_config,
        auto_compress_threshold=15,  # 更低的阈值
        compression_callback=custom_callback
    )
    
    # 模拟长对话
    app.start_new_session("长对话测试")
    
    # 添加更多消息来触发压缩
    for i in range(20):
        app.add_message("user", f"这是第{i+1}个用户消息，包含一些测试内容。")
        app.add_message("assistant", f"这是第{i+1}个助手回复，提供相应的帮助信息。")
    
    print(f"\n📊 最终统计:")
    final_stats = app.get_session_stats()
    print(f"   最终消息数: {final_stats['message_count']}")
    print(f"   压缩次数: {final_stats['compression_stats']['total_compressions']}")


if __name__ == "__main__":
    demo_integration()
    demo_advanced_usage()