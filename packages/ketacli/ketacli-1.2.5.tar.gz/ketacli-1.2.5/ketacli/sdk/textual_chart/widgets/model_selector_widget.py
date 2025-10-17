"""模型选择器组件模块"""

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Label, Select


class ModelSelectorWidget(Container):
    """模型选择组件"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def compose(self) -> ComposeResult:
        """构建模型选择UI"""
        with Horizontal(classes="model-selector-row"):
            yield Label("AI模型:", classes="model-label")
            yield Select(
                options=[("默认模型", None)],  # 将在初始化时更新
                id="model-select",
                classes="model-select"
            )
            yield Button("新会话", id="new-session-button", variant="success")
            yield Button("工具列表", id="tools-button", variant="default")
            
    def on_mount(self) -> None:
        """组件挂载时初始化模型列表"""
        self._update_model_options()
        
    def _update_model_options(self):
        """更新模型选项"""
        try:
            from ketacli.sdk.ai import AIConfig
            config = AIConfig(allow_empty=True)
            models = config.list_models()
            
            # 尝试获取默认模型
            default_model = None
            try:
                default_model = config.get_default_model()
            except:
                # 如果没有设置默认模型，继续处理
                pass
            
            options = []
            selected_value = None
            
            # 如果没有默认模型或模型列表为空，添加"默认模型"选项
            if not default_model or not models:
                options.append(("默认模型", None))
                selected_value = None
            else:
                # 有默认模型时，不添加"默认模型"选项，直接设置默认选择
                selected_value = default_model
            
            # 添加所有模型选项
            for model in models:
                label = f"{model} (默认)" if model == default_model else model
                options.append((label, model))
                
            select_widget = self.query_one("#model-select", Select)
            select_widget.set_options(options)
            
            # 如果有默认模型，自动选择它
            if selected_value is not None:
                select_widget.value = selected_value
                
        except Exception:
            # 如果获取模型列表失败，使用默认选项
            select_widget = self.query_one("#model-select", Select)
            select_widget.set_options([("默认模型", None)])
            
    def get_selected_model(self) -> Optional[str]:
        """获取选中的模型"""
        select_widget = self.query_one("#model-select", Select)
        return select_widget.value
    
    def refresh_model_list(self):
        """刷新模型列表"""
        self._update_model_options()