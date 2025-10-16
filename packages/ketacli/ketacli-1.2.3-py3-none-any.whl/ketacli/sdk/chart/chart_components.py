"""图表可视化组件模块

基于textual和textual-plot实现的图表组件，支持折线图、柱状图等多种图表类型。
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button, Select, Label, DataTable, SelectionList, Checkbox
from textual.reactive import reactive
from textual.message import Message
from textual.screen import ModalScreen
from textual.binding import Binding

from textual_plotext import PlotextPlot
from rich.text import Text
from ketacli.sdk.chart.utils import format


class ChartTypeSelector(Static):
    """图表类型选择器组件"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chart_types = [
            ("line", "折线图"),
            ("bar", "柱状图"),
            # 可以扩展更多图表类型
        ]
    
    def compose(self) -> ComposeResult:
        """构建图表类型选择器UI"""
        with Horizontal():
            yield Label("图表类型:", classes="chart-label")
            yield Select(
                options=[(name, value) for value, name in self.chart_types],
                value="line",
                id="chart-type-select",
                classes="chart-type-select"
            )
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """处理图表类型选择变化"""
        if event.select.id == "chart-type-select":
            self.post_message(self.ChartTypeChanged(event.value))
    
    class ChartTypeChanged(Message):
        """图表类型变化消息"""
        def __init__(self, chart_type: str):
            super().__init__()
            self.chart_type = chart_type


class FieldConfigModal(ModalScreen):
    """图表字段配置弹窗"""
    
    BINDINGS = [
        Binding("escape", "dismiss", "关闭弹窗"),
        Binding("enter", "confirm_config", "确认配置"),
    ]
    
    def __init__(self, fields: List[str], chart_type: str = "line", current_config: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.available_fields = fields
        self.chart_type = chart_type
        self.current_config = current_config or {"x_field": None, "y_fields": [], "group_field": None}
        self.x_field = self.current_config.get("x_field")
        self.y_fields = self.current_config.get("y_fields", [])
        self.group_field = self.current_config.get("group_field")
    
    def _sanitize_field_id(self, field: str) -> str:
        """清理字段名，生成有效的ID"""
        import re
        # 将特殊字符替换为下划线，确保ID有效
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', field)
        # 确保不以数字开头
        if sanitized and sanitized[0].isdigit():
            sanitized = f"field_{sanitized}"
        return sanitized
    

    
    def compose(self) -> ComposeResult:
        """构建弹窗UI"""
        with Container(id="config-modal", classes="config-modal"):
            with Vertical(classes="config-content"):
                yield Label(f"{self.chart_type}图表字段配置", classes="modal-title")
                
                with Horizontal(classes="field-row"):
                    yield Label("X轴字段:", classes="field-label")
                    yield Select(
                        options=[(field, field) for field in self.available_fields],
                        id="x-field-select",
                        classes="field-select"
                    )
                
                with Horizontal(classes="field-row"):
                    yield Label("Y轴字段:", classes="field-label")
                    with Vertical(id="y-field-checkboxes", classes="y-field-checkboxes"):
                        for field in self.available_fields:
                            field_id = self._sanitize_field_id(field)
                            yield Checkbox(field, id=f"y-field-{field_id}", classes="y-field-checkbox")
                
                with Horizontal(classes="field-row"):
                    yield Label("分组字段:", classes="field-label")
                    group_options = [("无分组", None)] + [(field, field) for field in self.available_fields]
                    yield Select(
                        options=group_options,
                        id="group-field-select",
                        classes="field-select"
                    )
                
                with Horizontal(classes="button-row"):
                    yield Button("确认", id="confirm-config", variant="primary")
                    yield Button("取消", id="cancel-config", variant="default")
    
    def on_mount(self) -> None:
        """弹窗挂载时自动选择字段"""
        self._auto_select_fields()
    
    def _auto_select_fields(self):
        """自动选择合适的字段或加载当前配置"""
        if not self.available_fields:
            return
            
        x_select = self.query_one("#x-field-select", Select)
        
        # 如果有当前配置，优先使用当前配置
        if self.x_field and self.x_field in self.available_fields:
            x_select.value = self.x_field
        else:
            # 自动选择X轴字段（时间字段）
            if "_time" in self.available_fields:
                x_select.value = "_time"
            elif "time" in self.available_fields:
                x_select.value = "time"
            elif "timestamp" in self.available_fields:
                x_select.value = "timestamp"
            elif self.available_fields:
                x_select.value = self.available_fields[0]
        
        # 设置分组字段
        group_select = self.query_one("#group-field-select", Select)
        if self.group_field and self.group_field in self.available_fields:
            group_select.value = self.group_field
        else:
            group_select.value = None  # 默认无分组
        
        # 如果有当前Y轴配置，优先使用当前配置
        if self.y_fields:
            for field in self.y_fields:
                if field in self.available_fields:
                    field_id = self._sanitize_field_id(field)
                    checkbox = self.query_one(f"#y-field-{field_id}", Checkbox)
                    checkbox.value = True
        else:
            # 自动选择Y轴字段（数值字段）- 支持多选
            auto_select_fields = []
            if "count" in self.available_fields:
                auto_select_fields.append("count")
            if "value" in self.available_fields:
                auto_select_fields.append("value")
            if "eventsNum" in self.available_fields:
                auto_select_fields.append("eventsNum")
            
            # 如果没有找到常见字段，选择第二个字段（第一个通常是时间字段）
            if not auto_select_fields and len(self.available_fields) > 1:
                auto_select_fields.append(self.available_fields[1])
                
            # 设置选中状态
            for field in auto_select_fields:
                if field in self.available_fields:
                    field_id = self._sanitize_field_id(field)
                    checkbox = self.query_one(f"#y-field-{field_id}", Checkbox)
                    checkbox.value = True
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        if event.button.id == "confirm-config":
            self.action_confirm_config()
        elif event.button.id == "cancel-config":
            self.dismiss()
    
    def action_confirm_config(self) -> None:
        """确认配置"""
        x_select = self.query_one("#x-field-select", Select)
        group_select = self.query_one("#group-field-select", Select)
        
        self.x_field = x_select.value
        self.group_field = group_select.value
        
        # 获取所有选中的Y轴字段
        self.y_fields = []
        for field in self.available_fields:
            field_id = self._sanitize_field_id(field)
            checkbox = self.query_one(f"#y-field-{field_id}", Checkbox)
            if checkbox.value:
                self.y_fields.append(field)
        
        if self.x_field and self.y_fields:
            self.dismiss((self.x_field, self.y_fields, self.group_field))
        else:
            # 如果没有选择字段，显示提示
            pass
    
    def action_dismiss(self) -> None:
        """关闭弹窗"""
        self.dismiss()


class FieldConfigSelector(Static):
    """数据字段配置选择器（保留用于兼容性）"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.available_fields = []
        self.x_field = None
        self.y_field = None
        self.y_fields = []  # 支持多个Y轴字段
    
    def compose(self) -> ComposeResult:
        """构建字段配置UI"""
        with Vertical():
            yield Label("按 Ctrl+F 配置图表字段", classes="config-hint")
    
    def update_fields(self, fields: List[str]):
        """更新可用字段列表"""
        self.available_fields = fields
    
    class FieldConfigChanged(Message):
        """字段配置变化消息"""
        def __init__(self, x_field: str, y_fields: List[str]):
            super().__init__()
            self.x_field = x_field
            self.y_fields = y_fields
            # 为了兼容现有代码，设置第一个Y字段
            self.y_field = y_fields[0] if y_fields else None




class ChartContainer(Static):
    """图表容器组件"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chart_type = "line"
        self.data = []
        self.x_field = "_time"
        self.y_field = "count"
        self.y_fields = []  # 支持多个Y轴字段
        # 生成唯一的容器ID，避免重复ID冲突
        import uuid
        self.container_id = str(uuid.uuid4())[:8]
        self._updating = False  # 防止并发更新
    
    def _is_timestamp_field(self, field_name: str, data: List[Dict]) -> bool:
        """检测字段是否为时间戳字段"""
        # 检查字段名是否包含时间相关关键词
        time_keywords = ['time', 'timestamp', 'date', 'datetime', '_time']
        field_lower = field_name.lower()
        
        # 如果字段名包含时间关键词，进一步检查数据
        if any(keyword in field_lower for keyword in time_keywords):
            # 检查前几个数据点的值是否像时间戳
            for row in data[:5]:  # 只检查前5行
                if field_name in row and row[field_name] is not None:
                    value = row[field_name]
                    # 检查是否为数字类型的时间戳
                    if isinstance(value, (int, float)):
                        # 检查是否在合理的时间戳范围内（1970-2050年）
                        if 0 < value < 2524608000000:  # 毫秒时间戳范围
                            return True
                        elif 0 < value < 2524608000:  # 秒时间戳范围
                            return True
                    # 检查是否为时间字符串格式
                    elif isinstance(value, str):
                        try:
                            # 尝试解析ISO格式时间字符串
                            datetime.fromisoformat(value.replace('Z', '+00:00'))
                            return True
                        except:
                            pass
        return False
    
    def _is_numeric_field(self, field_name: str, data: List[Dict]) -> bool:
        """检测字段是否为数值字段"""
        if not data:
            return False
            
        # 检查前几个数据点的值是否为数值类型
        for row in data[:5]:  # 只检查前5行
            if field_name in row and row[field_name] is not None:
                value = row[field_name]
                if isinstance(value, (int, float)):
                    return True
                elif isinstance(value, str):
                    try:
                        float(value)
                        return True
                    except ValueError:
                        continue
        return False
    
    def _is_suitable_for_line_chart(self, field_name: str, data: List[Dict]) -> bool:
        """检测字段是否适合绘制折线图（数值或时间字段）"""
        return self._is_timestamp_field(field_name, data) or self._is_numeric_field(field_name, data)
    
    def _format_timestamp_for_display(self, value, field_name: str) -> str:
        """将时间戳转换为格式化的时间字符串用于显示"""
        try:
            if isinstance(value, (int, float)):
                # 判断是毫秒还是秒时间戳
                if value > 1000000000000:  # 毫秒时间戳
                    # 使用与plotext期望格式匹配的格式
                    return format(value, 'timestamp_ms', format='%Y-%m-%d %H:%M:%S')
                else:  # 秒时间戳
                    return format(value, 'timestamp_s', format='%Y-%m-%d %H:%M:%S')
            elif isinstance(value, str):
                # 尝试解析时间字符串
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
        return str(value)
    
    def compose(self) -> ComposeResult:
        """构建图表容器UI"""
        with Container(id="chart-content", classes="chart-content"):
            yield Static("请选择图表类型和配置数据字段", id="chart-placeholder")
    
    def update_chart(self, chart_type: str, data: List[Dict], x_field: str, y_fields: List[str], group_field: str = None):
        """更新图表显示 - 直接在主界面显示图表"""
        # 防止并发更新
        if self._updating:
            return
        
        print(f"[DEBUG] ChartContainer.update_chart called:")
        print(f"  chart_type: {chart_type}")
        print(f"  x_field: {x_field}")
        print(f"  y_fields: {y_fields}")
        print(f"  group_field: {group_field}")
        print(f"  data length: {len(data) if data else 0}")
        if data and len(data) > 0:
            print(f"  sample data keys: {list(data[0].keys())}")
        
        self._updating = True
        try:
            self.chart_type = chart_type
            self.data = data
            self.x_field = x_field
            self.y_fields = y_fields
            self.group_field = group_field
            # 为了兼容现有代码，设置第一个Y字段
            self.y_field = y_fields[0] if y_fields else None
            
            # 清除现有内容
            chart_content = self.query_one("#chart-content")
            chart_content.remove_children()
            
            if not data:
                chart_content.mount(Static("暂无数据可显示", classes="chart-placeholder"))
                return
            
            # 准备图表数据 - 为每个Y字段准备独立的数据系列
            chart_data_series = self._prepare_chart_data_series(data, x_field, y_fields, group_field)
            
            if not chart_data_series:
                chart_content.mount(Static("数据格式不正确或为空", classes="chart-placeholder"))
                return
            
            # 直接显示图表内容
            try:
                from textual_plotext import PlotextPlot
                
                # 创建PlotextPlot并设置尺寸
                plot_widget = PlotextPlot(classes="chart-widget")
                plot_widget.styles.height = "1fr"
                plot_widget.styles.width = "100%"
                plot_widget.styles.min_height = "15"
                
                # 先挂载PlotextPlot
                chart_content.mount(plot_widget)
                
                # 使用call_after_refresh确保在下一个刷新周期后绘制图表
                def draw_chart():
                    try:
                        if chart_data_series:
                            print(f"[DEBUG] draw_chart called with {len(chart_data_series)} series:")
                            for series_name, series_data in chart_data_series.items():
                                print(f"  Series '{series_name}': {len(series_data)} data points")
                            
                            # 清除之前的图表
                            plot_widget.plt.clear_data()
                            
                            # 检测x_field是否为时间戳字段
                            is_timestamp = self._is_timestamp_field(x_field, data)
                            print(f"  x_field '{x_field}' is timestamp: {is_timestamp}")
                            
                            # 如果是折线图，检查X轴字段是否适合绘制折线图
                            if chart_type == "line" and not self._is_suitable_for_line_chart(x_field, data):
                                error_text = f"无法绘制折线图：X轴字段 '{x_field}' 不是数值或时间字段。\n\n折线图要求X轴为连续的数值或时间数据。\n请通过 ctrl+f 选择数值字段或时间字段作为X轴，或切换到柱状图。"
                                chart_content.remove_children()
                                chart_content.mount(Static(error_text, classes="chart-error"))
                                return
                            
                            # 为每个Y字段绘制一条线/柱
                            # 如果是时间戳字段，设置时间格式
                            if is_timestamp:
                                # plotext库的date_form方法期望不带%的格式
                                plotext_format = "Y-m-d H:M:S"
                                try:
                                    plot_widget.plt.date_form(plotext_format)
                                    print(f"  Set time format: {plotext_format}")
                                except Exception as e:
                                    print(f"  Warning: Failed to set date format: {e}")
                            
                            # 检查是否有分组字段，决定使用单柱状图还是分组柱状图
                            if chart_type == "bar" and group_field and len(chart_data_series) > 1:
                                # 使用分组柱状图 (multiple_bar)
                                print(f"  Using multiple_bar for grouped data with {len(chart_data_series)} series")
                                
                                # 收集所有唯一的X值
                                all_x_values = set()
                                for series_data in chart_data_series.values():
                                    for item in series_data:
                                        all_x_values.add(item[0])
                                
                                # 排序X值
                                sorted_x_values = sorted(all_x_values)
                                
                                # 如果是时间戳字段，转换为格式化的时间字符串
                                if is_timestamp:
                                    x_labels = [self._format_timestamp_for_display(x_val, x_field) for x_val in sorted_x_values]
                                else:
                                    x_labels = [str(x_val) for x_val in sorted_x_values]
                                
                                # 为每个系列准备Y值数组
                                y_data_arrays = []
                                series_labels = []
                                
                                for series_name, series_data in chart_data_series.items():
                                    # 创建一个字典来快速查找Y值
                                    y_dict = {item[0]: item[1] for item in series_data}
                                    
                                    # 为每个X值创建对应的Y值，缺失的用0填充
                                    y_values = [y_dict.get(x_val, 0) for x_val in sorted_x_values]
                                    
                                    y_data_arrays.append(y_values)
                                    series_labels.append(series_name)
                                    print(f"    Series '{series_name}': {len(y_values)} values")
                                
                                # 使用multiple_bar绘制分组柱状图
                                if y_data_arrays and x_labels:
                                    plot_widget.plt.multiple_bar(x_labels, y_data_arrays, label=series_labels)
                                    print(f"  Drew multiple_bar with {len(x_labels)} categories and {len(y_data_arrays)} series")
                            else:
                                # 使用普通的单系列绘图
                                for i, (y_field, series_data) in enumerate(chart_data_series.items()):
                                    if series_data:
                                        x_values = [item[0] for item in series_data]
                                        y_values = [item[1] for item in series_data]
                                        
                                        # 如果是时间戳字段，转换为格式化的时间字符串
                                        if is_timestamp and len(x_values) > 0:
                                            # 将时间戳转换为格式化的时间字符串
                                            formatted_x_values = []
                                            for x_val in x_values:
                                                formatted_time = self._format_timestamp_for_display(x_val, x_field)
                                                formatted_x_values.append(formatted_time)
                                            
                                            if len(formatted_x_values) > 0 and len(y_values) > 0:
                                                print(f"  Drawing time series '{y_field}' with {len(formatted_x_values)} points")
                                                if chart_type == "bar":
                                                    plot_widget.plt.bar(formatted_x_values, y_values, label=y_field)
                                                else:
                                                    plot_widget.plt.plot(formatted_x_values, y_values, label=y_field)
                                        else:
                                            # 非时间戳字段，直接使用原始值
                                            if len(x_values) > 0 and len(y_values) > 0:
                                                print(f"  Drawing series '{y_field}' with {len(x_values)} points")
                                                if chart_type == "bar":
                                                    plot_widget.plt.bar(x_values, y_values, label=y_field)
                                                else:
                                                    plot_widget.plt.plot(x_values, y_values, label=y_field)
                            
                            # 设置坐标轴标签
                            plot_widget.plt.xlabel(x_field)
                            if len(y_fields) == 1:
                                plot_widget.plt.ylabel(y_fields[0])
                            else:
                                plot_widget.plt.ylabel("值")
                            
                            # plotext库会根据label参数自动显示图例，无需手动调用show_legend
                            print(f"  Chart data series count: {len(chart_data_series)}")
                            if len(chart_data_series) > 1:
                                print("  Legend will be automatically shown based on labels")
                            else:
                                print("  Not showing legend (only one series)")
                            
                            # 强制刷新PlotextPlot
                            plot_widget.refresh()
                    except Exception as e:
                        print(f"[ERROR] draw_chart failed: {e}")
                        import traceback
                        traceback.print_exc()
                        # 显示错误信息给用户
                        error_text = f"图表绘制失败: {str(e)}"
                        chart_content.remove_children()
                        chart_content.mount(Static(error_text, classes="chart-error"))
                
                # 延迟绘制图表，确保PlotextPlot已完全挂载
                def delayed_draw():
                    self.call_after_refresh(draw_chart)
                
                self.call_after_refresh(delayed_draw)
            except ImportError:
                # 如果textual-plot不可用，显示简单的数据摘要
                y_fields_str = ", ".join(self.y_fields) if self.y_fields else "无"
                summary_text = f"图表类型: {chart_type}\n数据点数: {len(chart_data)}\nX轴: {x_field}\nY轴: {y_fields_str}"
                chart_content.mount(Static(summary_text, classes="chart-summary"))
                
        finally:
            self._updating = False
    

    
    def _prepare_chart_data_series(self, data: List[Dict], x_field: str, y_fields: List[str], group_field: str = None) -> Dict[str, List[Tuple]]:
        """准备图表数据系列 - 为每个Y字段准备独立的数据系列，支持分组"""
        print(f"[DEBUG] _prepare_chart_data_series called:")
        print(f"  x_field: {x_field}")
        print(f"  y_fields: {y_fields}")
        print(f"  group_field: {group_field}")
        print(f"  data length: {len(data) if data else 0}")
        
        if not y_fields:
            print("  no y_fields, returning empty dict")
            return {}
        
        # 检测x_field是否为时间戳字段
        is_timestamp = self._is_timestamp_field(x_field, data)
        print(f"  x_field '{x_field}' is timestamp: {is_timestamp}")
        
        # 如果有分组字段，按分组创建数据系列
        if group_field and data and group_field in data[0]:
            print(f"  has group field: {group_field}")
            # 获取所有分组值
            group_values = set()
            for row in data:
                if group_field in row and row[group_field] is not None:
                    group_values.add(str(row[group_field]))
            
            print(f"  group_values: {sorted(group_values)}")
            
            # 为每个分组和Y字段的组合创建数据系列
            chart_data_series = {}
            for group_val in sorted(group_values):
                for y_field in y_fields:
                    series_key = f"{y_field}_{group_val}" if len(y_fields) > 1 else group_val
                    chart_data_series[series_key] = []
                    print(f"  created series key: {series_key}")
        else:
            print("  no group field, creating series for each y_field")
            # 没有分组字段时，为每个Y字段创建独立的数据系列
            chart_data_series = {y_field: [] for y_field in y_fields}
            print(f"  created series keys: {list(chart_data_series.keys())}")
        
        for row in data:
            if x_field in row:
                try:
                    x_val = row[x_field]
                    x_display_val = x_val  # 用于显示的值
                    
                    # 处理时间字段
                    if is_timestamp:
                        # 如果是时间戳字段，转换为格式化时间用于显示
                        x_display_val = self._format_timestamp_for_display(x_val, x_field)
                        
                        # 对于绘图，确保x_val是数值类型
                        if isinstance(x_val, str):
                            try:
                                # 尝试解析时间字符串为时间戳
                                dt = datetime.fromisoformat(x_val.replace('Z', '+00:00'))
                                x_val = dt.timestamp()
                            except:
                                # 如果解析失败，保持原始字符串值
                                x_val = str(x_val)
                        elif not isinstance(x_val, (int, float)):
                            x_val = 0  # 默认值
                    elif x_field in ['_time', 'time'] and isinstance(x_val, str):
                        try:
                            # 尝试解析时间字符串
                            dt = datetime.fromisoformat(x_val.replace('Z', '+00:00'))
                            x_val = dt.timestamp()
                            x_display_val = self._format_timestamp_for_display(x_val, x_field)
                        except:
                            # 如果解析失败，保持原始字符串值
                            x_val = str(x_val)
                            x_display_val = str(x_val)
                    elif not isinstance(x_val, (int, float)):
                        # 如果X值不是数字，保持原始值（字符串）
                        x_val = str(x_val)
                        x_display_val = str(x_val)
                    
                    # 根据是否有分组字段处理数据
                    if group_field and group_field in row and row[group_field] is not None:
                        # 有分组字段时，按分组处理数据
                        group_val = str(row[group_field])
                        print(f"    processing grouped data for group: {group_val}")
                        for y_field in y_fields:
                            series_key = f"{y_field}_{group_val}" if len(y_fields) > 1 else group_val
                            if series_key in chart_data_series:
                                if y_field in row:
                                    y_val = row[y_field]
                                    # 处理数值字段
                                    if isinstance(y_val, str):
                                        try:
                                            y_val = float(y_val)
                                        except:
                                            y_val = 0  # 默认值
                                    elif not isinstance(y_val, (int, float)):
                                        y_val = 0  # 默认值
                                    
                                    chart_data_series[series_key].append((x_val, y_val))
                                    print(f"      added data point to {series_key}: ({x_val}, {y_val})")
                                else:
                                    # 缺失字段默认为0
                                    chart_data_series[series_key].append((x_val, 0))
                                    print(f"      added default data point to {series_key}: ({x_val}, 0)")
                    else:
                        # 没有分组字段时，为每个Y字段处理数据
                        print(f"    processing non-grouped data")
                        for y_field in y_fields:
                            if y_field in row:
                                y_val = row[y_field]
                                # 处理数值字段
                                if isinstance(y_val, str):
                                    try:
                                        y_val = float(y_val)
                                    except:
                                        y_val = 0  # 默认值
                                elif not isinstance(y_val, (int, float)):
                                    y_val = 0  # 默认值
                                
                                chart_data_series[y_field].append((x_val, y_val))
                                print(f"      added data point to {y_field}: ({x_val}, {y_val})")
                            else:
                                # 缺失字段默认为0
                                chart_data_series[y_field].append((x_val, 0))
                                print(f"      added default data point to {y_field}: ({x_val}, 0)")
                    
                except (ValueError, TypeError):
                    continue
        
        print(f"  final chart_data_series keys: {list(chart_data_series.keys())}")
        print(f"  series lengths: {[(k, len(v)) for k, v in chart_data_series.items()]}")
        return chart_data_series
    
    def _prepare_chart_data(self, data: List[Dict], x_field: str, y_fields: List[str], group_field: str = None) -> List[Tuple]:
        """准备图表数据 - 兼容性方法，保留用于向后兼容"""
        chart_data_series = self._prepare_chart_data_series(data, x_field, y_fields, group_field)
        
        # 如果只有一个Y字段，返回该字段的数据
        if len(y_fields) == 1:
            return chart_data_series.get(y_fields[0], [])
        
        # 多个Y字段时，合并所有数据（向后兼容）
        chart_data = []
        for y_field, series_data in chart_data_series.items():
            chart_data.extend(series_data)
        
        return chart_data
    
    def clear_chart(self):
        """清除图表"""
        chart_content = self.query_one("#chart-content")
        chart_content.remove_children()
        # 不再添加占位符文本，让图表内容直接显示
        self.current_chart = None


class ChartVisualizationWidget(Static):
    """图表可视化主组件"""
    
    BINDINGS = [
        Binding("ctrl+o", "open_field_config", "配置图表字段"),
        Binding("ctrl+f", "refresh_chart", "刷新图表"),
    ]
    
    def __init__(self, chart_type="line", **kwargs):
        
        self.data = kwargs.pop("data", [])
        self.fields = []
        self.chart_configured = False
        self.chart_type = chart_type
        # 为每个图表类型创建独立的配置存储
        self.chart_configs = {
            "line": {"x_field": None, "y_fields": [], "group_field": None},
            "bar": {"x_field": None, "y_fields": [], "group_field": None}
        }
        # 保留兼容性字段
        self.x_field = kwargs.pop("x_field", None)
        self.y_fields = kwargs.pop("y_fields", None) or []
        self.y_field = kwargs.pop("y_field", None)
        self.group_field = kwargs.pop("group_field", None)
        super().__init__(**kwargs)
    
    def compose(self) -> ComposeResult:
        """构建图表可视化UI"""
        with Vertical():
            # 字段配置选择器
            yield FieldConfigSelector(id="field-config-selector")
            
            # 图表容器
            yield ChartContainer(id="chart-container")
    
    def update_data(self, data: List[Dict]):
        """更新数据并检查字段配置"""
        self.data = data
        if not data:
            self.fields = []
            self._show_field_config()
            return
        
        # 提取字段列表
        self.fields = list(data[0].keys()) if data else []
        
        # 自动选择字段并渲染图表
        self._auto_select_fields()
        
        if self.x_field and (self.y_field or self.y_fields):
            # 如果有y_fields使用y_fields，否则使用单个y_field
            y_fields_to_use = self.y_fields if self.y_fields else [self.y_field] if self.y_field else []
            if y_fields_to_use:
                self._render_chart(self.chart_type, self.x_field, y_fields_to_use, self.group_field)
    
    def _needs_field_config(self) -> bool:
        """检查是否需要字段配置"""
        # 总是显示字段配置，让用户选择合适的字段
        return True
    
    def _show_field_config(self):
        """显示字段配置界面"""
        field_config = self.query_one("#field-config-selector", FieldConfigSelector)
        field_config.remove_class("hidden")
        field_config.update_fields(self.fields)
        
        # 隐藏图表容器
        chart_container = self.query_one("#chart-container", ChartContainer)
        chart_container.clear_chart()
    
    def _auto_select_fields(self):
        """自动选择字段或加载当前图表类型的配置"""
        # 获取当前图表类型的配置
        current_config = self.chart_configs.get(self.chart_type, {"x_field": None, "y_fields": [], "group_field": None})
        
        # 如果当前图表类型已有配置且字段仍然可用，使用已有配置
        if (current_config["x_field"] and current_config["x_field"] in self.fields and
            current_config["y_fields"] and all(field in self.fields for field in current_config["y_fields"])):
            self.x_field = current_config["x_field"]
            self.y_fields = current_config["y_fields"]
            self.group_field = current_config.get("group_field")
            # 为了兼容现有代码，设置第一个Y字段
            self.y_field = self.y_fields[0] if self.y_fields else None
            return
        
        # 否则进行自动选择
        # 自动选择X轴字段（时间字段）
        if "_time" in self.fields:
            self.x_field = "_time"
        elif "time" in self.fields:
            self.x_field = "time"
        elif "timestamp" in self.fields:
            self.x_field = "timestamp"
        elif self.fields:
            self.x_field = self.fields[0]
            
        # 自动选择Y轴字段（数值字段）
        # 优先选择常见的数值字段
        preferred_y_fields = ["count", "value", "eventsNum"]
        selected_y_fields = []
        
        for field in preferred_y_fields:
            if field in self.fields:
                selected_y_fields.append(field)
        
        # 如果没有找到常见字段，选择除X轴外的其他字段
        if not selected_y_fields and len(self.fields) > 1:
            for field in self.fields:
                if field != self.x_field:
                    selected_y_fields.append(field)
                    break  # 默认只选择一个字段
        
        self.y_fields = selected_y_fields
        # 为了兼容现有代码，设置第一个Y字段
        self.y_field = selected_y_fields[0] if selected_y_fields else None
        
        # 保存配置到当前图表类型
        self.chart_configs[self.chart_type] = {
            "x_field": self.x_field,
            "y_fields": self.y_fields,
            "group_field": self.group_field
        }
    
    def action_open_field_config(self) -> None:
        """打开字段配置弹窗"""
        if not self.data:
            return
            
        fields = list(self.data[0].keys()) if self.data else []
        if not fields:
            return
            
        def handle_config_result(result):
            if result:
                self.x_field, self.y_fields, self.group_field = result
                # 为了兼容现有代码，如果只有一个Y字段，设置y_field
                self.y_field = self.y_fields[0] if self.y_fields else None
                
                # 保存配置到当前图表类型
                self.chart_configs[self.chart_type] = {
                    "x_field": self.x_field,
                    "y_fields": self.y_fields,
                    "group_field": self.group_field
                }
                
                self._render_chart(self.chart_type, self.x_field, self.y_fields, self.group_field)
                # 强制刷新显示
                self.refresh()
        
        # 获取当前图表类型的配置
        current_config = self.chart_configs.get(self.chart_type, {"x_field": None, "y_fields": []})
        modal = FieldConfigModal(fields, self.chart_type, current_config)
        self.app.push_screen(modal, handle_config_result)
    
    def _render_chart(self, chart_type: str, x_field: str, y_fields: List[str], group_field: str = None):
        """渲染图表"""
        # 隐藏字段配置选择器
        field_config = self.query_one("#field-config-selector", FieldConfigSelector)
        field_config.add_class("hidden")
        
        # 更新图表
        chart_container = self.query_one("#chart-container", ChartContainer)
        chart_container.update_chart(chart_type, self.data, x_field, y_fields, group_field)
        self.chart_configured = True
    

    
    def on_chart_type_selector_chart_type_changed(self, message: ChartTypeSelector.ChartTypeChanged):
        """处理图表类型变化"""
        self.chart_type = message.chart_type
        
        # 获取新图表类型的配置
        current_config = self.chart_configs.get(self.chart_type, {"x_field": None, "y_fields": []})
        
        # 如果新图表类型有配置，使用该配置
        if current_config["x_field"] and current_config["y_fields"]:
            self.x_field = current_config["x_field"]
            self.y_fields = current_config["y_fields"]
            self.y_field = self.y_fields[0] if self.y_fields else None
            self._render_chart(self.chart_type, self.x_field, self.y_fields, self.group_field)
        else:
            # 如果新图表类型没有配置，重新进行字段自动选择
            if self.data:
                self._auto_select_fields()
                if self.x_field and self.y_fields:
                    self._render_chart(self.chart_type, self.x_field, self.y_fields, self.group_field)
                else:
                    # 显示字段配置界面
                    self._show_field_config()
    
    def on_field_config_selector_field_config_changed(self, message: FieldConfigSelector.FieldConfigChanged):
        """处理字段配置变化"""
        self._render_chart(self.chart_type, message.x_field, message.y_fields, getattr(message, 'group_field', None))
        
        # 隐藏字段配置
        field_config = self.query_one("#field-config-selector", FieldConfigSelector)
        field_config.add_class("hidden")
    
    def action_refresh_chart(self):
        """刷新图表"""
        if self.x_field and (self.y_field or self.y_fields) and self.data:
            y_fields_to_use = self.y_fields if self.y_fields else [self.y_field] if self.y_field else []
            if y_fields_to_use:
                self._render_chart(self.chart_type, self.x_field, y_fields_to_use)