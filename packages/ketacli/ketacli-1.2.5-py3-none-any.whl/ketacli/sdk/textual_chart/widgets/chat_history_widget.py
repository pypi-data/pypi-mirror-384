"""聊天历史组件模块"""

from datetime import datetime
from typing import Dict, List, Optional

from textual.containers import ScrollableContainer

from .message_widget import MessageWidget, StreamingMessageWidget, ToolCallWidget
from ..token_calculator import TokenStats, calculate_token_stats


class ChatHistoryWidget(ScrollableContainer):
    """对话历史显示组件"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages: List[Dict] = []
        self._current_streaming_widget = None  # 当前流式消息组件
        
    def add_message(self, role: str, content: str, token_stats: Optional[TokenStats] = None):
        """添加消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        message_data = {
            "role": role,
            "content": content,
            "timestamp": timestamp
        }
        
        # 获取当前上下文消息（不包括即将添加的消息）
        context_messages = [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
        
        # 添加到消息历史
        self.messages.append(message_data)
        
        # 创建消息组件并添加到界面
        message_widget = MessageWidget(
            role=role, 
            content=content, 
            timestamp=timestamp,
            token_stats=token_stats,
            context_messages=context_messages
        )
        self.mount(message_widget)
        
        # 滚动到底部
        self.scroll_end()
        
    def start_streaming_message(self, role: str) -> 'StreamingMessageWidget':
        """开始流式消息，返回流式消息组件"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 获取当前上下文消息
        context_messages = [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
        
        # 创建流式消息组件
        streaming_widget = StreamingMessageWidget(
            role=role, 
            timestamp=timestamp,
            context_messages=context_messages
        )
        self.mount(streaming_widget)
        self._current_streaming_widget = streaming_widget
        
        # 滚动到底部
        self.scroll_end()
        
        return streaming_widget
        
    def finish_streaming_message(self, final_content: str):
        """完成流式消息，将其转换为普通消息"""
        if self._current_streaming_widget:
            # 添加到消息历史
            message_data = {
                "role": self._current_streaming_widget.role,
                "content": final_content,
                "timestamp": self._current_streaming_widget.timestamp
            }
            self.messages.append(message_data)
            
            # 清除当前流式组件引用
            self._current_streaming_widget = None
        
    def add_tool_call(self, tool_name: str, arguments: str, result: str = None, success: bool = True, result_obj: Optional[Dict] = None):
        """添加工具调用显示"""
        tool_widget = ToolCallWidget(tool_name, arguments, result, success, result_obj=result_obj)
        self.mount(tool_widget)
        self.scroll_end()
        
    def clear_history(self):
        """清空对话历史"""
        self.messages.clear()
        self._current_streaming_widget = None
        # 移除所有子组件
        for child in list(self.children):
            child.remove()
    
    def get_total_tokens(self) -> int:
        """获取当前对话的总token数"""
        if not self.messages:
            return 0
        
        # 计算所有消息的token总数
        total_tokens = 0
        for i, message in enumerate(self.messages):
            context_messages = self.messages[:i]  # 当前消息之前的所有消息作为上下文
            current_message = {"role": message["role"], "content": message["content"]}
            
            stats = calculate_token_stats(
                current_message=current_message,
                context_messages=[{"role": msg["role"], "content": msg["content"]} for msg in context_messages]
            )
            total_tokens += stats.total_tokens
        
        return total_tokens
    
    def get_context_for_message(self, message_index: int) -> List[Dict]:
        """获取指定消息的上下文"""
        if message_index < 0 or message_index >= len(self.messages):
            return []
        
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages[:message_index]]