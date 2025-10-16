"""上下文管理器

提供统一的上下文压缩和管理接口，方便集成到现有系统中。
"""

import json
import os
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from .context_compressor import ContextCompressor, CompressionConfig
from .data_models import ChatSession


class ContextManager:
    """上下文管理器"""
    
    def __init__(self, 
                 compression_config: CompressionConfig = None,
                 auto_compress_threshold: int = 100,
                 enable_auto_compression: bool = True,
                 compression_callback: Callable[[Dict[str, Any]], None] = None):
        """
        初始化上下文管理器
        
        Args:
            compression_config: 压缩配置
            auto_compress_threshold: 自动压缩阈值（消息数量）
            enable_auto_compression: 是否启用自动压缩
            compression_callback: 压缩完成后的回调函数
        """
        self.compressor = ContextCompressor(compression_config)
        self.auto_compress_threshold = auto_compress_threshold
        self.enable_auto_compression = enable_auto_compression
        self.compression_callback = compression_callback
        
        # 压缩历史记录
        self.compression_history = []
    
    def process_messages(self, messages: List[Dict[str, Any]], 
                        force_compress: bool = False) -> List[Dict[str, Any]]:
        """
        处理消息列表，根据配置决定是否压缩
        
        Args:
            messages: 原始消息列表
            force_compress: 是否强制压缩
            
        Returns:
            处理后的消息列表
        """
        # 检查是否需要压缩
        should_compress = (
            force_compress or 
            (self.enable_auto_compression and 
             len(messages) >= self.auto_compress_threshold)
        )
        
        if not should_compress:
            return messages
        
        # 执行压缩
        compressed_messages = self.compressor.compress_messages(messages)
        
        # 记录压缩统计
        stats = self.compressor.get_compression_stats(messages, compressed_messages)
        self._record_compression(stats)
        
        # 执行回调
        if self.compression_callback:
            self.compression_callback(stats)
        
        return compressed_messages
    
    def compress_session(self, session: ChatSession, 
                        save_original: bool = True) -> ChatSession:
        """
        压缩会话
        
        Args:
            session: 原始会话
            save_original: 是否保存原始会话备份
            
        Returns:
            压缩后的会话
        """
        if save_original:
            self._backup_session(session)
        
        compressed_messages = self.process_messages(session.messages, force_compress=True)
        
        # 创建新的压缩会话
        compressed_session = ChatSession(
            session_id=session.session_id,
            title=session.title + " (已压缩)",
            created_at=session.created_at,
            updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            messages=compressed_messages
        )
        
        return compressed_session
    
    def get_compression_recommendation(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取压缩建议
        
        Args:
            messages: 消息列表
            
        Returns:
            压缩建议信息
        """
        message_count = len(messages)
        
        # 估算当前token使用量
        def estimate_tokens(msgs):
            total = 0
            for msg in msgs:
                content = msg.get("content", "")
                # 简单估算
                total += len(content) // 2  # 假设平均每2个字符1个token
            return total
        
        current_tokens = estimate_tokens(messages)
        
        # 模拟压缩效果
        if message_count > 10:
            simulated_compressed = self.compressor.compress_messages(messages)
            estimated_compressed_tokens = estimate_tokens(simulated_compressed)
            potential_savings = current_tokens - estimated_compressed_tokens
        else:
            potential_savings = 0
            estimated_compressed_tokens = current_tokens
        
        recommendation = {
            "should_compress": message_count >= self.auto_compress_threshold,
            "current_message_count": message_count,
            "estimated_current_tokens": current_tokens,
            "estimated_compressed_tokens": estimated_compressed_tokens,
            "potential_token_savings": potential_savings,
            "compression_ratio": estimated_compressed_tokens / current_tokens if current_tokens > 0 else 1,
            "recommendation_reason": self._get_recommendation_reason(message_count, potential_savings)
        }
        
        return recommendation
    
    def _get_recommendation_reason(self, message_count: int, potential_savings: int) -> str:
        """获取推荐原因"""
        if message_count < self.auto_compress_threshold:
            return "消息数量较少，暂不需要压缩"
        elif potential_savings > 1000:
            return f"可节省约{potential_savings}个token，建议立即压缩"
        elif potential_savings > 500:
            return f"可节省约{potential_savings}个token，建议压缩"
        else:
            return "压缩收益较小，可选择性压缩"
    
    def _record_compression(self, stats: Dict[str, Any]):
        """记录压缩统计"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "stats": stats
        }
        self.compression_history.append(record)
        
        # 保持历史记录数量限制
        if len(self.compression_history) > 100:
            self.compression_history = self.compression_history[-50:]
    
    def _backup_session(self, session: ChatSession):
        """备份会话"""
        # 这里可以实现会话备份逻辑
        # 例如保存到特定的备份目录
        pass
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """获取压缩统计信息"""
        if not self.compression_history:
            return {
                "total_compressions": 0,
                "average_message_reduction": 0,
                "average_token_reduction": 0,
                "total_tokens_saved": 0
            }
        
        total_compressions = len(self.compression_history)
        message_reductions = []
        token_reductions = []
        total_tokens_saved = 0
        
        for record in self.compression_history:
            stats = record["stats"]
            message_reductions.append(stats.get("message_reduction_ratio", 0))
            token_reductions.append(stats.get("token_reduction_ratio", 0))
            
            original_tokens = stats.get("estimated_original_tokens", 0)
            compressed_tokens = stats.get("estimated_compressed_tokens", 0)
            total_tokens_saved += original_tokens - compressed_tokens
        
        return {
            "total_compressions": total_compressions,
            "average_message_reduction": sum(message_reductions) / len(message_reductions),
            "average_token_reduction": sum(token_reductions) / len(token_reductions),
            "total_tokens_saved": total_tokens_saved,
            "last_compression": self.compression_history[-1]["timestamp"] if self.compression_history else None
        }
    
    def update_config(self, **kwargs):
        """更新压缩配置"""
        config_dict = {
            "max_messages": kwargs.get("max_messages", self.compressor.config.max_messages),
            "preserve_recent": kwargs.get("preserve_recent", self.compressor.config.preserve_recent),
            "preserve_system": kwargs.get("preserve_system", self.compressor.config.preserve_system),
            "min_importance_score": kwargs.get("min_importance_score", self.compressor.config.min_importance_score),
            "similarity_threshold": kwargs.get("similarity_threshold", self.compressor.config.similarity_threshold),
            "enable_summarization": kwargs.get("enable_summarization", self.compressor.config.enable_summarization),
            "max_summary_length": kwargs.get("max_summary_length", self.compressor.config.max_summary_length)
        }
        
        self.compressor.config = CompressionConfig(**config_dict)
        
        # 更新自动压缩阈值
        if "auto_compress_threshold" in kwargs:
            self.auto_compress_threshold = kwargs["auto_compress_threshold"]
        
        if "enable_auto_compression" in kwargs:
            self.enable_auto_compression = kwargs["enable_auto_compression"]


class SessionContextManager:
    """会话上下文管理器
    
    专门用于管理ChatSession的上下文压缩
    """
    
    def __init__(self, context_manager: ContextManager = None):
        self.context_manager = context_manager or ContextManager()
    
    def auto_manage_session(self, session: ChatSession) -> ChatSession:
        """自动管理会话上下文"""
        if not session or not session.messages:
            return session
        
        # 检查是否需要压缩
        recommendation = self.context_manager.get_compression_recommendation(session.messages)
        
        if recommendation["should_compress"]:
            # 执行压缩
            compressed_session = self.context_manager.compress_session(session)
            return compressed_session
        
        return session
    
    def prepare_for_ai_request(self, session: ChatSession, 
                              max_context_tokens: int = 4000) -> List[Dict[str, Any]]:
        """
        为AI请求准备上下文
        
        Args:
            session: 会话对象
            max_context_tokens: 最大上下文token数
            
        Returns:
            准备好的消息列表
        """
        if not session or not session.messages:
            return []
        
        messages = session.messages.copy()
        
        # 估算当前token数
        def estimate_tokens(msgs):
            total = 0
            for msg in msgs:
                content = msg.get("content", "")
                total += len(content) // 2
            return total
        
        current_tokens = estimate_tokens(messages)
        
        # 如果超出限制，进行压缩
        if current_tokens > max_context_tokens:
            # 动态调整压缩配置
            target_messages = max(10, len(messages) * max_context_tokens // current_tokens)
            
            # 临时调整配置
            original_config = self.context_manager.compressor.config
            temp_config = CompressionConfig(
                max_messages=target_messages,
                preserve_recent=min(5, target_messages // 2),
                preserve_system=True,
                enable_summarization=True
            )
            
            self.context_manager.compressor.config = temp_config
            
            try:
                messages = self.context_manager.process_messages(messages, force_compress=True)
            finally:
                # 恢复原配置
                self.context_manager.compressor.config = original_config
        
        return messages


# 全局实例
default_context_manager = ContextManager()
default_session_context_manager = SessionContextManager(default_context_manager)


def compress_messages(messages: List[Dict[str, Any]], 
                     config: CompressionConfig = None) -> List[Dict[str, Any]]:
    """便捷函数：压缩消息列表"""
    if config:
        compressor = ContextCompressor(config)
        return compressor.compress_messages(messages)
    else:
        return default_context_manager.process_messages(messages, force_compress=True)


def get_compression_recommendation(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """便捷函数：获取压缩建议"""
    return default_context_manager.get_compression_recommendation(messages)


def prepare_session_for_ai(session: ChatSession, 
                          max_context_tokens: int = 4000) -> List[Dict[str, Any]]:
    """便捷函数：为AI请求准备会话上下文"""
    return default_session_context_manager.prepare_for_ai_request(session, max_context_tokens)