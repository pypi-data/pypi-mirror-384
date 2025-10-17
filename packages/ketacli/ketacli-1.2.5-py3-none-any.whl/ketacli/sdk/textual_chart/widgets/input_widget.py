"""聊天输入组件模块"""

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.widgets import Button, TextArea


class CustomTextArea(TextArea):
    """自定义TextArea组件，处理Enter键发送消息"""
    
    def on_key(self, event) -> None:
        """处理键盘事件"""
        # Shift+Enter 插入换行
        if event.key == "shift+enter":
            # 让TextArea处理换行，不阻止默认行为
            return
        # 单独的Enter键发送消息
        elif event.key == "enter":
            message_text = self.text.strip()
            if message_text:  # 只有非空消息才发送
                # 发送自定义消息给父组件
                self.post_message(ChatInputWidget.MessageSent(message_text))
                # 清空输入框
                self.text = ""
            event.prevent_default()  # 阻止默认的换行行为
            event.stop()  # 停止事件传播


class ChatInputWidget(Container):
    """聊天输入组件"""
    
    class MessageSent(Message):
        """消息发送事件"""
        def __init__(self, message: str):
            super().__init__()
            self.message = message
    
    class StopRequested(Message):
        """停止请求事件"""
        pass
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._is_loading = False
        self._is_processing = False  # AI正在处理中
        
    def compose(self) -> ComposeResult:
        """构建输入UI"""
        with Horizontal(classes="input-row"):
            yield CustomTextArea(id="message-input", classes="message-input")
            with Horizontal(classes="input-buttons"):
                yield Button("发送", id="send-button", variant="primary")
                yield Button("清空", id="clear-button", variant="default")
                
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        if event.button.id == "send-button":
            if self._is_processing:
                # 如果正在处理，发送停止请求
                self.post_message(self.StopRequested())
            else:
                # 否则发送消息
                self._send_message()
        elif event.button.id == "clear-button":
            self._clear_input()
            

    def on_text_area_submitted(self, event) -> None:
        """处理回车发送"""
        if event.text_area.id == "message-input":
            self._send_message()
            
    def _send_message(self):
        """发送消息"""
        if self._is_loading or self._is_processing:
            return
            
        input_widget = self.query_one("#message-input", CustomTextArea)
        message = input_widget.text.strip()
        if message:
            self.set_loading(True)
            self.post_message(self.MessageSent(message))
            input_widget.text = ""
            
    def _clear_input(self):
        """清空输入"""
        input_widget = self.query_one("#message-input", CustomTextArea)
        input_widget.text = ""
        
    def set_loading(self, loading: bool = True):
        """设置加载状态"""
        self._is_loading = loading
        send_button = self.query_one("#send-button", Button)
        input_widget = self.query_one("#message-input", CustomTextArea)
        
        if loading:
            send_button.label = "发送中..."
            send_button.disabled = True
            input_widget.disabled = True
        else:
            send_button.label = "发送"
            send_button.disabled = False
            input_widget.disabled = False
    
    def set_processing(self, processing: bool = True):
        """设置AI处理状态"""
        self._is_processing = processing
        send_button = self.query_one("#send-button", Button)
        input_widget = self.query_one("#message-input", CustomTextArea)
        
        if processing:
            send_button.label = "停止"
            send_button.variant = "error"
            send_button.disabled = False
            input_widget.disabled = True
        else:
            send_button.label = "发送"
            send_button.variant = "primary"
            send_button.disabled = False
            input_widget.disabled = False