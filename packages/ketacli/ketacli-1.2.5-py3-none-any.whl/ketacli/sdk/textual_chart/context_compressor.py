"""上下文压缩算法

智能压缩聊天上下文，减少token消耗的同时保留关键信息。
"""

import re
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class CompressionConfig:
    """压缩配置"""
    max_messages: int = 50  # 压缩后最大消息数
    preserve_recent: int = 10  # 始终保留的最近消息数
    preserve_system: bool = True  # 是否保留系统消息
    min_importance_score: float = 0.3  # 最小重要性分数阈值
    similarity_threshold: float = 0.8  # 相似度合并阈值
    enable_summarization: bool = True  # 是否启用摘要功能
    max_summary_length: int = 200  # 摘要最大长度


@dataclass
class MessageScore:
    """消息评分结果"""
    message_index: int
    importance_score: float
    time_weight: float
    role_weight: float
    content_weight: float
    interaction_weight: float


class ContextCompressor:
    """上下文压缩器"""
    
    def __init__(self, config: CompressionConfig = None):
        self.config = config or CompressionConfig()
        
        # 角色权重配置
        self.role_weights = {
            "system": 1.0,
            "user": 1.2,       # 提升用户消息权重，优先保留
            "assistant": 0.75,
            "tool": 0.5        # 非文档类工具输出优先压缩
        }
        
        # 关键词权重配置
        self.keyword_patterns = {
            "question": (r"[？?]|如何|怎么|什么|为什么|能否|可以", 0.3),
            "error": (r"错误|error|失败|fail|异常|exception", 0.4),
            "code": (r"```|`[^`]+`|def |class |import |function", 0.3),
            "important": (r"重要|关键|注意|警告|warning|critical", 0.2),
            "request": (r"请|帮助|help|需要|want|require", 0.2),
            # 文档类查询与参考信息
            "doc": (r"文档|docs|指南|手册|reference|语法|spl|示例|example|说明", 0.35)
        }

        # 文档类工具函数名称（这些工具输出应优先保留）
        self.doc_tool_names = {"get_docs"}
        # 临时映射：tool_call_id -> function_name（在一次压缩流程中构建）
        self._tool_call_id_to_name: Dict[str, str] = {}
    
    def compress_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        压缩消息列表
        
        Args:
            messages: 原始消息列表
            
        Returns:
            压缩后的消息列表
        """
        if len(messages) <= self.config.max_messages:
            return messages
        
        # 0. 构建工具调用映射，便于识别文档类工具输出
        self._build_tool_call_map(messages)
        
        # 1. 计算消息重要性评分
        scores = self._calculate_message_scores(messages)
        
        # 2. 确定保留的消息
        preserved_messages = self._select_messages_to_preserve(messages, scores)
        
        # 3. 对剩余消息进行智能合并和摘要
        if self.config.enable_summarization:
            preserved_messages = self._apply_summarization(preserved_messages)
        
        # 4. 最终检查和调整
        final_messages = self._final_adjustment(preserved_messages)
        
        return final_messages
    
    def _calculate_message_scores(self, messages: List[Dict[str, Any]]) -> List[MessageScore]:
        """计算消息重要性评分"""
        scores = []
        total_messages = len(messages)
        
        for i, message in enumerate(messages):
            # 时间权重（越新权重越高）
            time_weight = (i + 1) / total_messages
            
            # 角色权重
            role = message.get("role", "user")
            role_weight = self.role_weights.get(role, 0.5)
            
            # 内容权重
            content_weight = self._calculate_content_weight(message)
            
            # 交互权重（考虑上下文关联）
            interaction_weight = self._calculate_interaction_weight(messages, i)
            
            # 综合重要性评分
            importance_score = (
                time_weight * 0.3 +
                role_weight * 0.25 +
                content_weight * 0.3 +
                interaction_weight * 0.15
            )
            
            scores.append(MessageScore(
                message_index=i,
                importance_score=importance_score,
                time_weight=time_weight,
                role_weight=role_weight,
                content_weight=content_weight,
                interaction_weight=interaction_weight
            ))
        
        return scores
    
    def _calculate_content_weight(self, message: Dict[str, Any]) -> float:
        """计算内容权重"""
        content = message.get("content", "")
        if not content:
            return 0.1
        
        weight = 0.5  # 基础权重
        content_lower = content.lower()
        
        # 检查关键词模式
        for pattern_name, (pattern, bonus) in self.keyword_patterns.items():
            if re.search(pattern, content_lower):
                weight += bonus
        
        # 内容长度权重（适中长度权重更高）
        length = len(content)
        if 50 <= length <= 500:
            weight += 0.1
        elif length > 1000:
            weight -= 0.1
        
        # 工具调用权重
        if message.get("tool_calls"):
            weight += 0.2
        
        # 文档类工具输出加权：role=tool 且工具为文档类
        if message.get("role") == "tool":
            tcid = message.get("tool_call_id")
            func_name = self._tool_call_id_to_name.get(tcid)
            if func_name and func_name in self.doc_tool_names:
                weight += 0.35  # 提升文档类工具输出的保留概率
            else:
                # 非文档类工具输出适度降低权重，促使摘要压缩
                weight -= 0.1
        
        return min(weight, 1.0)
    
    def _calculate_interaction_weight(self, messages: List[Dict[str, Any]], index: int) -> float:
        """计算交互权重（上下文关联性）"""
        if index == 0:
            return 0.5
        
        current_message = messages[index]
        prev_message = messages[index - 1]
        
        weight = 0.5
        
        # 问答对权重
        if (prev_message.get("role") == "user" and 
            current_message.get("role") == "assistant"):
            weight += 0.3
        
        # 工具调用链权重
        if (prev_message.get("tool_calls") and 
            current_message.get("role") == "tool"):
            # 文档类工具链更重要
            tcid = current_message.get("tool_call_id")
            func_name = self._tool_call_id_to_name.get(tcid)
            if func_name and func_name in self.doc_tool_names:
                weight += 0.4
            else:
                weight += 0.15
        
        # 连续对话权重
        if (current_message.get("role") == prev_message.get("role") and
            current_message.get("role") in ["user", "assistant"]):
            weight += 0.1
        
        return min(weight, 1.0)
    
    def _select_messages_to_preserve(self, messages: List[Dict[str, Any]], 
                                   scores: List[MessageScore]) -> List[Dict[str, Any]]:
        """选择要保留的消息"""
        preserved = []
        
        # 1. 保留系统消息
        if self.config.preserve_system:
            for i, message in enumerate(messages):
                if message.get("role") == "system":
                    preserved.append((i, message))
        
        # 2. 保留最近的消息
        recent_start = max(0, len(messages) - self.config.preserve_recent)
        for i in range(recent_start, len(messages)):
            if messages[i].get("role") != "system":  # 避免重复添加系统消息
                preserved.append((i, messages[i]))
        
        # 3. 根据重要性评分选择其他消息
        remaining_slots = self.config.max_messages - len(preserved)
        if remaining_slots > 0:
            # 排除已保留的消息
            preserved_indices = {idx for idx, _ in preserved}
            candidate_scores = [s for s in scores if s.message_index not in preserved_indices]
            
            # 按重要性排序
            candidate_scores.sort(key=lambda x: x.importance_score, reverse=True)
            
            # 选择高分消息
            for score in candidate_scores[:remaining_slots]:
                if score.importance_score >= self.config.min_importance_score:
                    preserved.append((score.message_index, messages[score.message_index]))
        
        # 按原始顺序排序
        preserved.sort(key=lambda x: x[0])
        return [msg for _, msg in preserved]
    
    def _apply_summarization(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """应用摘要功能"""
        if len(messages) <= self.config.max_messages:
            return messages
        
        # 识别可以摘要的消息段
        summarizable_segments = self._identify_summarizable_segments(messages)
        
        result = []
        i = 0
        
        while i < len(messages):
            # 检查当前位置是否在可摘要段中
            in_segment = False
            for start, end in summarizable_segments:
                if start <= i <= end:
                    # 创建摘要
                    segment_messages = messages[start:end+1]
                    summary = self._create_summary(segment_messages)
                    result.append({
                        "role": "system",
                        "content": f"[摘要] {summary}",
                        "is_summary": True
                    })
                    i = end + 1
                    in_segment = True
                    break
            
            if not in_segment:
                result.append(messages[i])
                i += 1
        
        return result
    
    def _identify_summarizable_segments(self, messages: List[Dict[str, Any]]) -> List[Tuple[int, int]]:
        """识别可以摘要的消息段"""
        segments = []
        current_segment_start = None
        
        for i, message in enumerate(messages):
            role = message.get("role")
            
            # 跳过系统消息和最近的消息
            if (role == "system" or 
                i >= len(messages) - self.config.preserve_recent):
                if current_segment_start is not None:
                    if i - current_segment_start >= 3:  # 至少3条消息才摘要
                        segments.append((current_segment_start, i - 1))
                    current_segment_start = None
                continue
            
            # 将用户消息与文档类工具消息作为摘要段的边界，避免被摘要
            is_doc_tool = False
            if role == "tool":
                tcid = message.get("tool_call_id")
                func_name = self._tool_call_id_to_name.get(tcid)
                is_doc_tool = bool(func_name and func_name in self.doc_tool_names)

            if role == "user" or is_doc_tool:
                # 关闭当前摘要段（如存在）
                if current_segment_start is not None and i - current_segment_start >= 3:
                    segments.append((current_segment_start, i - 1))
                current_segment_start = None
                continue

            # 开始或继续摘要段（assistant与非文档工具输出优先压缩）
            if current_segment_start is None:
                current_segment_start = i
        
        # 处理最后一段
        if (current_segment_start is not None and 
            len(messages) - current_segment_start >= 3):
            segments.append((current_segment_start, len(messages) - self.config.preserve_recent - 1))
        
        return segments

    def _build_tool_call_map(self, messages: List[Dict[str, Any]]) -> None:
        """构建 tool_call_id -> function_name 的映射，用于识别文档类工具消息"""
        mapping: Dict[str, str] = {}
        for msg in messages:
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                for tc in msg.get("tool_calls", []) or []:
                    try:
                        tcid = (tc or {}).get("id")
                        fname = (tc or {}).get("function", {}).get("name")
                        if tcid and fname:
                            mapping[tcid] = fname
                    except Exception:
                        continue
        self._tool_call_id_to_name = mapping
    
    def _create_summary(self, messages: List[Dict[str, Any]]) -> str:
        """创建消息段摘要"""
        if not messages:
            return ""
        
        # 提取关键信息
        topics = set()
        key_actions = []
        errors = []
        
        for message in messages:
            content = message.get("content", "")
            role = message.get("role", "")
            
            # 提取主题
            if role == "user":
                # 提取用户问题的关键词
                words = re.findall(r'\b\w+\b', content.lower())
                topics.update(word for word in words if len(word) > 3)
            
            # 提取关键动作
            if message.get("tool_calls"):
                for tool_call in message["tool_calls"]:
                    func_name = tool_call.get("function", {}).get("name", "")
                    if func_name:
                        key_actions.append(func_name)
            
            # 提取错误信息
            if "错误" in content or "error" in content.lower():
                errors.append(content[:50] + "..." if len(content) > 50 else content)
        
        # 构建摘要
        summary_parts = []
        
        if topics:
            main_topics = list(topics)[:3]  # 取前3个主题
            summary_parts.append(f"讨论了{', '.join(main_topics)}等话题")
        
        if key_actions:
            unique_actions = list(set(key_actions))[:3]
            summary_parts.append(f"执行了{', '.join(unique_actions)}等操作")
        
        if errors:
            summary_parts.append(f"遇到{len(errors)}个错误")
        
        if not summary_parts:
            summary_parts.append(f"包含{len(messages)}条消息的对话")
        
        summary = "；".join(summary_parts)
        
        # 限制摘要长度
        if len(summary) > self.config.max_summary_length:
            summary = summary[:self.config.max_summary_length - 3] + "..."
        
        return summary
    
    def _final_adjustment(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """最终调整和优化"""
        if len(messages) <= self.config.max_messages:
            return messages
        
        # 如果仍然超出限制，优先保留最重要的消息
        # 重新计算评分
        scores = self._calculate_message_scores(messages)
        scores.sort(key=lambda x: x.importance_score, reverse=True)
        
        # 保留最高分的消息
        keep_indices = set()
        
        # 确保保留系统消息和最近消息
        for i, message in enumerate(messages):
            if (message.get("role") == "system" or 
                i >= len(messages) - self.config.preserve_recent):
                keep_indices.add(i)
        
        # 添加高分消息直到达到限制
        for score in scores:
            if len(keep_indices) >= self.config.max_messages:
                break
            keep_indices.add(score.message_index)
        
        # 按原始顺序返回
        result = []
        for i, message in enumerate(messages):
            if i in keep_indices:
                result.append(message)
        
        return result
    
    def get_compression_stats(self, original_messages: List[Dict[str, Any]], 
                            compressed_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取压缩统计信息"""
        original_count = len(original_messages)
        compressed_count = len(compressed_messages)
        
        # 估算token数量（简单估算：中文1字符≈1token，英文1词≈1token）
        def estimate_tokens(messages):
            total = 0
            for msg in messages:
                content = msg.get("content", "")
                # 简单估算：中文字符数 + 英文单词数
                chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
                english_words = len(re.findall(r'\b[a-zA-Z]+\b', content))
                total += chinese_chars + english_words
            return total
        
        original_tokens = estimate_tokens(original_messages)
        compressed_tokens = estimate_tokens(compressed_messages)
        
        return {
            "original_message_count": original_count,
            "compressed_message_count": compressed_count,
            "message_reduction_ratio": (original_count - compressed_count) / original_count if original_count > 0 else 0,
            "estimated_original_tokens": original_tokens,
            "estimated_compressed_tokens": compressed_tokens,
            "token_reduction_ratio": (original_tokens - compressed_tokens) / original_tokens if original_tokens > 0 else 0,
            "compression_efficiency": compressed_count / original_count if original_count > 0 else 1
        }