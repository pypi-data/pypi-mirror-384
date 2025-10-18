"""
模型配置管理应用

独立的模型配置管理界面应用。
"""

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import Container
from textual.widgets import Header, Footer
from textual import on

from .widgets.config_widgets import ModelConfigManagerWidget, ModelConfigModal
from .config_manager import ModelConfigManager


class ModelConfigScreen(Screen):
    """模型配置管理界面"""
    
    BINDINGS = [
        ("escape", "app.pop_screen", "返回"),
        ("b", "return_back", "返回"),
        ("a", "add_model", "新增模型"),
        ("e", "edit_model", "编辑模型"),
        ("d", "delete_model", "删除模型"),
        ("r", "refresh", "刷新"),
    ]
    
    def compose(self) -> ComposeResult:
        """组合界面"""
        yield ModelConfigManagerWidget()
    
    @on(ModelConfigModal.ConfigSaved)
    def on_config_saved(self, event: ModelConfigModal.ConfigSaved) -> None:
        """处理配置保存事件，转发给 ModelConfigManagerWidget"""
        # 添加调试信息
        self.app.notify("DEBUG: ModelConfigScreen.on_config_saved 被调用，准备转发给 ModelConfigManagerWidget", severity="info")
        
        # 获取 ModelConfigManagerWidget 并转发消息
        manager = self.query_one(ModelConfigManagerWidget)
        manager.on_config_saved(event)
    
    @on(ModelConfigModal.ConfigTested)
    def on_config_tested(self, event: ModelConfigModal.ConfigTested) -> None:
        """处理配置测试事件，转发给 ModelConfigManagerWidget"""
        manager = self.query_one(ModelConfigManagerWidget)
        manager.on_config_tested(event)
    
    def action_add_model(self) -> None:
        """新增模型动作"""
        manager = self.query_one(ModelConfigManagerWidget)
        manager.on_add_button_pressed(None)
    
    def action_edit_model(self) -> None:
        """编辑模型动作"""
        manager = self.query_one(ModelConfigManagerWidget)
        manager.on_edit_button_pressed(None)
    
    def action_delete_model(self) -> None:
        """删除模型动作"""
        manager = self.query_one(ModelConfigManagerWidget)
        manager.on_delete_button_pressed(None)
    
    def action_refresh(self) -> None:
        """刷新动作"""
        manager = self.query_one(ModelConfigManagerWidget)
        manager.on_refresh_button_pressed(None)
    
    def action_return_back(self) -> None:
        """返回动作"""
        self.app.pop_screen()


class ModelConfigApp(App):
    """独立的模型配置管理应用"""
    
    TITLE = "KetaCLI - 模型配置管理"
    CSS_PATH = "styles.py"
    
    def compose(self) -> ComposeResult:
        """组合应用界面"""
        yield Header()
        yield ModelConfigManagerWidget()
        yield Footer()


def run_model_config_app():
    """运行模型配置管理应用"""
    app = ModelConfigApp()
    app.run()


if __name__ == "__main__":
    run_model_config_app()