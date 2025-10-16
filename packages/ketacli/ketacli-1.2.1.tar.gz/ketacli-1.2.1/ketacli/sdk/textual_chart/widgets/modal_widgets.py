"""弹窗组件模块"""

import json

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static, Checkbox, Collapsible
import logging

from ..data_models import ChatSession, SessionManager


class ToolsListModal(ModalScreen):
    """工具列表弹窗（支持选择启用的工具）"""

    class ToolsSaved(Message):
        def __init__(self, selected_tools: list[str]):
            super().__init__()
            self.selected_tools = selected_tools

    def __init__(self, enabled_tools: set[str] | None = None, **kwargs):
        super().__init__(**kwargs)
        self._enabled_tools = set(enabled_tools or [])
        self._tool_names: list[str] = []
        # 记录每个复选框对应的行容器，便于动态切换选中样式
        self._row_by_checkbox_id: dict[str, Container] = {}

    def compose(self) -> ComposeResult:
        """构建工具列表UI"""
        with Container(id="tools-modal", classes="tools-modal"):
            with Vertical(classes="tools-content"):
                yield Label("可用工具（勾选以启用）", classes="modal-title")
                yield ScrollableContainer(classes="tools-list", id="tools-list")
                with Horizontal(classes="modal-buttons"):
                    yield Button("保存", id="save-button", variant="primary")
                    yield Button("关闭", id="close-button", variant="default")

    def on_mount(self) -> None:
        """弹窗挂载后添加工具列表内容"""
        tools_list = self.query_one("#tools-list", ScrollableContainer)
        
        # 获取可用工具
        from ketacli.sdk.ai.function_call import function_registry
        tools = function_registry.get_openai_tools_format() or []
        # 将已选中的工具排在前面（保持原始顺序，只调整分组）
        enabled_defs = []
        disabled_defs = []
        for tool in tools:
            func_info = tool.get('function', {})
            name = func_info.get('name', '')
            if not name:
                continue
            if name in self._enabled_tools:
                enabled_defs.append(tool)
            else:
                disabled_defs.append(tool)

        ordered_tools = enabled_defs + disabled_defs
        self._tool_names = []
        for tool in ordered_tools:
            func_info = tool.get('function', {})
            name = func_info.get('name', '')
            desc = func_info.get('description') or '(无描述)'
            params = func_info.get('parameters', {})
            if not name:
                continue
            self._tool_names.append(name)
            # 复选框行
            row = Container(classes="tool-item")
            # 先将行容器挂载到滚动容器，再挂载子组件，避免挂载顺序错误
            tools_list.mount(row)
            # 标题行：复选框 + 名称
            header = Horizontal(classes="tool-item-header")
            row.mount(header)
            checkbox = Checkbox(label="", value=(name in self._enabled_tools), compact=True)
            checkbox.id = f"tool-checkbox-{name}"
            # 建立映射，便于在复选框状态改变时更新行样式
            self._row_by_checkbox_id[checkbox.id] = row
            name_label = Static(name, classes="tool-item-title", markup=False)
            header.mount(checkbox)
            header.mount(name_label)
            # 描述固定展示
            desc_widget = Static(
                desc,
                classes="tool-item-desc",
                markup=False
            )
            row.mount(desc_widget)
            # 参数默认收起，放入折叠容器
            params_widget = Static(
                f"[dim]{json.dumps(params, indent=2, ensure_ascii=False)}[/dim]",
                classes="tool-item-params",
                markup=True
            )
            details = Collapsible(
                params_widget,
                title="参数",
                collapsed=True,
                classes="tool-item-details",
            )
            row.mount(details)

            # 初始状态：若已启用则给行容器加选中样式
            try:
                if checkbox.value:
                    row.add_class("tool-item-selected")
            except Exception:
                pass

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """切换复选框时更新工具项的选中样式（绿色边框）"""
        try:
            cb = getattr(event, "checkbox", None) or getattr(event, "sender", None)
            if isinstance(cb, Checkbox):
                row = self._row_by_checkbox_id.get(cb.id)
                if row:
                    if cb.value:
                        row.add_class("tool-item-selected")
                    else:
                        row.remove_class("tool-item-selected")
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        if event.button.id == "close-button":
            self.dismiss()
        elif event.button.id == "save-button":
            # 收集选中的工具
            selected: list[str] = []
            for name in self._tool_names:
                cb = self.query_one(f"#tool-checkbox-{name}", Checkbox)
                if cb.value:
                    selected.append(name)
            # 发出保存事件
            self.post_message(self.ToolsSaved(selected_tools=selected))
            self.dismiss()


class ContextWindowModal(ModalScreen):
    """上下文查看弹窗
    
    展示当前会话上下文、系统提示词，以及为AI请求准备的上下文。
    """

    def compose(self) -> ComposeResult:
        with Container(id="context-modal", classes="context-modal"):
            with Vertical(classes="context-content"):
                yield Label("上下文窗口", classes="modal-title")
                yield ScrollableContainer(classes="context-sections", id="context-content")
                with Horizontal(classes="modal-buttons"):
                    yield Button("关闭", id="close-button", variant="default")

    def on_mount(self) -> None:
        content = self.query_one("#context-content", ScrollableContainer)

        # 系统提示词
        try:
            system_prompt = getattr(self.app.ai_client, "system_prompt", "") or "(无系统提示词)"
        except Exception:
            system_prompt = "(无法获取系统提示词)"

        system_block = Static(
            f"系统提示词\n{system_prompt}",
            classes="context-block",
            markup=False
        )
        content.mount(system_block)

        # 已启用工具列表
        try:
            enabled = list(getattr(self.app, "enabled_tools", set()) or [])
            enabled.sort()
            tools_text = ["已启用工具"]
            if not enabled:
                tools_text.append("暂无启用的工具（将不进行函数调用）")
            else:
                tools_text.append(f"数量: {len(enabled)}")
                tools_text.extend([f"- {n}" for n in enabled])
            content.mount(Static("\n".join(tools_text), classes="context-block", markup=False))
        except Exception:
            pass

        # 原始会话消息（完整，不截断），并区分用户输入与模型返回
        try:
            raw_messages = list(self.app.conversation_history or [])
        except Exception:
            raw_messages = []

        # 时间线（完整）
        timeline_lines = ["会话时间线（完整）"]
        if not raw_messages:
            timeline_lines.append("暂无消息")
        else:
            timeline_lines.append(f"总消息数: {len(raw_messages)}")
            for i, msg in enumerate(raw_messages, start=1):
                role = msg.get("role", "unknown")
                label = {
                    "system": "系统提示",
                    "user": "用户输入",
                    "assistant": "模型返回",
                    "tool": "工具结果"
                }.get(role, role)
                content_full = (msg.get("content", "") or "").strip()
                timeline_lines.append(f"{i}. [{label}] {content_full}")
        content.mount(Static("\n".join(timeline_lines), classes="context-block", markup=False))

        # 用户输入（完整）
        user_lines = ["用户输入（完整）"]
        user_messages = [m for m in raw_messages if (m.get("role") == "user")]
        if not user_messages:
            user_lines.append("暂无用户输入")
        else:
            for i, msg in enumerate(user_messages, start=1):
                content_full = (msg.get("content", "") or "").strip()
                user_lines.append(f"{i}. {content_full}")
        content.mount(Static("\n".join(user_lines), classes="context-block", markup=False))

        # 模型返回（完整）
        assistant_lines = ["模型返回（完整）"]
        assistant_messages = [m for m in raw_messages if (m.get("role") == "assistant")]
        if not assistant_messages:
            assistant_lines.append("暂无模型返回")
        else:
            for i, msg in enumerate(assistant_messages, start=1):
                content_full = (msg.get("content", "") or "").strip()
                assistant_lines.append(f"{i}. {content_full}")
        content.mount(Static("\n".join(assistant_lines), classes="context-block", markup=False))

        # 压缩建议
        try:
            recommendation = self.app.context_manager.get_compression_recommendation(raw_messages)
        except Exception:
            recommendation = {"should_compress": False, "estimated_tokens": 0}

        rec_block = Static(
            "\n".join([
                "压缩建议",
                f"是否建议压缩: {'是' if recommendation.get('should_compress') else '否'}",
                f"估算当前token: {recommendation.get('estimated_tokens', 0)}",
            ]),
            classes="context-block",
            markup=False
        )
        content.mount(rec_block)

        # 为AI请求准备的上下文（压缩后）
        try:
            # 准备一个会话对象
            session: ChatSession = self.app.current_session or ChatSession.create_new()
            if not session.messages:
                session.update_messages(raw_messages)
            prepared_messages = self.app.session_context_manager.prepare_for_ai_request(session, max_context_tokens=4000) or []
        except Exception:
            prepared_messages = []

        # 记录上下文准备情况
        try:
            logger = logging.getLogger("ketacli.textual")
            logger.debug(f"[context-modal] 原始消息数={len(raw_messages)}, 预处理后消息数={len(prepared_messages)}")
        except Exception:
            pass

        prepared_lines = ["AI请求上下文（压缩后/裁剪后）"]
        if not prepared_messages:
            prepared_lines.append("暂无上下文（可能没有消息或准备失败）")
            try:
                logging.getLogger("ketacli.textual").warning("[context-modal] 预处理上下文为空：可能没有消息或准备失败")
            except Exception:
                pass
        else:
            prepared_lines.append(f"上下文消息数: {len(prepared_messages)}")
            for i, msg in enumerate(prepared_messages, start=1):
                role = msg.get("role", "unknown")
                content_preview = (msg.get("content", "") or "").strip()
                if len(content_preview) > 200:
                    content_preview = content_preview[:200] + "..."
                prepared_lines.append(f"{i}. [{role}] {content_preview}")

        prepared_block = Static("\n".join(prepared_lines), classes="context-block", markup=False)
        content.mount(prepared_block)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-button":
            self.dismiss()


class SessionHistoryModal(ModalScreen):
    """历史会话列表弹窗"""
    
    class SessionSelected(Message):
        """会话选择事件"""
        def __init__(self, session: ChatSession):
            super().__init__()
            self.session = session
    
    def __init__(self, session_manager: SessionManager, **kwargs):
        super().__init__(**kwargs)
        self.session_manager = session_manager
        self.sessions = []
    
    def compose(self) -> ComposeResult:
        """构建历史会话列表UI"""
        with Container(id="session-history-modal", classes="session-history-modal"):
            with Vertical(classes="session-history-content"):
                yield Label("历史会话", classes="modal-title")
                yield ScrollableContainer(classes="session-list", id="session-list")
                with Horizontal(classes="modal-buttons"):
                    yield Button("关闭", id="close-button", variant="default")
    
    def on_mount(self) -> None:
        """弹窗挂载后加载历史会话"""
        self._load_sessions()
        # 设置初始焦点到第一个会话项
        self.call_after_refresh(self._focus_first_session)
    
    def _focus_first_session(self):
        """将焦点设置到第一个会话项"""
        session_list = self.query_one("#session-list", ScrollableContainer)
        session_widgets = session_list.query(SessionItemWidget)
        if session_widgets:
            first_widget = session_widgets.first()
            first_widget.focus()
    
    def on_focus(self, event) -> None:
        """监听焦点变化"""
        pass
    
    def on_key(self, event) -> None:
        """处理键盘事件"""
        if event.key == "up":
            self._navigate_sessions(-1)
            event.prevent_default()
        elif event.key == "down":
            self._navigate_sessions(1)
            event.prevent_default()
        elif event.key == "enter":
            self._select_focused_session()
            event.prevent_default()
        elif event.key == "delete" or event.key == "d":
            self._delete_focused_session()
            event.prevent_default()
        elif event.key == "escape":
            self.dismiss()
            event.prevent_default()
    
    def _navigate_sessions(self, direction: int):
        """在会话之间导航"""
        session_list = self.query_one("#session-list", ScrollableContainer)
        session_widgets = list(session_list.query(SessionItemWidget))
        
        if not session_widgets:
            return
        
        # 找到当前焦点的会话
        focused_widget = self.focused
        if not isinstance(focused_widget, SessionItemWidget):
            # 如果没有焦点在会话项上，设置到第一个
            session_widgets[0].focus()
            return
        
        # 找到当前焦点会话的索引
        try:
            current_index = session_widgets.index(focused_widget)
        except ValueError:
            session_widgets[0].focus()
            return
        
        # 计算新的索引
        new_index = current_index + direction
        if 0 <= new_index < len(session_widgets):
            session_widgets[new_index].focus()
    
    def _select_focused_session(self):
        """选择当前焦点的会话"""
        focused_widget = self.focused
        if isinstance(focused_widget, SessionItemWidget):
            # 触发会话选择
            self.post_message(self.SessionSelected(focused_widget.session))
            self.dismiss()
    
    def _load_sessions(self):
        """加载历史会话列表"""
        session_list = self.query_one("#session-list", ScrollableContainer)
        
        # 清空现有内容
        for child in list(session_list.children):
            child.remove()
        
        # 获取历史会话
        self.sessions = self.session_manager.list_sessions()
        
        if not self.sessions:
            empty_widget = Static(
                "[dim]暂无历史会话[/dim]",
                classes="empty-message"
            )
            session_list.mount(empty_widget)
            return
        
        # 显示会话列表
        for session in self.sessions:
            session_widget = SessionItemWidget(session)
            session_list.mount(session_widget)
    
    def on_session_item_widget_session_clicked(self, message) -> None:
        """处理会话项点击事件"""
        self.post_message(self.SessionSelected(message.session))
        self.dismiss()
    

    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        if event.button.id == "close-button":
            self.dismiss()
    

    
    def _delete_focused_session(self):
        """删除当前焦点的会话"""
        session_list = self.query_one("#session-list", ScrollableContainer)
        target_widget = None
        
        # 检查当前焦点
        focused_widget = self.focused
        if isinstance(focused_widget, SessionItemWidget):
            target_widget = focused_widget
        else:
            # 查找有焦点样式的会话项
            for widget in session_list.query(SessionItemWidget):
                if widget.has_class("focused"):
                    target_widget = widget
                    break
        
        if not target_widget:
            self.notify("请先选择要删除的会话", severity="warning")
            return
        
        session = target_widget.session
        if self.session_manager.delete_session(session.session_id):
            self.notify(f"已删除会话: {session.title}")
            self._load_sessions()  # 重新加载列表
            # 重新设置焦点到第一个会话
            self.call_after_refresh(self._focus_first_session)
        else:
            self.notify("删除失败", severity="error")


class SessionItemWidget(Static):
    """会话项组件"""
    
    # 允许接收焦点
    can_focus = True
    
    class SessionClicked(Message):
        """会话点击事件"""
        def __init__(self, session: ChatSession):
            super().__init__()
            self.session = session
    
    def __init__(self, session: ChatSession, **kwargs):
        super().__init__(**kwargs)
        self.session = session
        self.last_click_time = 0
    
    def compose(self) -> ComposeResult:
        """构建会话项UI"""
        title = self.session.get_display_title()
        created_time = self.session.created_at
        message_count = len(self.session.messages)
        
        content = f"[bold]{title}[/bold]\n"
        content += f"[dim]创建时间: {created_time}[/dim]\n"
        content += f"[dim]消息数: {message_count}[/dim]"
        
        yield Static(content, classes="session-item-content", id="content")
    
    def on_click(self, event) -> None:
        """处理点击事件 - 支持双击检测"""
        import time
        current_time = time.time()
        
        # 双击检测：如果两次点击间隔小于0.5秒，认为是双击
        if current_time - self.last_click_time < 0.5:
            # 双击 - 加载会话
            self.post_message(self.SessionClicked(self.session))
        
        self.last_click_time = current_time
    
    def on_key(self, event) -> None:
        """处理键盘事件"""
        if event.key == "enter":
            # Enter键加载会话
            self.post_message(self.SessionClicked(self.session))
            event.prevent_default()
    

    
    def on_focus(self) -> None:
        """获得焦点时的处理"""
        self.add_class("focused")
    
    def on_blur(self) -> None:
        """失去焦点时的处理"""
        self.remove_class("focused")