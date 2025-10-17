"""主应用类"""

import asyncio
from datetime import datetime
import os
import logging
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, Button
from textual.worker import Worker
from textual import on

from .data_models import ChatSession, SessionManager
from .widgets import (
    ModelSelectorWidget, ChatHistoryWidget, ChatInputWidget, 
    CustomTextArea, ToolsListModal, SessionHistoryModal, ContextWindowModal,
    ModelConfigManagerWidget
)
from .widgets.config_widgets import ModelConfigModal
from .styles import CSS
from .context_manager import ContextManager, SessionContextManager
from .token_calculator import calculate_token_stats
from ketacli.sdk.ai.client import AIClient
from ketacli.sdk.ai.function_call import function_registry, function_executor
from ketacli.sdk.ai.tool_output_compressor import compress_if_large
from textual.widget import Widget

# 轻量日志：写入到仓库根目录的 log/textual_debug.log
logger = logging.getLogger("ketacli.textual")
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        log_dir = os.path.join(base_dir, "log")
        os.makedirs(log_dir, exist_ok=True)
        fh = logging.FileHandler(os.path.join(log_dir, "textual_debug.log"))
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(fh)
    except Exception:
        # 若文件日志初始化失败，不影响运行
        pass


class InteractiveChatApp(App):
    """交互式聊天应用"""
    
    CSS = CSS
    
    BINDINGS = [
        ("q", "quit", "退出"),
        ("c", "clear_chat", "清空对话"),
        ("n", "clear_chat", "新会话"),
        ("t", "show_tools", "显示工具"),
        ("i", "focus_input", "聚焦输入框"),
        ("h", "show_session_history", "历史会话"),
        ("m", "show_model_config", "模型配置"),
        ("k", "show_context", "上下文"),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ai_client = None
        self.conversation_history = []
        self.session_manager = SessionManager()
        self.current_session = None
        self._chat_in_progress = False
        self._current_ai_task = None  # 当前AI响应任务
        
        # 上下文管理器
        self.context_manager = ContextManager()
        self.session_context_manager = SessionContextManager()

        # 工具启用状态：默认开启资源列出、日志/指标搜索、获取文档
        # 对应函数名：list_assets, list_queryable_assets, search_data_for_log, search_data_for_metric, get_docs
        self.enabled_tools = {
            "list_assets",
            "list_queryable",
            "search_data",
            "get_repo_fields",
            "get_docs",
        }
        
        # 通知过滤配置：仅展示重要信息（error/warning/success）
        self._important_severities = {"error", "warning", "success"}
        # 明显的调试/噪音标记，统一屏蔽
        self._debug_markers = ("DEBUG", "🧪", "🔧", "➡️", "🔗", "⚙️", "📩", "🛠️", "🧹", "🔁")

    def notify(self, message, **kwargs):
        """统一过滤通知，仅保留重要提示。

        规则：
        - 严重级别在 error/warning/success 的提示保留；
        - 包含明显调试标记（如 DEBUG/🧪/🔧 等）的提示直接忽略；
        - 其他 info 级别或未设严重级别的提示忽略。
        """
        try:
            severity = kwargs.get("severity", "info")
            text = str(message)
        except Exception:
            severity = kwargs.get("severity", "info")
            text = message

        # 屏蔽明显的调试/噪音提示
        if any(marker in (text or "") for marker in self._debug_markers):
            return

        # 仅保留重要等级
        if severity not in self._important_severities:
            return

        # 透传给父类实现
        return super().notify(message, **kwargs)
        
    def compose(self) -> ComposeResult:
        """构建应用UI"""
        yield Header()
        
        with Container(classes="chat-container"):
            yield Static("🤖 AI智能对话助手", classes="chat-header")
            
            with Vertical(classes="chat-main"):
                yield ModelSelectorWidget(id="model-selector")
                yield ChatHistoryWidget(id="chat-history", classes="chat-history")
                yield ChatInputWidget(id="chat-input", classes="chat-input-container")
                
        yield Footer()
        
    def on_mount(self) -> None:
        """应用启动时的初始化"""
        self._initialize_ai_client()
        self._add_welcome_message()
        
    def _initialize_ai_client(self):
        """初始化AI客户端"""
        try:
            # 修正系统提示词文件路径，指向 sdk/ai/prompts/system.md
            prompt_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../ai/prompts/system.md")
            )
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
            self.ai_client = AIClient(system_prompt=system_prompt)
        except Exception as e:
            self.notify(f"AI客户端初始化失败: {e}", severity="error")
            
    def _add_welcome_message(self):
        """添加欢迎消息"""
        chat_history = self.query_one("#chat-history", ChatHistoryWidget)
        welcome_msg = f"""👋 欢迎使用KetaOps AI智能对话助手！

我可以帮助您：
- 📊 数据查询和分析
- 🔍 智能搜索
- 📈 资源监控
- 🛠️ 系统管理

推荐示例：
- 对当前系统进行巡检
- 查询traceid为xxx的记录，分析其潜在的性能或异常
- 创建一个repo、soucetype等资源
- 查询logs_keta仓库中的异常日志并分析

请输入您的问题，我会尽力为您提供帮助。

当前已启用工具：{', '.join([f'`{x}`' for x in self.enabled_tools]) or '无'}。您也可以按 `T` 查看可用的工具列表来启用或关闭工具开关。"""
        
        chat_history.add_message("assistant", welcome_msg)

    def _get_enabled_tools_openai_format(self):
        """获取已启用工具的OpenAI格式定义列表"""
        try:
            all_tools = function_registry.get_openai_tools_format() or []
            if not self.enabled_tools:
                return []
            filtered = []
            for t in all_tools:
                fn = (t or {}).get("function", {})
                nm = fn.get("name")
                if nm and nm in self.enabled_tools:
                    filtered.append(t)
            return filtered
        except Exception:
            return []
        
    def on_chat_input_widget_stop_requested(self, message: ChatInputWidget.StopRequested) -> None:
        """处理停止请求"""
        if self._current_ai_task:
            self._current_ai_task.cancel()
            self._current_ai_task = None
            self._chat_in_progress = False
            
            # 重置按钮状态
            chat_input = self.query_one("#chat-input", ChatInputWidget)
            chat_input.set_processing(False)
            
            # 显示停止消息
            chat_history = self.query_one("#chat-history", ChatHistoryWidget)
            if chat_history._current_streaming_widget:
                chat_history.finish_streaming_message("**[已停止响应]**")
            
            self.notify("已停止AI响应", severity="success")

    def on_chat_input_widget_message_sent(self, message: ChatInputWidget.MessageSent) -> None:
        """处理用户发送的消息"""
        if self._chat_in_progress:
            chat_input = self.query_one("#chat-input", ChatInputWidget)
            chat_input.set_loading(False)
            # 进度提示弱化，减少噪音
            self.notify("对话正在进行中，请稍候...", severity="info")
            return
            
        user_message = message.message
        chat_history = self.query_one("#chat-history", ChatHistoryWidget)
        
        # 如果是新会话，创建会话
        if not self.current_session:
            self.current_session = ChatSession.create_new()
        
        # 添加用户消息到历史，计算token统计
        model_selector = self.query_one("#model-selector", ModelSelectorWidget)
        selected_model = model_selector.get_selected_model() or "gpt-3.5-turbo"
        
        # 计算用户消息的token统计
        user_msg_dict = {"role": "user", "content": user_message}
        context_messages = [{"role": msg["role"], "content": msg["content"]} for msg in self.conversation_history]
        user_token_stats = calculate_token_stats(
            current_message=user_msg_dict,
            context_messages=context_messages
        )
        
        chat_history.add_message("user", user_message, token_stats=user_token_stats)
        
        # 设置处理状态
        chat_input = self.query_one("#chat-input", ChatInputWidget)
        chat_input.set_processing(True)
        
        # 异步处理AI响应
        self._current_ai_task = self.run_worker(self._process_ai_response(user_message))
        
    async def _process_ai_response(self, user_message: str):
        """处理AI响应"""
        if not self.ai_client:
            self.notify("AI客户端未初始化", severity="error")
            return
            
        self._chat_in_progress = True
        chat_history = self.query_one("#chat-history", ChatHistoryWidget)
        model_selector = self.query_one("#model-selector", ModelSelectorWidget)
        
        try:
            # 获取选中的模型
            selected_model = model_selector.get_selected_model()
            if selected_model:
                self.ai_client = AIClient(
                    system_prompt=self.ai_client.system_prompt,
                    model_name=selected_model
                )
            # 增强系统提示词：统一工具调用为 auto，并要求“调用一次工具后先分析输出结论，避免重复调用”
            def _augment_system_prompt(base: str) -> str:
                rules = (
                    "你是一个可靠的助手，工具调用策略为自动模式。\n"
                    "当你决定调用工具时，请遵循以下规则：\n"
                    "1) 每轮至多调用一个工具；调用后必须基于工具结果进行分析并输出明确文本结论。\n"
                    "2) 避免连续多次重复调用同一工具或在已具备足够信息时再次调用。\n"
                    "3) 如工具调用失败，请解释原因并给出替代方案或推断结论。\n"
                    "4) 仅在明确缺少信息且无法产出结论时，才再次考虑调用工具。\n"
                    "5) 不要返回只有工具调用而没有任何文本内容的响应。\n"
                )
                try:
                    base = (base or "").strip()
                except Exception:
                    base = ""
                return (base + "\n\n" + rules) if base else rules
            try:
                self.ai_client.system_prompt = _augment_system_prompt(self.ai_client.system_prompt)
            except Exception:
                pass
            
            # 准备对话历史，应用上下文压缩
            current_message = {"role": "user", "content": user_message}

            # 工具消息规范化：移除无前置 tool_calls 的孤立工具消息（OpenAI规范）
            def _sanitize_tool_messages(messages: list, provider: str) -> list:
                try:
                    prov = (provider or "").lower()
                except Exception:
                    prov = ""
                # 仅在 OpenAI 风格下清理
                if "openai" not in prov:
                    return messages
                sanitized = []
                # 记录最近一次 assistant(tool_calls) 的ID集合
                allowed_ids = set()
                for msg in messages:
                    role = msg.get("role")
                    if role == "assistant":
                        tool_calls = msg.get("tool_calls") or []
                        allowed_ids = set([
                            tc.get("id") for tc in tool_calls if isinstance(tc, dict)
                        ])
                        sanitized.append(msg)
                    elif role == "tool":
                        tool_id = msg.get("tool_call_id")
                        if tool_id and tool_id in allowed_ids:
                            sanitized.append(msg)
                        # 否则丢弃该孤立工具消息
                    else:
                        # 一旦出现非工具消息，重置允许集，避免跨段误配
                        allowed_ids = set()
                        sanitized.append(msg)
                return sanitized

            # 检查是否需要压缩
            if len(self.conversation_history) > 20:  # 当消息数量超过20时考虑压缩
                # 使用上下文管理器进行压缩（替换不存在的 compress_context 为 process_messages）
                # 将最大保留消息数调整为15
                self.context_manager.update_config(max_messages=15)

                original_messages = self.conversation_history
                compressed_messages = self.context_manager.process_messages(
                    original_messages, force_compress=True
                )
                # 在压缩后执行工具消息规范化，避免 OpenAI 400 错误
                provider = getattr(self.ai_client.model_config, "provider", "")
                sanitized_messages = _sanitize_tool_messages(compressed_messages, provider)

                # 显示压缩统计信息（依据即时统计信息）
                if len(compressed_messages) < len(original_messages):
                    stats = self.context_manager.compressor.get_compression_stats(
                        original_messages, compressed_messages
                    )
                    tokens_saved = max(
                        0,
                        stats.get("estimated_original_tokens", 0)
                        - stats.get("estimated_compressed_tokens", 0)
                    )
                    compression_info = (
                        f"🗜️ 上下文已压缩: "
                        f"{len(original_messages)}→{len(compressed_messages)}条消息, "
                        f"节省{tokens_saved}个token"
                    )
                    self.notify(compression_info, timeout=3)

                # 如果有被移除的孤立工具消息，提示用户
                removed_count = len(compressed_messages) - len(sanitized_messages)
                if removed_count > 0:
                    self.notify(f"已移除 {removed_count} 条不合规的工具消息，避免请求错误", severity="warning")

                messages = sanitized_messages + [current_message]
            else:
                messages = self.conversation_history + [current_message]

            # 额外修复：严格校验并重建 OpenAI 工具消息配对序列
            def _enforce_openai_tool_sequence(msgs: list) -> tuple[list, int, int]:
                sanitized = []
                removed_assistant = 0
                removed_tool = 0
                i = 0
                n = len(msgs)
                while i < n:
                    msg = msgs[i]
                    role = msg.get("role")
                    if role != "assistant":
                        # 丢弃任何无前置assistant.tool_calls的孤立tool消息
                        if role == "tool":
                            removed_tool += 1
                        else:
                            sanitized.append(msg)
                        i += 1
                        continue

                    # assistant
                    tool_calls = msg.get("tool_calls") or []
                    if not tool_calls:
                        sanitized.append(msg)
                        i += 1
                        continue

                    # 有tool_calls，检查紧随其后的tool消息配对
                    ids = [tc.get("id") for tc in tool_calls if isinstance(tc, dict) and tc.get("id")]
                    j = i + 1
                    matched_ids = []
                    collected_tools = []
                    while j < n and msgs[j].get("role") == "tool":
                        tcid = msgs[j].get("tool_call_id")
                        if tcid in ids:
                            matched_ids.append(tcid)
                            collected_tools.append(msgs[j])
                        else:
                            # 丢弃不匹配的tool消息
                            removed_tool += 1
                        j += 1

                    if len(set(ids)) == len(set(matched_ids)) and len(ids) > 0:
                        # 完整配对，保留assistant与对应tool消息
                        sanitized.append(msg)
                        sanitized.extend(collected_tools)
                    else:
                        # 配对不完整：为避免400，移除此assistant的tool_calls，并丢弃其后的tool消息段
                        new_msg = dict(msg)
                        new_msg.pop("tool_calls", None)
                        sanitized.append(new_msg)
                        removed_assistant += 1
                        # 丢弃其后的所有连续tool消息（已在上面统计）
                    i = j
                return sanitized, removed_assistant, removed_tool

            messages, removed_assistant, removed_tool = _enforce_openai_tool_sequence(messages)
            if removed_assistant or removed_tool:
                self.notify(
                    f"🧹 已规范化工具消息：移除不完整assistant {removed_assistant} 条/孤立tool {removed_tool} 条",
                    severity="warning",
                    timeout=4
                )
            
            # “继续”场景下强制工具调用：避免误走纯流式分支
            def _should_force_tool_call(msgs: list, user_text: str) -> bool:
                try:
                    text = (user_text or "").strip().lower()
                except Exception:
                    text = ""
                # 常见继续词
                continue_words = {"继续", "继续执行", "继续查询", "继续检索", "继续分析", "go on", "continue", "carry on"}
                force_by_text = text in continue_words or (len(text) <= 6 and any(w in text for w in {"继续", "go", "cont"}))
                # 历史中是否出现过工具调用
                has_prev_tool_calls = any(
                    (m.get("role") == "assistant" and (m.get("tool_calls") or []))
                    for m in self.conversation_history
                )
                # 若历史存在工具调用且当前为“继续”，则强制走工具分支
                return bool(force_by_text and has_prev_tool_calls)
            
            # 默认走工具调用路径，让模型自决是否调用工具；
            # 不在此处提前进行纯流式渲染。
            pass

            # 获取可用工具（仅传递已启用的工具到模型）
            tools = self._get_enabled_tools_openai_format()
            # 调试：显示工具数量与模型信息
            try:
                provider = getattr(self.ai_client.model_config, "provider", "")
                current_model = self.ai_client.get_current_model() if hasattr(self.ai_client, "get_current_model") else ""
                self.notify(f"🔧 当前模型: {current_model} / 提供方: {provider}，可用工具: {len(tools)}", timeout=3)
                # 若为“继续”触发的强制工具调用，提示一次
                if _should_force_tool_call(messages, user_message):
                    self.notify("➡️ 已因‘继续’与历史工具调用，强制走工具分支", timeout=4)
            except Exception:
                pass
            
            # 迭代上限改为读取模型配置，默认20
            try:
                max_iterations = getattr(self.ai_client.model_config, "max_iterations", 20) or 20
                if not isinstance(max_iterations, int) or max_iterations <= 0:
                    max_iterations = 20
            except Exception:
                max_iterations = 20
            iteration = 0
            # 新增：当前用户请求周期内的工具失败屏蔽标志与重复调用去重集合
            block_tool_retry_for_current_query = False
            executed_tool_signatures = set()
            
            while iteration < max_iterations:
                iteration += 1
                # 调试：每轮请求前提示当前消息数
                try:
                    self.notify(f"➡️ 第{iteration}轮工具请求，上下文消息数: {len(messages)}", timeout=2)
                except Exception:
                    pass

                # 在发送前再次严格规范配对，确保满足OpenAI约束
                try:
                    messages, ra, rt = _enforce_openai_tool_sequence(messages)
                    if ra or rt:
                        self.notify(
                            f"🧩 请求前已规范化：移除不完整assistant {ra} 条/孤立tool {rt} 条",
                            severity="warning",
                            timeout=3
                        )
                    # 展示最近一次配对情况
                    last_assistant_idx = None
                    for idx in range(len(messages)-1, -1, -1):
                        if messages[idx].get("role") == "assistant":
                            last_assistant_idx = idx
                            break
                    if last_assistant_idx is not None:
                        ids = [tc.get("id") for tc in messages[last_assistant_idx].get("tool_calls") or [] if isinstance(tc, dict) and tc.get("id")]
                        j = last_assistant_idx + 1
                        following = 0
                        while j < len(messages) and messages[j].get("role") == "tool":
                            following += 1
                            j += 1
                        if ids:
                            self.notify(f"🔗 最近assistant工具调用: {len(ids)}，后续tool消息: {following}", timeout=3)
                except Exception:
                    pass
                
                # 统一使用 auto 策略进行工具调用
                tool_choice_value = "auto"
                tools_for_request = tools
                response = await self.ai_client.chat_with_tools_async(
                    messages=messages,
                    tools=tools_for_request,
                    tool_choice=tool_choice_value
                )
                # 不再使用 required 强制调用，完全依赖 auto 与提示词约束
                
                # 调试：响应基础信息
                try:
                    content_len = len(response.content or "")
                    # 过滤出仅启用工具的调用
                    filtered_tool_calls = [
                        tc for tc in (response.tool_calls or [])
                        if ((tc or {}).get("function", {}).get("name") in self.enabled_tools)
                    ]
                    tc_len = len(filtered_tool_calls)
                    self.notify(f"📩 收到响应：内容长度 {content_len}，解析到工具调用 {tc_len} 个（已按启用工具过滤）", timeout=3)
                except Exception:
                    pass
                
                # 添加AI响应到对话历史
                assistant_message = {
                    "role": "assistant",
                    "content": response.content
                }
                # 根据启用的工具过滤模型返回的工具调用
                try:
                    disabled_called_names = []
                    # 保持与上方一致的过滤，并在禁用轮次下强制清空
                    filtered_tool_calls = [
                        tc for tc in (response.tool_calls or [])
                        if ((tc or {}).get("function", {}).get("name") in self.enabled_tools)
                    ]
                    # 保持 auto 策略，不再强制清空
                    # 去重：避免同一函数与相同参数的重复调用（同一用户请求周期内）
                    try:
                        import json
                        dedup = []
                        for tc in filtered_tool_calls:
                            fn = (tc or {}).get("function", {})
                            nm = fn.get("name")
                            args = fn.get("arguments", "{}")
                            try:
                                if isinstance(args, (dict, list)):
                                    args_norm = json.dumps(args, ensure_ascii=False, sort_keys=True)
                                else:
                                    args_norm = str(args)
                            except Exception:
                                args_norm = str(args)
                            sig = f"{nm}:{args_norm}"
                            if sig in executed_tool_signatures:
                                try:
                                    self.notify(f"♻️ 跳过重复工具调用: {nm}", severity="warning", timeout=3)
                                except Exception:
                                    pass
                                continue
                            executed_tool_signatures.add(sig)
                            dedup.append(tc)
                        filtered_tool_calls = dedup
                    except Exception:
                        pass
                    # 若存在被禁用的工具调用，告知用户并忽略它们
                    try:
                        disabled_called = [
                            (tc or {}).get("function", {}).get("name")
                            for tc in (response.tool_calls or [])
                            if ((tc or {}).get("function", {}).get("name") not in self.enabled_tools)
                        ]
                        disabled_called_names = disabled_called
                        if disabled_called:
                            # 顶部通知：提示未启用工具被忽略
                            self.notify(
                                f"🚫 检测到未启用的工具调用已被忽略：{', '.join([n for n in disabled_called if n][:6])}",
                                severity="warning",
                                timeout=4
                            )
                            # 在聊天消息中追加启用指引，保证用户在对话中也能看到
                            try:
                                preview = ", ".join([n for n in disabled_called if n][:6])
                                guidance = (
                                    f"⚠️ 检测到模型尝试调用未启用的工具：{preview}。该调用已被忽略。\n"
                                    "请按 `T` 或 `Ctrl+T` 打开工具列表启用所需工具，或继续输入让我在不使用工具的情况下回答。"
                                )
                                existing = (assistant_message.get("content") or "")
                                # 若已有文本回复，则在末尾追加指引；否则直接作为回复内容
                                if existing.strip():
                                    sep = "\n\n" if not existing.endswith("\n") else "\n"
                                    assistant_message["content"] = existing + sep + guidance
                                else:
                                    assistant_message["content"] = guidance
                            except Exception:
                                pass
                        
                    except Exception:
                        pass
                except Exception:
                    filtered_tool_calls = []

                # 若模型仅返回未启用的工具调用且没有文本内容，提供合理的助手提示
                try:
                    if (not filtered_tool_calls) and disabled_called_names and not (response.content or "").strip():
                        disabled_preview = ", ".join([n for n in disabled_called_names if n][:6])
                        fallback_text = (
                            f"⚠️ 检测到模型尝试调用未启用的工具：{disabled_preview}。该调用已被忽略。\n"
                            "请按 `Ctrl+T` 打开工具列表启用所需工具，或继续输入让我在不使用工具的情况下回答。"
                        )
                        assistant_message["content"] = fallback_text
                except Exception:
                    pass

                if filtered_tool_calls:
                    # 限制每轮仅执行一次工具调用，减少过度调用
                    try:
                        filtered_tool_calls = filtered_tool_calls[:1]
                        self.notify("🎯 为提升精准度：本轮仅执行1次工具调用并随后进行思考", severity="success", timeout=3)
                    except Exception:
                        pass
                    assistant_message["tool_calls"] = filtered_tool_calls
                    # 调试：列出工具名
                    try:
                        names = []
                        for tc in filtered_tool_calls:
                            fn = (tc or {}).get("function", {})
                            nm = fn.get("name")
                            if nm:
                                names.append(nm)
                        if names:
                            self.notify(f"🛠️ 将执行工具: {', '.join(names[:5])}", timeout=3)
                    except Exception:
                        pass
                    
                messages.append(assistant_message)
                
                # 显示AI响应（优先使用可能已追加指引的 assistant_message 内容）
                try:
                    assistant_content = (assistant_message.get("content") or "")
                    if assistant_content.strip():
                        assistant_msg_dict = {"role": "assistant", "content": assistant_content}
                        # 使用当前messages作为上下文（不包括即将添加的assistant消息）
                        context_for_assistant = messages[:-1] if messages else []
                        assistant_token_stats = calculate_token_stats(
                            current_message=assistant_msg_dict,
                            context_messages=context_for_assistant
                        )
                        chat_history.add_message("assistant", assistant_content, token_stats=assistant_token_stats)
                except Exception:
                    pass
                
                # 处理工具调用（仅执行已启用的工具）
                # 仅在允许工具且确实有调用时执行
                # 仅在允许工具且确实有调用时执行
                if filtered_tool_calls:
                    # 异步执行所有工具调用
                    tool_results = await function_executor.execute_from_tool_calls_async(filtered_tool_calls)
                    
                    # 处理工具执行结果
                    import json
                    for i, tool_result in enumerate(tool_results):
                        tool_call = filtered_tool_calls[i]
                        func_data = tool_call.get("function", {})
                        func_name = func_data.get("name")
                        func_args = func_data.get("arguments", "{}")
                        
                        if tool_result.get("success"):
                            result_val = tool_result.get("result", "")
                            # 若为特定可视化对象或结构化对象，分别处理用于UI与模型的内容
                            if isinstance(result_val, Widget):
                                # UI展示使用对象本身；模型消息使用简短占位说明
                                result_str = "(图表可视化结果)"
                                result_obj_for_ui = result_val
                            elif isinstance(result_val, (dict, list)):
                                try:
                                    result_str = json.dumps(result_val, ensure_ascii=False)
                                except Exception:
                                    result_str = str(result_val)
                                # 仅在dict时传递对象用于UI（目前UI只识别dict为结构化文本显示）
                                result_obj_for_ui = result_val if isinstance(result_val, dict) else None
                            else:
                                result_str = str(result_val) if result_val is not None else ""
                                result_obj_for_ui = None
                            if not result_str.strip():
                                result_str = "(结果为空)"
                            # 压缩过大的工具结果
                            compressed_text, was_compressed = compress_if_large(result_str, threshold=8000)
                            # 更新工具调用结果显示（界面展示用原文或压缩文），并传递原始对象用于渲染
                            chat_history.add_tool_call(
                                func_name,
                                func_args,
                                compressed_text if was_compressed else result_str,
                                True,
                                result_obj=result_obj_for_ui,
                            )
                            
                            # 添加工具结果到对话历史（发送给模型）
                            tool_message = {
                                "role": "tool",
                                "tool_call_id": tool_call.get("id", f"call_{func_name}"),
                                "content": compressed_text if was_compressed else result_str
                            }
                            messages.append(tool_message)
                            # 调试：工具执行成功
                            try:
                                self.notify(f"✅ 工具 {func_name} 执行成功", timeout=2)
                            except Exception:
                                pass
                        else:
                            error_msg = tool_result.get("error", "执行失败")
                            if not (error_msg or "").strip():
                                error_msg = "(错误信息为空)"
                            chat_history.add_tool_call(func_name, func_args, error_msg, False)
                            
                            tool_message = {
                                "role": "tool",
                                "tool_call_id": tool_call.get("id", f"call_{func_name}"),
                                "content": error_msg
                            }
                            messages.append(tool_message)
                            # 工具失败：本次用户请求周期内屏蔽后续强制重试与重复调用
                            block_tool_retry_for_current_query = True
                            # 调试：工具执行失败
                            try:
                                self.notify(f"❌ 工具 {func_name} 执行失败：{error_msg}", severity="warning", timeout=4, markup=False)
                            except Exception:
                                pass
                    
                    # 继续下一轮对话
                    continue
                else:
                    # 未返回结构化工具调用：增加详细调试信息，便于定位问题
                    try:
                        import re
                        provider = getattr(self.ai_client.model_config, "provider", "")
                        current_model = self.ai_client.get_current_model() if hasattr(self.ai_client, "get_current_model") else ""
                        tools = self._get_enabled_tools_openai_format()
                        tool_names = []
                        for t in tools:
                            fn = (t or {}).get("function", {})
                            nm = fn.get("name")
                            if nm:
                                tool_names.append(nm)
                        # 标记文本检测
                        markers = re.findall(r"<\|\s*tool_call_begin\s*\|>(.*?)<\|\s*tool_call_end\s*\|>", response.content or "", flags=re.DOTALL)
                        snippet = (response.content or "").strip().replace("\n", " ")[:300]
                        # 最近一次用户输入片段
                        last_user = ""
                        for idx in range(len(messages)-1, -1, -1):
                            if messages[idx].get("role") == "user":
                                last_user = (messages[idx].get("content") or "").strip().replace("\n", " ")[:120]
                                break
                        self.notify(
                            f"🧪 调试：模型未返回结构化工具调用 | 模型: {current_model}/{provider} | 工具数: {len(tools)} | 标记段: {len(markers)}",
                            severity="warning",
                            timeout=5,
                            markup=False
                        )
                        if tool_names:
                            self.notify(f"🧪 可用工具: {', '.join(tool_names[:6])}", timeout=4, markup=False)
                        if last_user:
                            self.notify(f"🧪 最近用户输入片段: {last_user}", timeout=4, markup=False)
                        if snippet:
                            self.notify(f"🧪 响应片段: {snippet}", timeout=5, markup=False)
                    except Exception:
                        pass
                    # 非工具轮次或模型未给出工具调用：结束本次响应
                    break
                    
            # 若达到迭代上限，给出明确提示并在聊天中写入说明
            if iteration >= max_iterations:
                try:
                    self.notify(
                        f"⚠️ 工具执行次数已达到上限（{max_iterations}），已停止继续。",
                        severity="warning",
                        timeout=5
                    )
                except Exception:
                    pass
                try:
                    chat_history.add_message(
                        "assistant",
                        (
                            f"工具执行次数已达到上限（{max_iterations}）。"
                            "如需继续，请输入“继续”让我接着执行，"
                            "或按 Ctrl+T 打开工具列表启用/调整所需工具后再试。"
                        )
                    )
                except Exception:
                    pass
            
            # 更新对话历史
            self.conversation_history = messages
            
        except Exception as e:
            chat_history.add_message("assistant", f"❌ 处理请求时出错: {str(e)}")
            
        finally:
            self._chat_in_progress = False
            self._current_ai_task = None
            # 清除加载状态和处理状态
            chat_input = self.query_one("#chat-input", ChatInputWidget)
            chat_input.set_loading(False)
            chat_input.set_processing(False)
            # 自动保存会话
            self._save_current_session()
            
    async def _stream_chat_async(self, messages):
        """异步流式聊天：实时推送chunk，避免等待全部完成"""
        import asyncio

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        done = asyncio.Event()
        yield_count = 0

        # 启动前记录一些上下文信息
        try:
            provider = getattr(self.ai_client.model_config, "provider", "")
            current_model = self.ai_client.get_current_model() if hasattr(self.ai_client, "get_current_model") else ""
            logger.debug(f"[stream] 启动: provider={provider}, model={current_model}, messages_len={len(messages) if isinstance(messages, list) else 1}")
        except Exception:
            pass

        def producer():
            try:
                for chunk in self.ai_client.stream_chat(messages):
                    # 将chunk安全地推送到异步队列
                    asyncio.run_coroutine_threadsafe(queue.put(chunk), loop)
            except Exception as e:
                try:
                    logger.error(f"[stream] 生产者异常: {type(e).__name__}: {e}")
                except Exception:
                    pass
                asyncio.run_coroutine_threadsafe(queue.put(f"\n[流式错误] {e}"), loop)
            finally:
                # 通知消费者结束
                loop.call_soon_threadsafe(done.set)

        # 在线程中运行同步的流式生成器
        producer_task = asyncio.create_task(asyncio.to_thread(producer))

        try:
            while True:
                # 如果生产者已结束且队列为空，则退出
                if done.is_set() and queue.empty():
                    break
                try:
                    chunk = await asyncio.wait_for(queue.get(), timeout=0.5)
                    yield_count += 1
                    yield chunk
                except asyncio.TimeoutError:
                    if done.is_set():
                        break
        finally:
            try:
                logger.debug(f"[stream] 结束: yielded={yield_count}, done={done.is_set()}, queue_empty={queue.empty()}")
            except Exception:
                pass
            await producer_task
            
    def _needs_tool_call(self, content: str) -> bool:
        """检测是否需要工具调用（增强版）
        
        目标：减少漏判，让常见数据检索/列表类请求自动走工具通道。
        """
        try:
            text = (content or "").strip()
        except Exception:
            text = ""
        if not text:
            return False

        # 基础关键字（中英文）
        base_keywords = [
            "搜索", "查询", "获取", "执行", "调用", "运行", "查看", "看下", "列出", "列表", "统计", "top", "limit",
            "search", "query", "get", "execute", "call", "run", "smart_search"
        ]

        # 常见模式：前N条、最近N条、limit N
        import re
        patterns = [
            r"前\s*\d+\s*条",
            r"最近\s*\d+\s*条",
            r"limit\s*\d+",
        ]

        text_lower = text.lower()
        if any(k in text for k in base_keywords) or any(re.search(p, text_lower) for p in patterns):
            return True

        # 涉及明显数据域词汇时也倾向使用工具
        domain_hints = ["事件", "日志", "记录", "仓库", "repo", "数据", "表", "查询语句"]
        if any(h in text for h in domain_hints):
            return True

        return False

    # 兜底方案暂不启用：改为强化调试信息，定位模型未返回 tool_calls 的原因

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击事件"""
        if event.button.id == "tools-button":
            # 保持与快捷键 Ctrl+T 一致：传入当前已启用工具以预选复选框
            try:
                self.push_screen(ToolsListModal(enabled_tools=self.enabled_tools))
            except Exception:
                # 回退：若异常则仍尝试打开，但不预选
                self.push_screen(ToolsListModal())
        elif event.button.id == "new-session-button":
            self.action_clear_chat()
            
    def action_clear_chat(self) -> None:
        """清空对话历史"""
        # 保存当前会话
        self._save_current_session()
        
        # 清空对话
        chat_history = self.query_one("#chat-history", ChatHistoryWidget)
        chat_history.clear_history()
        self.conversation_history.clear()
        self.current_session = None
        self._chat_in_progress = False
        self._add_welcome_message()
        self.notify("对话历史已清空", severity="success")
        
    def action_show_tools(self) -> None:
        """显示工具列表"""
        try:
            self.push_screen(ToolsListModal(enabled_tools=self.enabled_tools))
        except Exception as e:
            self.notify(f"打开工具列表失败: {e}", severity="error")

    @on(ToolsListModal.ToolsSaved)
    def on_tools_list_modal_tools_saved(self, message: ToolsListModal.ToolsSaved) -> None:
        """处理工具选择保存事件"""
        try:
            selected = set(message.selected_tools or [])
            self.enabled_tools = selected
            # 简单提示当前启用工具
            names_preview = ", ".join(list(selected)[:6]) if selected else "(无)"
            self.notify(f"✅ 已更新启用工具：{names_preview}", timeout=4, severity="success")
        except Exception as e:
            self.notify(f"更新启用工具失败: {e}", severity="error")
        
    def action_show_session_history(self) -> None:
        """显示历史会话"""
        modal = SessionHistoryModal(self.session_manager)
        self.push_screen(modal)
        
    def action_show_model_config(self) -> None:
        """显示模型配置管理"""
        from .model_config_app import ModelConfigScreen
        self.push_screen(ModelConfigScreen())
    
    def action_show_context(self) -> None:
        """显示上下文窗口"""
        try:
            self.push_screen(ContextWindowModal())
        except Exception as e:
            self.notify(f"打开上下文窗口失败: {e}", severity="error")
    
    @on(ModelConfigModal.ConfigSaved)
    def on_model_config_saved(self, event: ModelConfigModal.ConfigSaved) -> None:
        """处理模型配置保存事件，转发给当前的 ModelConfigScreen"""
        # 添加调试信息
        self.notify("DEBUG: InteractiveChatApp.on_model_config_saved 被调用，准备转发给 ModelConfigScreen", severity="info")
        
        # 获取当前屏幕栈中的 ModelConfigScreen
        from .model_config_app import ModelConfigScreen
        for screen in reversed(self.screen_stack):
            if isinstance(screen, ModelConfigScreen):
                # 找到了 ModelConfigScreen，转发消息
                self.notify("DEBUG: 找到 ModelConfigScreen，转发 ConfigSaved 消息", severity="info")
                screen.on_config_saved(event)
                break
        else:
            self.notify("DEBUG: 未找到 ModelConfigScreen", severity="warning")
        
        # 刷新主界面的模型选择器
        try:
            model_selector = self.query_one(ModelSelectorWidget)
            model_selector.refresh_model_list()
            self.notify("DEBUG: 主界面模型选择器已刷新", severity="info")
        except Exception as e:
            self.notify(f"DEBUG: 刷新模型选择器失败: {e}", severity="warning")
        
    def action_focus_input(self) -> None:
        """聚焦到输入框"""
        input_widget = self.query_one("#message-input", CustomTextArea)
        input_widget.focus()
    
    def on_session_history_modal_session_selected(self, message) -> None:
        """处理历史会话选择事件"""
        self._load_session(message.session)
    
    def _load_session(self, session: ChatSession):
        """加载指定会话"""
        # 保存当前会话
        if self.current_session and self.conversation_history:
            self.current_session.messages = self.conversation_history.copy()
            self.session_manager.save_session(self.current_session)
        
        # 加载新会话
        self.current_session = session
        self.conversation_history = session.messages.copy()
        
        # 更新UI
        chat_history = self.query_one("#chat-history", ChatHistoryWidget)
        chat_history.clear_history()
        
        # 重新显示历史消息
        for message in self.conversation_history:
            if message["role"] == "user":
                chat_history.add_message("user", message["content"])
            elif message["role"] == "assistant":
                chat_history.add_message("assistant", message["content"])
        
        # 加载完成后提示一次
        self.notify(f"已加载会话: {session.get_display_title()}", severity="success")
    
    def _save_current_session(self):
        """保存当前会话"""
        if not self.conversation_history:
            return
        
        if not self.current_session:
            # 创建新会话
            self.current_session = ChatSession.create()
        
        # 更新会话消息
        self.current_session.messages = self.conversation_history.copy()
        self.current_session.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 保存会话
        self.session_manager.save_session(self.current_session)


def run_interactive_chat():
    """运行交互式对话应用"""
    try:
        app = InteractiveChatApp()
        app.run()
    except Exception as e:
        print(f"交互式聊天应用启动失败: {e}")
        import traceback
        with open("interactive_chat_error.log", "w") as f:
            traceback.print_exc(file=f)
