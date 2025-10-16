"""Token计算工具模块

提供消息token数量估算功能，支持单条消息和上下文token统计。
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TokenStats:
    """Token统计信息"""
    current_message_tokens: int  # 当前消息token数
    context_tokens: int  # 上下文总token数
    total_tokens: int = 0  # 总token数
    structural_overhead: int = 0  # 结构开销
    compression_ratio: float = 0.0  # 压缩比例（如果使用了压缩）
    
    def __post_init__(self):
        """计算总token数"""
        if self.total_tokens == 0:
            self.total_tokens = self.current_message_tokens + self.context_tokens
    
    def __str__(self) -> str:
        """格式化显示"""
        if self.compression_ratio > 0:
            return f"消息: {self.current_message_tokens} | 上下文: {self.context_tokens} | 总计: {self.total_tokens} | 压缩率: {self.compression_ratio:.1%}"
        else:
            return f"消息: {self.current_message_tokens} | 上下文: {self.context_tokens} | 总计: {self.total_tokens}"


class TokenCalculator:
    """Token计算器
    
    提供统一的token估算方法。
    """
    
    # 不同角色的token权重（用于更精确的估算）
    ROLE_WEIGHTS = {
        "system": 1.1,      # 系统消息通常包含更多结构化信息
        "user": 1.0,        # 用户消息基准权重
        "assistant": 1.2,   # AI回复通常更详细
        "tool": 0.8,        # 工具调用结果通常更简洁
        "function": 0.8     # 函数调用
    }
    
    # 特殊内容的token倍数
    CONTENT_MULTIPLIERS = {
        "code": 1.3,        # 代码内容token密度更高
        "json": 1.2,        # JSON结构化数据
        "markdown": 1.1,    # Markdown格式
        "plain": 1.0        # 普通文本
    }
    
    def __init__(self):
        """初始化token计算器"""
        pass
        
    def estimate_message_tokens(self, message: Dict[str, Any]) -> int:
        """估算单条消息的token数量
        
        Args:
            message: 消息字典，包含role、content等字段
            
        Returns:
            估算的token数量
        """
        if not isinstance(message, dict):
            return 0
            
        role = message.get("role", "user")
        content = message.get("content", "")
        
        # 基础token计算
        base_tokens = self._calculate_base_tokens(content)
        
        # 应用角色权重
        role_weight = self.ROLE_WEIGHTS.get(role, 1.0)
        weighted_tokens = int(base_tokens * role_weight)
        
        # 检查特殊内容类型
        content_type = self._detect_content_type(content)
        content_multiplier = self.CONTENT_MULTIPLIERS.get(content_type, 1.0)
        
        final_tokens = int(weighted_tokens * content_multiplier)
        
        # 添加消息结构开销（role、timestamp等）
        structure_overhead = 8
        
        # 处理工具调用
        if "tool_calls" in message:
            tool_calls = message["tool_calls"]
            if isinstance(tool_calls, list):
                for tool_call in tool_calls:
                    if isinstance(tool_call, dict):
                        # 工具调用名称和参数的token
                        tool_name = tool_call.get("function", {}).get("name", "")
                        tool_args = tool_call.get("function", {}).get("arguments", "")
                        final_tokens += int(self._calculate_base_tokens(tool_name) * 2)  # 名称权重更高
                        final_tokens += int(self._calculate_base_tokens(tool_args) * 1.2)
        
        # 保证返回整数
        return max(int(final_tokens + structure_overhead), 1)  # 至少1个token
    
    def estimate_context_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """估算整个上下文的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            上下文总token数
        """
        if not messages:
            return 0
            
        total_tokens = 0
        
        # 计算所有消息的token
        for message in messages:
            total_tokens += self.estimate_message_tokens(message)
        
        # 添加对话结构开销
        conversation_overhead = len(messages) * 3  # 每条消息的分隔符等
        
        # 保证返回整数
        return int(total_tokens + conversation_overhead)
    
    def calculate_token_stats(self, 
                            current_message: Dict[str, Any], 
                            context_messages: List[Dict[str, Any]] = None,
                            compression_ratio: float = 0.0) -> TokenStats:
        """计算完整的token统计信息
        
        Args:
            current_message: 当前消息
            context_messages: 上下文消息列表
            compression_ratio: 压缩比例（如果使用了压缩）
            
        Returns:
            TokenStats对象
        """
        message_tokens = self.estimate_message_tokens(current_message)
        
        if context_messages:
            context_tokens = self.estimate_context_tokens(context_messages)
        else:
            context_tokens = message_tokens
        
        return TokenStats(
            current_message_tokens=message_tokens,
            context_tokens=context_tokens,
            compression_ratio=compression_ratio
        )
    
    def _calculate_base_tokens(self, text: str) -> int:
        """计算文本的基础token数量
        
        使用多种启发式方法估算token数量。
        """
        if not text:
            return 0
        
        # 方法1: 基于字符数的估算（英文为主）
        char_based = len(text) / 4
        
        # 方法2: 基于单词数的估算
        words = len(text.split())
        word_based = words * 1.3  # 平均每个单词1.3个token
        
        # 方法3: 基于中文字符的估算
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        chinese_based = chinese_chars * 1.5  # 中文字符通常需要更多token
        
        # 方法4: 基于标点符号和特殊字符
        special_chars = len(re.findall(r'[^\w\s\u4e00-\u9fff]', text))
        special_based = special_chars * 0.8
        
        # 综合估算
        if chinese_chars > len(text) * 0.3:  # 中文内容为主
            base_estimate = chinese_based + special_based
        else:  # 英文内容为主
            base_estimate = max(char_based, word_based) + special_based
        
        return max(int(base_estimate), 1)
    
    def _detect_content_type(self, content: str) -> str:
        """检测内容类型"""
        if not content:
            return "plain"
        
        # 检测代码块
        if "```" in content or content.count("\n") > 5 and any(
            keyword in content for keyword in ["def ", "function ", "class ", "import ", "from "]
        ):
            return "code"
        
        # 检测JSON
        try:
            json.loads(content)
            return "json"
        except:
            pass
        
        # 检测Markdown
        if any(marker in content for marker in ["# ", "## ", "**", "*", "[", "](", "`"]):
            return "markdown"
        
        return "plain"
    



class ContextTokenTracker:
    """上下文token跟踪器
    
    跟踪整个对话过程中的token使用情况。
    """
    
    def __init__(self):
        self.calculator = TokenCalculator()
        self.message_history: List[Tuple[Dict[str, Any], TokenStats]] = []
        self.total_tokens_used = 0
    
    def add_message(self, message: Dict[str, Any], compression_ratio: float = 0.0) -> TokenStats:
        """添加新消息并计算token统计
        
        Args:
            message: 新消息
            compression_ratio: 压缩比例
            
        Returns:
            当前消息的token统计
        """
        # 获取当前上下文（所有历史消息）
        context_messages = [msg for msg, _ in self.message_history] + [message]
        
        # 计算token统计
        stats = self.calculator.calculate_token_stats(
            current_message=message,
            context_messages=context_messages,
            compression_ratio=compression_ratio
        )
        
        # 记录到历史
        self.message_history.append((message, stats))
        
        # 更新总计
        self.total_tokens_used += stats.current_message_tokens
        
        return stats
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话token使用摘要"""
        if not self.message_history:
            return {
                "total_messages": 0,
                "total_tokens": 0,
                "average_tokens_per_message": 0,
                "current_context_tokens": 0
            }
        
        current_context_tokens = self.message_history[-1][1].context_tokens if self.message_history else 0
        
        return {
            "total_messages": len(self.message_history),
            "total_tokens": self.total_tokens_used,
            "average_tokens_per_message": self.total_tokens_used / len(self.message_history),
            "current_context_tokens": current_context_tokens
        }
    
    def clear_history(self):
        """清空历史记录"""
        self.message_history.clear()
        self.total_tokens_used = 0


# 便捷函数
def estimate_message_tokens(message: Dict[str, Any]) -> int:
    """快速估算单条消息的token数量"""
    calculator = TokenCalculator()
    return calculator.estimate_message_tokens(message)


def estimate_context_tokens(messages: List[Dict[str, Any]]) -> int:
    """快速估算上下文token数量"""
    calculator = TokenCalculator()
    return calculator.estimate_context_tokens(messages)


def calculate_token_stats(current_message: Dict[str, Any], 
                         context_messages: List[Dict[str, Any]] = None,
                         compression_ratio: float = 0.0) -> TokenStats:
    """快速计算token统计信息"""
    calculator = TokenCalculator()
    return calculator.calculate_token_stats(current_message, context_messages, compression_ratio)