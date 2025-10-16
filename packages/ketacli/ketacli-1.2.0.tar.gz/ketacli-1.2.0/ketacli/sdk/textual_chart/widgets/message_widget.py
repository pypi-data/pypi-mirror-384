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

from ..token_calculator import TokenStats, calculate_token_stats
from typing import Optional, Dict


def safe_markdown_widget(content: str, **kwargs):
    """安全地创建Markdown组件，如果解析失败则回退到Static组件"""
    try:
        return Markdown(content, **kwargs)
    except Exception:
        # 如果Markdown解析失败，回退到Static组件
        return Static(content, **kwargs)


class MessageWidget(Static):
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
            
            if self.role == "assistant":
                # AI消息使用安全的Markdown渲染
                if is_long and not self.is_expanded:
                    truncated_content = self.content[:500] + "..."
                    yield safe_markdown_widget(truncated_content, classes="message-content", id=f"message-content-{self.unique_id}")
                    yield Button("点击查看完整消息", id=f"expand-message-button-{self.unique_id}", classes="expand-button")
                else:
                    yield safe_markdown_widget(self.content, classes="message-content", id=f"message-content-{self.unique_id}")
                    if is_long and self.is_expanded:
                        yield Button("收起", id=f"collapse-message-button-{self.unique_id}", classes="expand-button")
            else:
                # 用户消息使用普通文本
                if is_long and not self.is_expanded:
                    truncated_content = self.content[:500] + "..."
                    yield Static(truncated_content, classes="message-content", id=f"message-content-{self.unique_id}", markup=False)
                    yield Button("点击查看完整消息", id=f"expand-message-button-{self.unique_id}", classes="expand-button")
                else:
                    yield Static(self.content, classes="message-content", id=f"message-content-{self.unique_id}", markup=False)
                    if is_long and self.is_expanded:
                        yield Button("收起", id=f"collapse-message-button-{self.unique_id}", classes="expand-button")
            
            # 添加复制按钮
            yield Button("📋 复制", id=f"copy-message-button-{self.unique_id}", classes="copy-button")
            
            # 添加token统计显示
            yield self._create_token_stats_widget()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击事件"""
        if event.button.id == f"expand-message-button-{self.unique_id}":
            self.is_expanded = True
            self._update_message_content()
        elif event.button.id == f"collapse-message-button-{self.unique_id}":
            self.is_expanded = False
            self._update_message_content()
        elif event.button.id == f"copy-message-button-{self.unique_id}":
            self._copy_message_content()
    
    def _update_message_content(self):
        """更新消息内容显示"""
        # 更安全的方式：先查找现有组件，如果存在则更新内容，否则创建新组件
        is_long = len(self.content) > 500
        
        # 处理内容组件
        try:
            if self.role == "assistant":
                content_widget = self.query_one(f"#message-content-{self.unique_id}", Markdown)
            else:
                content_widget = self.query_one(f"#message-content-{self.unique_id}", Static)
            # 更新现有组件的内容
            if self.role == "assistant":
                if is_long and not self.is_expanded:
                    truncated_content = self.content[:500] + "..."
                    content_widget.update(truncated_content)
                else:
                    content_widget.update(self.content)
            else:
                if is_long and not self.is_expanded:
                    truncated_content = self.content[:500] + "..."
                    content_widget.update(truncated_content)
                else:
                    content_widget.update(self.content)
        except:
            # 如果组件不存在，创建新的
            if self.role == "assistant":
                if is_long and not self.is_expanded:
                    truncated_content = self.content[:500] + "..."
                    self.mount(safe_markdown_widget(truncated_content, classes="message-content", id=f"message-content-{self.unique_id}"))
                else:
                    self.mount(safe_markdown_widget(self.content, classes="message-content", id=f"message-content-{self.unique_id}"))
            else:
                if is_long and not self.is_expanded:
                    truncated_content = self.content[:500] + "..."
                    self.mount(Static(truncated_content, classes="message-content", id=f"message-content-{self.unique_id}"))
                else:
                    self.mount(Static(self.content, classes="message-content", id=f"message-content-{self.unique_id}"))
        
        # 处理按钮组件
        # 移除所有相关按钮（包括复制按钮）
        for button_id in [f"expand-message-button-{self.unique_id}", f"collapse-message-button-{self.unique_id}", f"copy-message-button-{self.unique_id}"]:
            try:
                button_widget = self.query_one(f"#{button_id}")
                button_widget.remove()
            except:
                pass
        
        # 根据状态添加相应的按钮
        if is_long:
            if not self.is_expanded:
                self.mount(Button("点击查看完整消息", id=f"expand-message-button-{self.unique_id}", classes="expand-button"))
            else:
                self.mount(Button("收起", id=f"collapse-message-button-{self.unique_id}", classes="expand-button"))
        
        # 重新添加复制按钮
        self.mount(Button("📋 复制", id=f"copy-message-button-{self.unique_id}", classes="copy-button"))
    
    def _copy_message_content(self):
        """复制消息内容到剪贴板"""
        try:
            pyperclip.copy(self.content)
            # 通过app发送通知
            if hasattr(self.app, 'notify'):
                self.app.notify(f"已复制消息内容")
        except Exception as e:
            if hasattr(self.app, 'notify'):
                self.app.notify(f"复制失败: {str(e)}")
    
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
        except:
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
            # 通过app发送通知
            if hasattr(self.app, 'notify'):
                self.app.notify(f"已复制消息内容")
        except Exception as e:
            if hasattr(self.app, 'notify'):
                self.app.notify(f"复制失败: {str(e)}")
        
    def get_final_content(self) -> str:
        """获取最终内容"""
        return "".join(self.content_chunks)


class ToolCallWidget(Static):
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
        
    def compose(self) -> ComposeResult:
        """构建工具调用UI"""
        status_color = "green" if self.success else "red"
        status_text = "✓" if self.success else "✗"
        
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
            # 文本结果的显示（支持展开/收起）
            lines = self.result.split('\n')
            is_long = len(lines) > 4
            if is_long and not self.is_expanded:
                # 只显示前4行，并添加省略号
                display_result = '\n'.join(lines[:4]) + "\n..."
                yield Static(f"结果: {display_result}", classes="tool-result", id=f"tool-result-content-{self.unique_id}", markup=False)
                yield Button("点击查看完整结果", id=f"expand-button-{self.unique_id}", classes="expand-button")
            else:
                yield Static(f"结果: {self.result}", classes="tool-result", id=f"tool-result-content-{self.unique_id}", markup=False)
                if is_long and self.is_expanded:
                    yield Button("收起", id=f"collapse-button-{self.unique_id}", classes="expand-button")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击事件"""
        if event.button.id == f"expand-button-{self.unique_id}":
            self.is_expanded = True
            self._update_content()
        elif event.button.id == f"collapse-button-{self.unique_id}":
            self.is_expanded = False
            self._update_content()
    
    def _update_content(self):
        """更新内容显示"""
        # 移除现有的结果和按钮组件
        result_widgets = self.query(f"#tool-result-content-{self.unique_id}")
        for widget in result_widgets:
            widget.remove()
        
        expand_buttons = self.query(f"#expand-button-{self.unique_id}")
        for widget in expand_buttons:
            widget.remove()
            
        collapse_buttons = self.query(f"#collapse-button-{self.unique_id}")
        for widget in collapse_buttons:
            widget.remove()
        
        # 使用call_after_refresh确保移除操作完成后再挂载新组件
        self.call_after_refresh(self._mount_new_content)
    
    def _mount_new_content(self):
        """在移除操作完成后挂载新内容"""
        if self.result:
            # 检查是否需要截断（按行数判断，超过4行）
            lines = self.result.split('\n')
            is_long = len(lines) > 4
            if is_long and not self.is_expanded:
                # 只显示前4行，并添加省略号
                display_result = '\n'.join(lines[:4]) + "\n..."
                self.mount(Static(f"结果: {display_result}", classes="tool-result", id=f"tool-result-content-{self.unique_id}", markup=False))
                self.mount(Button("点击查看完整结果", id=f"expand-button-{self.unique_id}", classes="expand-button"))
            else:
                self.mount(Static(f"结果: {self.result}", classes="tool-result", id=f"tool-result-content-{self.unique_id}", markup=False))
                if is_long and self.is_expanded:
                    self.mount(Button("收起", id=f"collapse-button-{self.unique_id}", classes="expand-button"))