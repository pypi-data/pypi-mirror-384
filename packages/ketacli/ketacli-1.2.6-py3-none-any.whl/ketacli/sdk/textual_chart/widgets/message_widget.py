"""消息显示组件

包含各种消息显示相关的UI组件。
"""

import pyperclip
import uuid
from typing import Dict, List, Optional
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, Button, Markdown
from textual.reactive import reactive
from textual.widget import Widget
from .message_actions_widget import MessageActions

from ..token_calculator import TokenStats, calculate_token_stats
from typing import Optional, Dict


def safe_markdown_widget(content: str, **kwargs):
    """安全地创建Markdown组件，如果解析失败则回退到Static组件"""
    try:
        return Markdown(content, **kwargs)
    except Exception:
        # 如果Markdown解析失败，回退到Static组件
        return Static(content, **kwargs)


class ExpandableContentMixin:
    """抽象可展开的文本内容逻辑：统一展开/收起、内容更新与复制"""

    def _render_actions(self, is_long: bool, on_copy):
        return MessageActions(
            on_toggle=self._on_actions_toggle,
            on_copy=on_copy,
            is_long=is_long,
            is_expanded=self.is_expanded,
            unique_id=self.unique_id,
            id=f"message-actions-{self.unique_id}",
        )

    def _update_text_content(
        self,
        text: str,
        is_markdown: bool,
        content_id: str,
        max_length: int,
        prefix: str = "",
    ):
        """统一更新文本内容组件（支持Markdown/Static），并在必要时挂载新组件"""
        try:
            content_widget = self.query_one(
                f"#{content_id}", Markdown if is_markdown else Static
            )
        except Exception:
            content_widget = None

        display_text = prefix + (
            text[:max_length] + "..." if len(text) > max_length and not self.is_expanded else text
        )

        if content_widget:
            content_widget.update(display_text)
        else:
            try:
                anchor = self.query_one(f"#message-actions-{self.unique_id}")
            except Exception:
                anchor = None
            if is_markdown:
                new_widget = safe_markdown_widget(
                    display_text, classes="message-content", id=content_id
                )
            else:
                new_widget = Static(
                    display_text, classes="message-content", id=content_id, markup=False
                )
            if anchor:
                self.mount(new_widget, before=anchor)
            else:
                self.mount(new_widget)

    def _copy_text_to_clipboard(self, text: str):
        try:
            pyperclip.copy(text or "")
            # 复制成功提示
            if hasattr(self, "notify"):
                self.notify("内容已复制到剪贴板", severity="success")
            elif hasattr(self.app, "notify"):
                self.app.notify("内容已复制到剪贴板", severity="success")
        except Exception as e:
            if hasattr(self, "notify"):
                self.notify(f"复制失败: {str(e)}", severity="error")
            elif hasattr(self.app, "notify"):
                self.app.notify(f"复制失败: {str(e)}", severity="error")


class MessageWidget(ExpandableContentMixin, Static):
    """单条消息显示组件"""
    
    def __init__(self, role: str, content: str, timestamp: str = None, 
                 token_stats: Optional[TokenStats] = None, 
                 context_messages: Optional[List[Dict]] = None, **kwargs):
        super().__init__(markup=False, **kwargs)
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now().strftime("%H:%M:%S")
        self.is_expanded = False
        # 为每个实例生成唯一ID前缀，避免多个实例间的ID冲突
        self.unique_id = str(uuid.uuid4())[:8]
        
        # Token统计相关
        self.context_messages = context_messages or []
        
        # 如果没有提供token统计，则自动计算
        if token_stats is None:
            message_dict = {"role": role, "content": content}
            self.token_stats = calculate_token_stats(
                current_message=message_dict,
                context_messages=self.context_messages
            )
        else:
            self.token_stats = token_stats
        
        
    def compose(self) -> ComposeResult:
        """构建消息UI"""
        role_color = "blue" if self.role == "user" else "green"
        role_text = "用户" if self.role == "user" else "AI助手"
        
        with Container(classes=f"message-container {self.role}-message"):
            yield Static(f"[{role_color}]{role_text}[/{role_color}] [{self.timestamp}]", classes="message-header")
            
            # 检查内容长度
            is_long = len(self.content) > 500

            # 内容展示（统一逻辑：根据 is_expanded 状态截断/展示）
            if self.role == "assistant":
                if is_long and not self.is_expanded:
                    truncated_content = self.content[:500] + "..."
                    yield safe_markdown_widget(truncated_content, classes="message-content", id=f"message-content-{self.unique_id}")
                else:
                    yield safe_markdown_widget(self.content, classes="message-content", id=f"message-content-{self.unique_id}")
            else:
                if is_long and not self.is_expanded:
                    truncated_content = self.content[:500] + "..."
                    yield Static(truncated_content, classes="message-content", id=f"message-content-{self.unique_id}", markup=False)
                else:
                    yield Static(self.content, classes="message-content", id=f"message-content-{self.unique_id}", markup=False)

            # 操作组件：复制 + 展开/收起（统一）
            yield self._render_actions(is_long, on_copy=self._copy_message_content)

            # 添加token统计显示
            yield self._create_token_stats_widget()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """消息按钮事件已统一由 MessageActions 处理"""
        pass

    def _on_actions_toggle(self, expanded: bool):
        """供 MessageActions 回调：切换展开状态"""
        self.is_expanded = expanded
        self._update_message_content()
    
    def _update_message_content(self):
        """更新消息内容显示（仅更新内容，操作按钮由 MessageActions 管理）"""
        is_markdown = self.role == "assistant"
        self._update_text_content(
            text=self.content,
            is_markdown=is_markdown,
            content_id=f"message-content-{self.unique_id}",
            max_length=500,
            prefix="",
        )

    def _copy_message_content(self):
        """复制消息内容到剪贴板"""
        self._copy_text_to_clipboard(self.content)

    def _create_token_stats_widget(self) -> Static:
        """创建token统计显示组件"""
        stats_text = f"[dim]🔢 {str(self.token_stats)}[/dim]"
        return Static(stats_text, classes="token-stats", id=f"token-stats-{self.unique_id}")

    def update_token_stats(self, new_stats: TokenStats):
        """更新token统计信息"""
        self.token_stats = new_stats
        try:
            stats_widget = self.query_one(f"#token-stats-{self.unique_id}", Static)
            stats_text = f"[dim]🔢 {str(new_stats)}[/dim]"
            stats_widget.update(stats_text)
        except Exception:
            # 如果组件不存在，重新创建
            self.mount(self._create_token_stats_widget())


class StreamingMessageWidget(Static):
    """流式消息显示组件"""
    
    def __init__(self, role: str, timestamp: str, 
                 context_messages: Optional[List[Dict]] = None, **kwargs):
        super().__init__(markup=False, **kwargs)
        self.role = role
        self.timestamp = timestamp
        self.content_chunks = []
        # 为每个实例生成唯一ID前缀，避免多个实例间的ID冲突
        self.unique_id = str(uuid.uuid4())[:8]
        
        # Token统计相关
        self.context_messages = context_messages or []
        self.token_stats = None
        
    def compose(self) -> ComposeResult:
        """构建流式消息UI"""
        role_color = "blue" if self.role == "user" else "green"
        role_text = "用户" if self.role == "user" else "AI助手"
        
        with Container(classes=f"message-container {self.role}-message"):
            yield Static(f"[{role_color}]{role_text}[/{role_color}] [{self.timestamp}] [dim]正在输入...[/dim]", classes="message-header")
            # 使用Markdown进行流式渲染，保持Markdown格式
            yield safe_markdown_widget("", id=f"streaming-content-{self.unique_id}", classes="message-content")
            
    def append_content(self, chunk: str):
        """追加内容块"""
        self.content_chunks.append(chunk)
        current_content = "".join(self.content_chunks)
        
        # 更新内容（优先使用Markdown组件）
        try:
            content_widget = self.query_one(f"#streaming-content-{self.unique_id}", Markdown)
        except Exception:
            content_widget = self.query_one(f"#streaming-content-{self.unique_id}", Static)
        content_widget.update(current_content)
        
        # 滚动到底部
        if self.parent:
            self.parent.scroll_end()
            
    def finalize_content(self):
        """完成内容输入，移除"正在输入"提示"""
        header_widget = self.query_one(".message-header", Static)
        role_color = "blue" if self.role == "user" else "green"
        role_text = "用户" if self.role == "user" else "AI助手"
        header_widget.update(f"[{role_color}]{role_text}[/{role_color}] [{self.timestamp}]")
        
    def finalize(self):
        """完成流式消息，添加复制按钮和token统计"""
        # 计算最终的token统计
        final_content = "".join(self.content_chunks)
        message_dict = {"role": self.role, "content": final_content}
        self.token_stats = calculate_token_stats(
            current_message=message_dict,
            context_messages=self.context_messages
        )
        
        # 添加复制按钮
        copy_button = Button("📋 复制", id=f"copy-streaming-button-{self.unique_id}", classes="copy-button")
        self.mount(copy_button)
        
        # 添加token统计显示
        stats_text = f"[dim]🔢 {str(self.token_stats)}[/dim]"
        token_stats_widget = Static(stats_text, classes="token-stats", id=f"token-stats-{self.unique_id}")
        self.mount(token_stats_widget)
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击事件"""
        if event.button.id == f"copy-streaming-button-{self.unique_id}":
            self._copy_message_content()
    
    def _copy_message_content(self):
        """复制消息内容到剪贴板"""
        try:
            content = "".join(self.content_chunks)
            pyperclip.copy(content)
            if hasattr(self, "notify"):
                self.notify("内容已复制到剪贴板", severity="success")
            elif hasattr(self.app, "notify"):
                self.app.notify("内容已复制到剪贴板", severity="success")
        except Exception as e:
            if hasattr(self, "notify"):
                self.notify(f"复制失败: {str(e)}", severity="error")
            elif hasattr(self.app, 'notify'):
                self.app.notify(f"复制失败: {str(e)}", severity="error")
        
    def get_final_content(self) -> str:
        """获取最终内容"""
        return "".join(self.content_chunks)


class ToolCallWidget(ExpandableContentMixin, Static):
    """工具调用显示组件"""
    
    def __init__(self, tool_name: str, arguments: str, result: str = None, success: bool = True, result_obj: Optional[Dict] = None, **kwargs):
        super().__init__(markup=False, **kwargs)
        self.tool_name = tool_name
        self.arguments = arguments
        self.result = result
        self.success = success
        self.result_obj = result_obj or None
        self.is_expanded = False
        # 为每个实例生成唯一ID前缀，避免多个实例间的ID冲突
        self.unique_id = str(uuid.uuid4())[:8]
        self.max_length = 500
        
    def compose(self) -> ComposeResult:
        """构建工具调用UI"""
        status_color = "green" if self.success else "red"
        status_text = "✓" if self.success else "✗"
        
        # 将结果与操作按钮一并置于工具容器（黄色框）内
        with Container(classes="tool-call-container"):
            yield Static(f"[cyan]🔧 调用工具: {self.tool_name}[/cyan] [{status_color}]{status_text}[/{status_color}]", classes="tool-header")
            yield Static(f"[dim]参数: {self.arguments}[/dim]", classes="tool-args")
            
            # 优先渲染对象结果（如图表组件或任意Textual组件）
            if self.result_obj and isinstance(self.result_obj, Widget):
                self.notify("图表可视化结果已显示")
                # 使用包装容器居中显示结果组件
                with Container(classes="tool-result-wrapper"):
                    yield self.result_obj
            elif isinstance(self.result, Widget):
                # 兼容旧逻辑：如果结果直接是组件实例
                self.notify("图表可视化结果已显示")
                with Container(classes="tool-result-wrapper"):
                    yield self.result
            elif self.result:
                # 文本结果显示（统一逻辑：按字符长度截断）
                is_long = len(self.result) > 500
                if is_long and not self.is_expanded:
                    truncated = self.result[:500] + "..."
                    yield Static(
                        f"结果: {truncated}",
                        classes="tool-result",
                        id=f"tool-result-content-{self.unique_id}",
                        markup=False,
                    )
                else:
                    yield Static(
                        f"结果: {self.result}",
                        classes="tool-result",
                        id=f"tool-result-content-{self.unique_id}",
                        markup=False,
                    )

                # 操作组件：复制 + 展开/收起（统一）放在容器内部
                yield self._render_actions(is_long, on_copy=self._copy_result_content)

    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """工具结果按钮事件由 MessageActions 处理"""
        pass

    def _on_actions_toggle(self, expanded: bool):
        """供 MessageActions 回调：切换展开状态"""
        self.is_expanded = expanded
        self._update_content()

    def _copy_result_content(self):
        """复制工具结果到剪贴板"""
        self._copy_text_to_clipboard(self.result or "")
    
    def _update_content(self):
        """更新内容显示"""
        if not self.result:
            return
        self._update_text_content(
            text=self.result,
            is_markdown=False,
            content_id=f"tool-result-content-{self.unique_id}",
            max_length=self.max_length,
            prefix="结果: ",
        )

        # 优先就地更新现有结果组件，避免影响操作条
        try:
            content_widget = self.query_one(
                f"#tool-result-content-{self.unique_id}", Static
            )
        except Exception:
            content_widget = None

        

        if self.result:
            is_long = len(self.result) > self.max_length
            if content_widget:
                if is_long and not self.is_expanded:
                    truncated = self.result[:self.max_length] + "..."
                    content_widget.update(f"结果: {truncated}")
                else:
                    content_widget.update(f"结果: {self.result}")
            else:
                # 若不存在结果组件，则创建；为保证位置稳定，尽量插入到操作条之前
                try:
                    anchor = self.query_one(f"#message-actions-{self.unique_id}")
                except Exception:
                    anchor = None
                if is_long and not self.is_expanded:
                    truncated = self.result[:self.max_length] + "..."
                    new_widget = Static(
                        f"结果: {truncated}",
                        classes="tool-result",
                        id=f"tool-result-content-{self.unique_id}",
                        markup=False,
                    )
                else:
                    new_widget = Static(
                        f"结果: {self.result}",
                        classes="tool-result",
                        id=f"tool-result-content-{self.unique_id}",
                        markup=False,
                    )
                if anchor:
                    self.mount(new_widget, before=anchor)
                else:
                    self.mount(new_widget)

        