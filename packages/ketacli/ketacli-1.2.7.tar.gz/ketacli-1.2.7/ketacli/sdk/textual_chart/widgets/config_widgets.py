"""
模型配置管理UI组件

提供模型配置的增删改查界面组件。
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Button, DataTable, Input, Label, Select, Static, 
    TextArea, Header, Footer, Collapsible
)
from textual.screen import ModalScreen
from textual.message import Message
from textual.reactive import reactive
from textual import on
from typing import Dict, Any, List, Optional
import json

from ..config_manager import ModelConfigManager, ModelConfigFormData


class ModelConfigTable(DataTable):
    """模型配置表格组件"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ModelConfigManager()
        self.cursor_type = "row"
        self.zebra_stripes = True
        
    def on_mount(self) -> None:
        """组件挂载时初始化表格"""
        self.add_columns(
            "模型名称", "提供商", "端点", "默认", "状态"
        )
        self.refresh_data()
    
    def refresh_data(self) -> None:
        """刷新表格数据"""
        self.clear()
        # 先刷新配置管理器以获取最新数据
        self.config_manager._refresh_config()
        models = self.config_manager.get_all_models()
        
        for index, model in enumerate(models):
            # 截断长URL显示
            endpoint = model.get('endpoint', '')
            if len(endpoint) > 40:
                endpoint = endpoint[:37] + "..."
            
            # 状态显示
            status = "✓ 正常" if model.get('api_key') else "⚠ 缺少密钥"
            
            self.add_row(
                model.get('name', ''),
                model.get('provider', 'openai'),
                endpoint,
                "✓" if model.get('is_default', False) else "",
                status,
                key=f"model_{index}"
            )
    
    def get_selected_model_name(self) -> Optional[str]:
        """获取选中的模型名称"""
        if self.cursor_row >= 0 and self.cursor_row < self.row_count:
            # 第一列是模型名称
            row_data = self.get_row_at(self.cursor_row)
            return str(row_data[0]) if row_data else None
        return None


class ModelConfigForm(Container):
    """模型配置表单组件"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.form_data = ModelConfigFormData()
        self.is_edit_mode = False
        self.original_name = ""
    
    def compose(self) -> ComposeResult:
        """组合表单界面"""
        with ScrollableContainer():
            yield Label("基本信息", classes="form-section-title")
            
            with Horizontal(classes="form-row"):
                yield Label("模型名称:", classes="form-label")
                yield Input(
                    id="name_input",
                    classes="form-input"
                )
            
            with Horizontal(classes="form-row"):
                yield Label("提供商:", classes="form-label")
                yield Select(
                    [
                        ("OpenAI", "openai"),
                        ("Anthropic", "anthropic"),
                        ("Google", "google"),
                        ("阿里云", "aliyun"),
                        ("深度求索", "deepseek"),
                        ("其他", "other")
                    ],
                    value="other",
                    id="provider_select",
                    classes="form-input"
                )
            
            with Horizontal(classes="form-row"):
                yield Label("API端点:", classes="form-label")
                yield Input(
                    id="endpoint_input",
                    classes="form-input"
                )
            
            with Horizontal(classes="form-row"):
                yield Label("API密钥:", classes="form-label")
                yield Input(
                    password=True,
                    id="api_key_input",
                    classes="form-input"
                )
            
            with Horizontal(classes="form-row"):
                yield Label("模型标识:", classes="form-label")
                yield Input(
                    id="model_input",
                    classes="form-input"
                )
            
            yield Label("高级设置", classes="form-section-title")
            
            with Horizontal(classes="form-row"):
                yield Label("最大Token:", classes="form-label")
                yield Input(
                    value="4096",
                    id="max_tokens_input",
                    classes="form-input"
                )
            
            with Horizontal(classes="form-row"):
                yield Label("温度参数:", classes="form-label")
                yield Input(
                    value="0.7",
                    id="temperature_input",
                    classes="form-input"
                )
            
            with Horizontal(classes="form-row"):
                yield Label("超时时间(秒):", classes="form-label")
                yield Input(
                    value="300",
                    id="timeout_input",
                    classes="form-input"
                )

            with Horizontal(classes="form-row"):
                yield Label("最大迭代次数:", classes="form-label")
                yield Input(
                    value="20",
                    id="max_iterations_input",
                    classes="form-input"
                )
            
            with Collapsible(title="请求头设置", collapsed=True):
                yield TextArea(
                    id="headers_textarea",
                    classes="form-textarea"
                )
            
            with Collapsible(title="额外参数", collapsed=True):
                yield TextArea(
                    id="extra_params_textarea",
                    classes="form-textarea"
                )
            
            with Horizontal(classes="form-buttons"):
                yield Button("保存", variant="primary", id="save_button")
                yield Button("取消", variant="default", id="cancel_button")
                yield Button("测试连接", variant="default", id="test_button")
    
    def load_form_data(self, form_data: ModelConfigFormData, is_edit: bool = False, original_name: str = ""):
        """加载表单数据"""
        self.form_data = form_data
        self.is_edit_mode = is_edit
        self.original_name = original_name
        
        # 填充表单字段
        self.query_one("#name_input", Input).value = form_data.name
        provider_select = self.query_one("#provider_select", Select)
        provider_select.value = form_data.provider
        # 在编辑模式下禁用提供商选择器，防止配置不一致
        provider_select.disabled = is_edit
        self.query_one("#endpoint_input", Input).value = form_data.endpoint
        self.query_one("#api_key_input", Input).value = form_data.api_key
        self.query_one("#model_input", Input).value = form_data.model
        self.query_one("#max_tokens_input", Input).value = str(form_data.max_tokens)
        self.query_one("#temperature_input", Input).value = str(form_data.temperature)
        self.query_one("#timeout_input", Input).value = str(form_data.timeout)
        try:
            self.query_one("#max_iterations_input", Input).value = str(getattr(form_data, 'max_iterations', 20))
        except Exception:
            self.query_one("#max_iterations_input", Input).value = "20"
        
        # 填充JSON字段
        if form_data.headers:
            self.query_one("#headers_textarea", TextArea).text = json.dumps(form_data.headers, indent=2, ensure_ascii=False)
        
        if form_data.extra_params:
            self.query_one("#extra_params_textarea", TextArea).text = json.dumps(form_data.extra_params, indent=2, ensure_ascii=False)
    
    def get_form_data(self) -> ModelConfigFormData:
        """获取表单数据"""
        form_data = ModelConfigFormData()
        
        form_data.name = self.query_one("#name_input", Input).value.strip()
        form_data.provider = self.query_one("#provider_select", Select).value
        form_data.endpoint = self.query_one("#endpoint_input", Input).value.strip()
        form_data.api_key = self.query_one("#api_key_input", Input).value.strip()
        form_data.model = self.query_one("#model_input", Input).value.strip()
        
        # 数值字段
        try:
            form_data.max_tokens = int(self.query_one("#max_tokens_input", Input).value)
        except ValueError:
            form_data.max_tokens = 4096
        
        try:
            form_data.temperature = float(self.query_one("#temperature_input", Input).value)
        except ValueError:
            form_data.temperature = 0.7
        
        try:
            form_data.timeout = int(self.query_one("#timeout_input", Input).value)
        except ValueError:
            form_data.timeout = 300

        try:
            form_data.max_iterations = int(self.query_one("#max_iterations_input", Input).value)
        except ValueError:
            form_data.max_iterations = 20
        
        # JSON字段
        try:
            headers_text = self.query_one("#headers_textarea", TextArea).text.strip()
            if headers_text:
                form_data.headers = json.loads(headers_text)
        except json.JSONDecodeError:
            form_data.headers = {}
        
        try:
            extra_params_text = self.query_one("#extra_params_textarea", TextArea).text.strip()
            if extra_params_text:
                form_data.extra_params = json.loads(extra_params_text)
        except json.JSONDecodeError:
            form_data.extra_params = {}
        
        return form_data
    
    @on(Button.Pressed, "#save_button")
    def on_save_button_pressed(self, event: Button.Pressed) -> None:
        """保存按钮点击事件"""
        self.post_message(self.SavePressed())
    
    @on(Button.Pressed, "#cancel_button")
    def on_cancel_button_pressed(self, event: Button.Pressed) -> None:
        """取消按钮点击事件"""
        self.post_message(self.CancelPressed())
    
    @on(Button.Pressed, "#test_button")
    def on_test_button_pressed(self, event: Button.Pressed) -> None:
        """测试连接按钮点击事件"""
        self.post_message(self.TestPressed())
    
    class SavePressed(Message):
        """保存按钮按下消息"""
        pass
    
    class CancelPressed(Message):
        """取消按钮按下消息"""
        pass
    
    class TestPressed(Message):
        """测试按钮按下消息"""
        pass


class ModelConfigModal(ModalScreen):
    """模型配置编辑模态框"""
    
    DEFAULT_CSS = """
    ModelConfigModal {
        align: center middle;
    }
    
    .modal-container {
        width: 80%;
        height: 80%;
        background: $surface;
        border: thick $primary;
    }
    
    #modal_header {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
        content-align: center middle;
    }
    
    #modal_content {
        padding: 1;
    }
    
    .form-section-title {
        margin: 1 0;
        text-style: bold;
        color: $primary;
    }
    
    .form-row {
        height: 3;
        margin: 0 0 1 0;
    }
    
    .form-label {
        width: 20;
        content-align: right middle;
        margin: 0 1 0 0;
    }
    
    .form-input {
        width: 1fr;
    }
    
    .form-textarea {
        height: 8;
        margin: 1 0;
    }
    
    .form-buttons {
        dock: bottom;
        height: 3;
        margin: 1 0 0 0;
        align: center middle;
    }
    
    .form-buttons Button {
        margin: 0 1;
    }
    """
    
    def __init__(self, title: str = "模型配置", form_data: ModelConfigFormData = None, is_edit: bool = False, original_name: str = "", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.form_data = form_data or ModelConfigFormData()
        self.is_edit = is_edit
        self.original_name = original_name
    
    def compose(self) -> ComposeResult:
        """组合模态框界面"""
        with Container(id="modal_container"):
            yield Header(self.title, id="modal_header")
            with Container(id="modal_content"):
                yield ModelConfigForm()
    
    def on_mount(self) -> None:
        """模态框挂载时加载数据"""
        form = self.query_one(ModelConfigForm)
        form.load_form_data(self.form_data, self.is_edit, self.original_name)
    
    @on(ModelConfigForm.SavePressed)
    def on_save_pressed(self, event: ModelConfigForm.SavePressed) -> None:
        """处理保存事件"""
        self.app.notify("DEBUG: ModelConfigModal.on_save_pressed 被调用", severity="info")
        
        form = self.query_one(ModelConfigForm)
        form_data = form.get_form_data()
        
        self.app.notify(f"DEBUG: 获取到表单数据，模型名={form_data.name}", severity="info")
        
        # 验证数据
        errors = form_data.validate()
        if errors:
            self.app.notify("验证失败: " + "；".join(errors), severity="error")
            return
        
        self.app.notify("DEBUG: 数据验证通过，准备发送 ConfigSaved 消息", severity="info")
        
        # 发送保存消息
        self.post_message(self.ConfigSaved(form_data, self.is_edit, self.original_name))
        self.app.notify("DEBUG: ConfigSaved 消息已发送", severity="info")
        self.dismiss()
    
    @on(ModelConfigForm.CancelPressed)
    def on_cancel_pressed(self, event: ModelConfigForm.CancelPressed) -> None:
        """处理取消事件"""
        self.dismiss()
    
    @on(ModelConfigForm.TestPressed)
    def on_test_pressed(self, event: ModelConfigForm.TestPressed) -> None:
        """处理测试连接事件"""
        form = self.query_one(ModelConfigForm)
        form_data = form.get_form_data()
        self.post_message(self.ConfigTested(form_data))
    
    class ConfigSaved(Message):
        """配置保存消息"""
        def __init__(self, form_data: ModelConfigFormData, is_edit: bool, original_name: str):
            super().__init__()
            self.form_data = form_data
            self.is_edit = is_edit
            self.original_name = original_name
    
    class ConfigTested(Message):
        """配置测试消息"""
        def __init__(self, form_data: ModelConfigFormData):
            super().__init__()
            self.form_data = form_data


class ModelConfigManagerWidget(Container):
    """模型配置管理主界面"""
    
    DEFAULT_CSS = """
    ModelConfigManagerWidget {
        height: 100%;
    }
    
    #config_header {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
    }
    
    #config_toolbar {
        dock: top;
        height: 3;
        background: $surface;
        padding: 0 1;
    }
    
    #config_content {
        padding: 1;
    }
    
    #config_table {
        height: 1fr;
    }
    
    .toolbar-button {
        margin: 0 1 0 0;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ModelConfigManager()
    
    def compose(self) -> ComposeResult:
        """组合管理界面"""
        with Container(id="config_header"):
            yield Label("模型配置管理", classes="header-title")
        
        with Horizontal(id="config_toolbar"):
            yield Button("返回", variant="default", id="return_button", classes="toolbar-button")
            yield Button("新增", variant="primary", id="add_button", classes="toolbar-button")
            yield Button("编辑", variant="default", id="edit_button", classes="toolbar-button")
            yield Button("删除", variant="error", id="delete_button", classes="toolbar-button")
            yield Button("复制", variant="default", id="copy_button", classes="toolbar-button")
            yield Button("设为默认", variant="default", id="default_button", classes="toolbar-button")
            yield Button("刷新", variant="default", id="refresh_button", classes="toolbar-button")
        
        with Container(id="config_content"):
            yield ModelConfigTable(id="config_table")
    
    def on_mount(self) -> None:
        """组件挂载时刷新数据"""
        self.refresh_table()
    
    def refresh_table(self) -> None:
        """刷新表格数据"""
        table = self.query_one("#config_table", ModelConfigTable)
        table.refresh_data()
    
    @on(Button.Pressed, "#return_button")
    def on_return_button_pressed(self, event: Button.Pressed) -> None:
        """返回按钮点击事件"""
        self.app.pop_screen()
    
    @on(Button.Pressed, "#add_button")
    def on_add_button_pressed(self, event: Button.Pressed) -> None:
        """新增按钮点击事件"""
        modal = ModelConfigModal(title="新增模型配置")
        self.app.push_screen(modal)
    
    @on(Button.Pressed, "#edit_button")
    def on_edit_button_pressed(self, event: Button.Pressed) -> None:
        """编辑按钮点击事件"""
        table = self.query_one("#config_table", ModelConfigTable)
        model_name = table.get_selected_model_name()
        
        if not model_name:
            self.app.notify("请选择要编辑的模型", severity="warning")
            return
        
        form_data = self.config_manager.get_model_config(model_name)
        if form_data:
            modal = ModelConfigModal(
                title=f"编辑模型配置 - {model_name}",
                form_data=form_data,
                is_edit=True,
                original_name=model_name
            )
            self.app.push_screen(modal)
        else:
            self.app.notify("获取模型配置失败", severity="error")
    
    @on(Button.Pressed, "#delete_button")
    def on_delete_button_pressed(self, event: Button.Pressed) -> None:
        """删除按钮点击事件"""
        table = self.query_one("#config_table", ModelConfigTable)
        model_name = table.get_selected_model_name()
        
        if not model_name:
            self.app.notify("请选择要删除的模型", severity="warning")
            return
        
        # TODO: 添加确认对话框
        success, message = self.config_manager.delete_model(model_name)
        if success:
            self.app.notify(message, severity="success")
            self.refresh_table()
        else:
            self.app.notify(message, severity="error")
    
    @on(Button.Pressed, "#copy_button")
    def on_copy_button_pressed(self, event: Button.Pressed) -> None:
        """复制按钮点击事件"""
        table = self.query_one("#config_table", ModelConfigTable)
        model_name = table.get_selected_model_name()
        
        if not model_name:
            self.app.notify("请选择要复制的模型", severity="warning")
            return
        
        new_name = f"{model_name}_copy"
        success, message = self.config_manager.duplicate_model(model_name, new_name)
        if success:
            self.app.notify(message, severity="success")
            self.refresh_table()
        else:
            self.app.notify(message, severity="error")
    
    @on(Button.Pressed, "#default_button")
    def on_default_button_pressed(self, event: Button.Pressed) -> None:
        """设为默认按钮点击事件"""
        table = self.query_one("#config_table", ModelConfigTable)
        model_name = table.get_selected_model_name()
        
        if not model_name:
            self.app.notify("请选择要设为默认的模型", severity="warning")
            return
        
        success, message = self.config_manager.set_default_model(model_name)
        if success:
            self.app.notify(message, severity="success")
            self.refresh_table()
        else:
            self.app.notify(message, severity="error")
    
    @on(Button.Pressed, "#refresh_button")
    def on_refresh_button_pressed(self, event: Button.Pressed) -> None:
        """刷新按钮点击事件"""
        self.refresh_table()
        self.app.notify("数据已刷新", severity="info")
    
    @on(ModelConfigModal.ConfigSaved)
    def on_config_saved(self, event: ModelConfigModal.ConfigSaved) -> None:
        """处理配置保存事件"""
        # 调试信息：确认方法被调用
        self.app.notify(f"DEBUG: on_config_saved 被调用，模式={'编辑' if event.is_edit else '新增'}，模型名={event.form_data.name}", severity="info")
        
        if event.is_edit:
            success, message = self.config_manager.update_model(event.original_name, event.form_data)
        else:
            success, message = self.config_manager.add_model(event.form_data)
        
        self.app.notify(f"DEBUG: 保存结果 success={success}, message={message}", severity="info")
        
        if success:
            self.app.notify(message, severity="success")
            self.refresh_table()
        else:
            self.app.notify(message, severity="error")
    
    @on(ModelConfigModal.ConfigTested)
    def on_config_tested(self, event: ModelConfigModal.ConfigTested) -> None:
        """处理配置测试事件"""
        # TODO: 实现配置测试逻辑
        self.app.notify("配置测试功能待实现", severity="warning")