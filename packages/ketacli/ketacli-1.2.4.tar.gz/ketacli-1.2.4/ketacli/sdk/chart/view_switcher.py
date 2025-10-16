"""视图切换组件模块

提供表格和图表视图之间的切换功能。
"""

from typing import Dict, List, Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button, TabbedContent, TabPane
from textual.reactive import reactive
from textual.message import Message
from textual.binding import Binding

from .chart_components import ChartVisualizationWidget


class ViewSwitcher(Static):
    """视图切换器组件"""
    
    current_view = reactive("table")  # "table", "line_chart" 或 "bar_chart"
    
    BINDINGS = []
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
    
    def compose(self) -> ComposeResult:
        """构建视图切换器UI"""
        with TabbedContent(id="view-tabs", initial="table-tab"):
            with TabPane("表格", id="table-tab"):
                # 这里将放置表格组件的占位符
                yield Static("", id="table-content-placeholder")
            
            with TabPane("折线图", id="line-chart-tab"):
                yield ChartVisualizationWidget(id="line-chart-visualization", chart_type="line")
                
            with TabPane("柱形图", id="bar-chart-tab"):
                yield ChartVisualizationWidget(id="bar-chart-visualization", chart_type="bar")
    
    def update_data(self, data: List[Dict]):
        """更新数据到所有视图"""
        self.data = data
        
        # 更新折线图数据
        line_chart_widget = self.query_one("#line-chart-visualization", ChartVisualizationWidget)
        line_chart_widget.update_data(data)
        
        # 更新柱形图数据
        bar_chart_widget = self.query_one("#bar-chart-visualization", ChartVisualizationWidget)
        bar_chart_widget.update_data(data)
        
        # 发送数据更新消息给父组件，用于更新表格
        self.post_message(self.DataUpdated(data))
    
    def set_table_widget(self, table_widget):
        """设置表格组件"""
        try:
            table_placeholder = self.query_one("#table-content-placeholder")
            table_placeholder.remove()
        except:
            pass  # 占位符可能已经被移除
        
        table_tab = self.query_one("#table-tab", TabPane)
        table_tab.mount(table_widget)
    

    
    def action_switch_to_table(self):
        """切换到表格视图"""
        tabs = self.query_one("#view-tabs", TabbedContent)
        tabs.active = "table-tab"
        self.current_view = "table"
    
    def action_switch_to_line_chart(self):
        """切换到折线图"""
        tabs = self.query_one("#view-tabs", TabbedContent)
        tabs.active = "line-chart-tab"
        self.current_view = "line_chart"
        
    def action_switch_to_bar_chart(self):
        """切换到柱形图"""
        tabs = self.query_one("#view-tabs", TabbedContent)
        tabs.active = "bar-chart-tab"
        self.current_view = "bar_chart"
    
    class DataUpdated(Message):
        """数据更新消息"""
        def __init__(self, data: List[Dict]):
            super().__init__()
            self.data = data


class EnhancedSearchResultWidget(Static):
    """增强的搜索结果组件，集成了视图切换功能"""
    
    BINDINGS = [
        Binding("ctrl+c", "copy_cell", "复制单元格"),
        Binding("ctrl+shift+c", "copy_row", "复制整行JSON"),
        Binding("shift+left", "page_up", "上一页"),
        Binding("shift+right", "page_down", "下一页"),
        Binding("ctrl+f", "open_field_config", "配置图表字段"),
    ]
    
    def __init__(self, original_search_widget, **kwargs):
        super().__init__(**kwargs)
        self.original_search_widget = original_search_widget
        self.data = []
    
    def compose(self) -> ComposeResult:
        """构建增强的搜索结果UI"""
        yield ViewSwitcher(id="view-switcher")
    
    def on_mount(self):
        """组件挂载时设置表格组件"""
        view_switcher = self.query_one("#view-switcher", ViewSwitcher)
        view_switcher.set_table_widget(self.original_search_widget)
    
    def initialize_table(self, page_size=10, limit=500, overflow="ellipsis"):
        """初始化表格"""
        self.original_search_widget.initialize_table(page_size, limit, overflow)
    
    async def search_async(self, spl_text, start_time=None, end_time=None, limit=100):
        """异步执行搜索"""
        # 调用原始搜索组件的异步搜索方法
        await self.original_search_widget.search_async(spl_text, start_time, end_time, limit)
        
        # 获取搜索结果数据并更新视图切换器
        if hasattr(self.original_search_widget, 'data') and self.original_search_widget.data:
            self.data = self.original_search_widget.data
            view_switcher = self.query_one("#view-switcher", ViewSwitcher)
            view_switcher.update_data(self.data)
    
    def search(self, spl_text, start_time=None, end_time=None):
        """执行搜索 - 兼容性方法"""
        # 调用原始搜索组件的搜索方法
        self.original_search_widget.search(spl_text, start_time, end_time)
        
        # 获取搜索结果数据并更新视图切换器
        if hasattr(self.original_search_widget, 'data') and self.original_search_widget.data:
            self.data = self.original_search_widget.data
            view_switcher = self.query_one("#view-switcher", ViewSwitcher)
            view_switcher.update_data(self.data)
    
    def filter_switch(self):
        """切换过滤功能"""
        self.original_search_widget.filter_switch()
    
    def navigate(self, direction):
        """导航"""
        self.original_search_widget.navigate(direction)
    
    def action_copy_cell(self):
        """复制单元格"""
        self.original_search_widget.action_copy_cell()
    
    def action_copy_row(self):
        """复制整行"""
        self.original_search_widget.action_copy_row()
    
    def action_page_up(self):
        """上一页"""
        self.original_search_widget.action_page_up()
    
    def action_page_down(self):
        """下一页"""
        self.original_search_widget.action_page_down()
    

    
    def action_switch_to_table(self):
        """切换到表格视图"""
        view_switcher = self.query_one("#view-switcher", ViewSwitcher)
        view_switcher.action_switch_to_table()
    
    def action_switch_to_line_chart(self):
        """切换到折线图"""
        view_switcher = self.query_one("#view-switcher", ViewSwitcher)
        view_switcher.action_switch_to_line_chart()
        
    def action_switch_to_bar_chart(self):
        """切换到柱形图"""
        view_switcher = self.query_one("#view-switcher", ViewSwitcher)
        view_switcher.action_switch_to_bar_chart()
    
    def action_open_field_config(self):
        """打开字段配置弹窗"""
        view_switcher = self.query_one("#view-switcher", ViewSwitcher)
        
        # 获取当前活跃的标签页
        try:
            tabbed_content = view_switcher.query_one("#view-tabs", TabbedContent)
            active_tab = tabbed_content.active
            
            if active_tab == "table-tab":
                # 如果在表格视图，提示用户切换到图表视图
                # 这里可以显示一个提示消息，或者什么都不做
                return
            elif active_tab == "line-chart-tab":
                chart_widget = view_switcher.query_one("#line-chart-visualization")
                chart_widget.action_open_field_config()
            elif active_tab == "bar-chart-tab":
                chart_widget = view_switcher.query_one("#bar-chart-visualization")
                chart_widget.action_open_field_config()
        except Exception:
            pass  # 如果组件不存在或出错，忽略
    
    def on_view_switcher_data_updated(self, message: ViewSwitcher.DataUpdated):
        """处理数据更新消息"""
        # 这里可以添加额外的数据处理逻辑
        pass