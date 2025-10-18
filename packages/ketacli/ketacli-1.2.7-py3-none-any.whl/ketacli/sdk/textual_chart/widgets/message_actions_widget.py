"""
消息操作组件：复制 + 展开/收起

统一为模型消息与工具消息提供复制与展开/收起操作。
"""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button
from textual.reactive import reactive


class MessageActions(Horizontal):
    """消息操作条组件

    - 复制消息内容
    - 展开/收起切换（单个按钮，依据状态变更文案）
    """

    is_expanded = reactive(False)

    def __init__(
        self,
        on_toggle,
        on_copy,
        is_long: bool,
        is_expanded: bool = False,
        unique_id: str = "",
        show_copy: bool = True,
        **kwargs,
    ):
        # 继承 Horizontal，设置容器样式类
        super().__init__(classes="message-actions", **kwargs)
        self.on_toggle = on_toggle
        self.on_copy = on_copy
        self.is_long = is_long
        self.is_expanded = is_expanded
        self.unique_id = unique_id
        self.show_copy = show_copy

    def compose(self) -> ComposeResult:
        """通过 compose 产出子按钮，避免在未挂载时执行 mount 导致错误"""
        if self.show_copy:
            yield Button(
                "📋 复制",
                id=f"copy-actions-{self.unique_id}",
                classes="copy-button",
            )
        if self.is_long:
            label = "收起" if self.is_expanded else "展开"
            yield Button(
                label,
                id=f"toggle-actions-{self.unique_id}",
                classes="expand-button",
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理操作条按钮点击"""
        # 复制
        if event.button.id == f"copy-actions-{self.unique_id}":
            if callable(self.on_copy):
                self.on_copy()
            return

        # 展开/收起切换
        if event.button.id == f"toggle-actions-{self.unique_id}":
            new_state = not self.is_expanded
            self.is_expanded = new_state
            if callable(self.on_toggle):
                self.on_toggle(new_state)

            # 直接更新按钮文案，避免重复ID导致的挂载错误
            try:
                toggle_btn = event.button
                toggle_btn.label = "收起" if new_state else "展开"
                toggle_btn.refresh()
            except Exception:
                # 兜底：如果无法直接更新，则查询并更新
                try:
                    btn = self.query_one(
                        f"#toggle-actions-{self.unique_id}", Button
                    )
                    btn.label = "收起" if new_state else "展开"
                    btn.refresh()
                except Exception:
                    pass