import re
import pyperclip
import json
import asyncio
from datetime import datetime, timedelta, timezone
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input, Static, DataTable, Footer, TextArea, Button, ListView, ListItem, Label, Select
from textual.binding import Binding
from textual.message import Message
from textual.coordinate import Coordinate
from rich.text import Text
from rich.console import Console
from rich.syntax import Syntax

from ketacli.sdk.chart.chart_utils.spl_textarea import SPLTextArea, SearchRequested
from ketacli.sdk.base.search import search_spl
from ketacli.sdk.chart.chart_utils.search_history import SearchHistoryManager
from ketacli.sdk.chart.view_switcher import EnhancedSearchResultWidget
from ketacli.sdk.ai.functions.search_functions import validate_spl_value_quotes


def format_time_field(field_name, value):
    """检测并格式化_time字段为+8时区"""
    if field_name == '_time' and value is not None:
        try:
            # 处理不同类型的时间值
            if isinstance(value, (int, float)):
                # 判断是毫秒还是秒时间戳
                if value > 1000000000000:  # 毫秒时间戳
                    dt = datetime.fromtimestamp(value / 1000, tz=timezone.utc)
                else:  # 秒时间戳
                    dt = datetime.fromtimestamp(value, tz=timezone.utc)
                
                # 转换为+8时区
                china_tz = timezone(timedelta(hours=8))
                dt_china = dt.astimezone(china_tz)
                return dt_china.strftime('%Y-%m-%d %H:%M:%S')
            
            elif isinstance(value, str):
                # 尝试解析时间字符串
                try:
                    # 处理ISO格式时间字符串
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    # 转换为+8时区
                    china_tz = timezone(timedelta(hours=8))
                    dt_china = dt.astimezone(china_tz)
                    return dt_china.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # 如果解析失败，返回原始值
                    return str(value)
        except Exception:
            # 如果格式化失败，返回原始值
            return str(value)
    
    # 非_time字段或处理失败，返回原始值
    return str(value)


def detect_field_type(value):
    """检测字段值的数据类型"""
    if value is None or value == "":
        return "null"
    
    # 转换为字符串进行检测
    str_value = str(value).strip()
    
    # 检测布尔值
    if str_value.lower() in ['true', 'false', 'yes', 'no', '1', '0']:
        return "boolean"
    
    # 检测数字（整数）
    try:
        int(str_value)
        return "integer"
    except ValueError:
        pass
    
    # 检测数字（浮点数）
    try:
        float(str_value)
        return "float"
    except ValueError:
        pass
    
    # 检测日期时间格式
    import re
    datetime_patterns = [
        r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}',  # YYYY-MM-DD HH:MM:SS
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO format
        r'\d{4}/\d{2}/\d{2}\s\d{2}:\d{2}:\d{2}',  # YYYY/MM/DD HH:MM:SS
    ]
    
    for pattern in datetime_patterns:
        if re.match(pattern, str_value):
            return "datetime"
    
    # 检测IP地址
    ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
    if re.match(ip_pattern, str_value):
        return "ip"
    
    # 检测URL
    url_pattern = r'^https?://'
    if re.match(url_pattern, str_value):
        return "url"
    
    # 默认为字符串
    return "string"


def get_color_for_type(field_type):
    """根据字段类型返回对应的颜色"""
    color_map = {
        "integer": "bright_blue",      # 整数 - 亮蓝色
        "float": "blue",              # 浮点数 - 蓝色
        "boolean": "bright_green",    # 布尔值 - 亮绿色
        "datetime": "magenta",        # 日期时间 - 洋红色
        "ip": "cyan",                 # IP地址 - 青色
        "url": "bright_cyan",         # URL - 亮青色
        "string": "white",            # 字符串 - 白色（默认）
        "null": "bright_black",       # 空值 - 亮黑色（灰色）
    }
    return color_map.get(field_type, "white")



class RealDataSource:
    """真实数据源，使用实际的搜索API"""
    
    def __init__(self):
        self.history_manager = SearchHistoryManager()
        
    def get_search_history(self):
        """获取搜索历史数据"""
        return self.history_manager.get_search_history()
        
    def add_search_to_history(self, query: str):
        """添加搜索查询到历史记录"""
        return self.history_manager.add_search(query)
    
    def search_data(self, spl_query, start=None, end=None, limit=100):
        """使用真实的搜索API进行数据搜索"""
        try:
            # 运行前进行 SPL 值引号校验（字段值必须用双引号）
            validate_spl_value_quotes(spl_query)
            # 调用真实的搜索API
            result = search_spl(spl_query, start=start, end=end, limit=limit)
            
            # 处理搜索结果
            if result and isinstance(result, dict):
                # 如果结果包含rows字段，说明是表格数据
                if 'rows' in result:
                    rows = result['rows']
                    fields = result.get('fields', [])
                    
                    # 从fields中提取字段名
                    headers = []
                    if fields and len(fields) > 0:
                        headers = [field.get('name', f'column_{i}') for i, field in enumerate(fields)]
                    
                    # 转换为字典列表格式
                    formatted_results = []
                    for row in rows:
                        if headers and len(headers) > 0:
                            # 使用从fields提取的字段名作为键名
                            row_dict = {}
                            for i, header in enumerate(headers):
                                if i < len(row):
                                    row_dict[header] = row[i]
                                else:
                                    row_dict[header] = ""
                            formatted_results.append(row_dict)
                        else:
                            # 没有fields信息，使用索引作为键名
                            row_dict = {}
                            for i, value in enumerate(row):
                                row_dict[f"column_{i}"] = value
                            formatted_results.append(row_dict)
                    
                    return formatted_results
                
                # 如果结果是其他格式，尝试直接返回
                elif isinstance(result, list):
                    return result
                else:
                    # 单个结果，包装成列表
                    return [result]
            
            # 如果没有结果，生成测试数据用于验证分页功能
            test_data = []
            for i in range(25):  # 生成25条测试数据
                test_data.append({
                    "时间": f"2024-01-{i+1:02d} 10:00:00",
                    "主机": f"server-{i+1:03d}",
                    "状态": "正常" if i % 3 == 0 else "警告" if i % 3 == 1 else "错误",
                    "CPU使用率": f"{(i * 3.7) % 100:.1f}%",
                    "内存使用率": f"{(i * 2.3) % 100:.1f}%",
                    "消息": f"测试消息 {i+1} - {spl_query[:20]}..."
                })
            return test_data
            
        except Exception as e:
            # 搜索出错时，返回错误信息
            return [{
                "error": "搜索失败",
                "message": str(e),
                "query": spl_query,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }]


class TimeRangeSelector(Static):
    """时间范围选择器组件"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_range = "前60分钟"
        
    def compose(self) -> ComposeResult:
        """构建时间选择器UI"""
        time_options = [
            ("前5分钟", "前5分钟"),
            ("前15分钟", "前15分钟"),
            ("前30分钟", "前30分钟"),
            ("前60分钟", "前60分钟"),
            ("前3小时", "前3小时"),
            ("前6小时", "前6小时"),
            ("前12小时", "前12小时"),
            ("前24小时", "前24小时"),
            ("过去3天", "过去3天"),
            ("过去7天", "过去7天"),
            ("过去30天", "过去30天"),
        ]
        yield Select(time_options, value="前60分钟", id="time-range-select")
        
    def on_select_changed(self, event: Select.Changed) -> None:
        """处理时间范围选择变化"""
        if event.select.id == "time-range-select":
            self.selected_range = event.value
            # 发送时间范围变化消息
            self.post_message(self.TimeRangeChanged(event.value))
            
    class TimeRangeChanged(Message):
        """时间范围变化消息"""
        def __init__(self, time_range: str):
            super().__init__()
            self.time_range = time_range
            
    def get_time_range(self):
        """获取当前选择的时间范围"""
        try:
            select = self.query_one("#time-range-select", Select)
            selected_value = select.value
            with open("time_range.txt", "w") as f:
                f.write(selected_value)
            if selected_value:
                # 解析时间范围值，计算开始和结束时间
                end_time = datetime.now()
                
                time_deltas = {
                    "前5分钟": timedelta(minutes=5),
                    "前15分钟": timedelta(minutes=15),
                    "前30分钟": timedelta(minutes=30),
                    "前60分钟": timedelta(hours=1),
                    "前3小时": timedelta(hours=3),
                    "前6小时": timedelta(hours=6),
                    "前12小时": timedelta(hours=12),
                    "前24小时": timedelta(days=1),
                    "过去3天": timedelta(days=3),
                    "过去7天": timedelta(days=7),
                    "过去30天": timedelta(days=30),
                }
                
                delta = time_deltas.get(selected_value, timedelta(hours=1))
                start_time = end_time - delta
                
                # 返回时间戳格式
                return int(start_time.timestamp()*1000), int(end_time.timestamp()*1000)
            else:
                # 默认返回前60分钟
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=1)
                return int(start_time.timestamp()*1000), int(end_time.timestamp()*1000)
                
        except Exception as e:
            # 出错时返回默认时间范围（前60分钟）
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            return int(start_time.timestamp()*1000), int(end_time.timestamp()*1000)
            
    def get_time_range_params(self):
        """根据选择的时间范围返回开始和结束时间参数"""
        now = datetime.now()
        
        time_deltas = {
            "前5分钟": timedelta(minutes=5),
            "前15分钟": timedelta(minutes=15),
            "前30分钟": timedelta(minutes=30),
            "前60分钟": timedelta(hours=1),
            "前3小时": timedelta(hours=3),
            "前6小时": timedelta(hours=6),
            "前12小时": timedelta(hours=12),
            "前24小时": timedelta(days=1),
            "过去3天": timedelta(days=3),
            "过去7天": timedelta(days=7),
            "过去30天": timedelta(days=30),
        }
        
        delta = time_deltas.get(self.selected_range, timedelta(hours=1))
        start_time = now - delta
        
        return {
            'start': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end': now.strftime('%Y-%m-%d %H:%M:%S')
        }


class SearchHistoryWidget(Static):
    """搜索历史显示组件 - 使用纯Textual DataTable"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_source = RealDataSource()
        self.visible = False
        
    def compose(self) -> ComposeResult:
        yield Static("搜索历史", classes="history-title")
        yield DataTable(id="history-table")
        
    def on_mount(self) -> None:
        """组件挂载时初始化"""
        self.refresh_history()
        
    def refresh_history(self):
        """刷新搜索历史"""
        if self.visible:
            table = self.query_one("#history-table", DataTable)
            table.clear(columns=True)
            
            # 添加列（SPL搜索语句在前，时间在后）
            table.add_column("搜索语句", key="query")
            table.add_column("时间", key="timestamp", width=20)
            
            # 获取历史数据并添加到表格
            history_data = self.data_source.get_search_history()
            for item in history_data:
                # 使用rich.syntax为SPL语句添加语法高亮
                try:
                    syntax = Syntax(item["query"], "sql", theme="github-dark", line_numbers=False, word_wrap=True)
                    console = Console()
                    with console.capture() as capture:
                        console.print(syntax)
                    query_text = Text.from_ansi(capture.get())
                except Exception:
                    # 如果语法高亮失败，回退到普通文本
                    query_text = Text(item["query"])
                    query_text.no_wrap = False
                table.add_row(query_text, item["timestamp"], key=str(item["id"]), height=None)
                
    def get_current_selection(self):
        """获取当前选中的历史记录"""
        table = self.query_one("#history-table", DataTable)
        if table.cursor_coordinate is not None:
            row_key = table.get_row_at(table.cursor_coordinate.row)
            if row_key and len(row_key) > 0:
                return str(row_key[0])  # 返回查询语句（现在在第一列）
        return ""
        
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """处理历史记录表格行选择事件"""
        # 当双击或回车选择行时，将查询语句放到搜索框中
        selected_query = self.get_current_selection()
        if selected_query:
            # 发送消息给父应用，通知选择了历史记录
            self.post_message(self.HistorySelected(selected_query))
            
    def on_key(self, event) -> None:
        """处理按键事件"""
        if event.key == "enter":
            # 按回车键时选择当前行
            selected_query = self.get_current_selection()
            if selected_query:
                self.post_message(self.HistorySelected(selected_query))
                event.prevent_default()
                event.stop()
            
    class HistorySelected(Message):
        """历史记录选择消息"""
        def __init__(self, query: str):
            super().__init__()
            self.query = query


class SearchResultWidget(Static):
    """搜索结果显示组件 - 使用纯Textual DataTable"""
    
    # 添加按键绑定
    BINDINGS = [
        Binding("ctrl+c", "copy_cell", "复制单元格"),
        Binding("ctrl+shift+c", "copy_row", "复制整行JSON"),
        Binding("shift+left", "page_up", "上一页"),
        Binding("shift+right", "page_down", "下一页"),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_source = RealDataSource()
        self.search_visible = True
        self.current_page = 0
        self.page_size = 10
        self.total_results = []
        self.columns = []  # 存储列名
        self.data = []  # 添加data属性供图表组件使用
        self.auto_adjust_page_size = True  # 是否自动调整页面大小
        
    def compose(self) -> ComposeResult:
        yield Static("准备搜索...", id="search-status")
        yield DataTable(id="results-table", zebra_stripes=True)
        
    def on_mount(self) -> None:
        """组件挂载时计算初始页面大小"""
        if self.auto_adjust_page_size:
            # 延迟计算，确保布局完成
            self.call_after_refresh(self._calculate_page_size)
            
    def on_resize(self) -> None:
        """窗口大小变化时重新计算页面大小"""
        if self.auto_adjust_page_size:
            old_page_size = self.page_size
            # 延迟计算，确保布局完成
            self.call_after_refresh(self._delayed_resize_calculation, old_page_size)
            
    def _delayed_resize_calculation(self, old_page_size):
        """延迟的窗口大小变化处理"""
        self._calculate_page_size()
        # 如果页面大小发生变化，刷新当前页面
        if old_page_size != self.page_size and self.total_results:
            self._refresh_current_page()
                
    def _calculate_page_size(self):
        """根据屏幕高度动态计算合适的页面大小"""
        try:
            import os
            
            # 尝试多种方法获取终端尺寸
            available_height = 0
            
            # 方法1: 使用os.get_terminal_size()
            try:
                terminal_size = os.get_terminal_size()
                available_height = terminal_size.lines
                self.notify(f"终端实际高度: {available_height}")
            except:
                pass
            
            # 方法2: 如果方法1失败，尝试从应用程序获取
            if available_height <= 0:
                try:
                    app_size = self.app.size
                    available_height = app_size.height if app_size else 0
                    self.notify(f"应用程序高度: {available_height}")
                except:
                    pass
            
            # 方法3: 如果前面都失败，尝试从组件获取
            if available_height <= 0:
                available_height = self.size.height
                self.notify(f"组件高度: {available_height}")
            
            # 如果所有方法都失败，使用默认值
            if available_height <= 0:
                available_height = 24  # 默认终端高度
                self.notify("使用默认高度: 24")
            
            # 预留空间：标题栏(3行) + 输入区域(10行) + 状态栏(1行) + 边距(4行)
            reserved_height = 18
            
            # 每行数据大小：根据CSS中的min-height设置，每行2个字符高度
            row_height = 2
            
            # 计算可显示的行数
            usable_height = max(available_height - reserved_height, row_height * 5)  # 至少保证5行的空间
            calculated_page_size = max(usable_height // row_height, 5)  # 最少显示5行
            
            # 限制最大页面大小，避免过大
            self.page_size = min(calculated_page_size, 50)
            
            self.notify(f"终端高度: {available_height}, 可用高度: {usable_height}, 计算页面大小: {self.page_size}")
            
        except Exception as e:
            # 如果计算失败，使用默认值
            self.page_size = 10
            self.notify(f"页面大小计算失败，使用默认值: {e}", severity="error")
        
    def initialize_table(self, page_size=None, limit=500, overflow="ellipsis"):
        """初始化搜索结果表格"""
        if page_size is not None:
            self.page_size = page_size
            self.auto_adjust_page_size = False  # 手动设置页面大小时禁用自动调整
        elif self.auto_adjust_page_size:
            self._calculate_page_size()
        
    async def search_async(self, spl_text, start_time=None, end_time=None, limit=100):
        """异步执行搜索"""
        status = self.query_one("#search-status", Static)
        table = self.query_one("#results-table", DataTable)
        status.update("搜索中...")
        
        try:
            # 保存搜索历史（在执行搜索前）
            if spl_text and spl_text.strip():
                self.data_source.add_search_to_history(spl_text.strip())
            
            # 在后台线程中执行搜索操作，避免阻塞UI
            search_results = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.data_source.search_data(spl_text, start=start_time, end=end_time, limit=limit)
            )
            
            self.total_results = search_results if search_results else []
            self.data = self.total_results  # 更新data属性供图表组件使用
            
            # 清空现有表格
            table.clear(columns=True)
            
            if self.total_results and len(self.total_results) > 0:
                # 获取列标题
                if isinstance(self.total_results[0], dict):
                    self.columns = list(self.total_results[0].keys())  # 保存列名
                    for col in self.columns:
                        table.add_column(str(col), key=str(col))
                    
                    # 添加数据行（分页显示）
                    start_idx = self.current_page * self.page_size
                    end_idx = min(start_idx + self.page_size, len(self.total_results))
                    
                    for i in range(start_idx, end_idx):
                        row_data = self.total_results[i]
                        # 为每个单元格创建带颜色的Text对象
                        colored_cells = []
                        for col in self.columns:
                            value = row_data.get(col, "")
                            # 检测并格式化_time字段
                            str_value = format_time_field(col, value)
                            field_type = detect_field_type(value)
                            color = get_color_for_type(field_type)
                            colored_text = Text(str_value, style=color)
                            colored_cells.append(colored_text)
                        table.add_row(*colored_cells, key=str(i))
                    
                    current_page_count = min(self.page_size, len(self.total_results) - self.current_page * self.page_size)
                    status.update(f"搜索完成 - 找到 {len(self.total_results)} 条结果 (第 {self.current_page + 1} 页，当前页 {current_page_count} 条)")
                else:
                    status.update("搜索完成 - 数据格式错误")
            else:
                status.update("搜索完成 - 未找到结果")
                
        except Exception as e:
            status.update(f"搜索错误: {e}")
    
    def search(self, spl_text, start_time=None, end_time=None):
        """执行搜索 - 兼容性方法"""
        # 创建异步任务
        asyncio.create_task(self.search_async(spl_text, start_time, end_time))
            
    def filter_switch(self):
        """切换过滤功能"""
        self.search_visible = not self.search_visible
        status = self.query_one("#search-status", Static)
        if self.search_visible:
            status.update("过滤功能已开启")
        else:
            status.update("过滤功能已关闭")
            
    def navigate(self, direction):
        """导航操作"""
        table = self.query_one("#results-table", DataTable)
        
        if direction == "up":
            if table.cursor_coordinate.row > 0:
                table.cursor_coordinate = Coordinate(table.cursor_coordinate.row - 1, table.cursor_coordinate.column)
        elif direction == "down":
            if table.cursor_coordinate.row < table.row_count - 1:
                table.cursor_coordinate = Coordinate(table.cursor_coordinate.row + 1, table.cursor_coordinate.column)
        elif direction == "page_up":
            if self.current_page > 0:
                self.current_page -= 1
                self._refresh_current_page()
        elif direction == "page_down":
            max_pages = (len(self.total_results) - 1) // self.page_size
            if self.current_page < max_pages:
                self.current_page += 1
                self._refresh_current_page()
                
    def _refresh_current_page(self):
        """刷新当前页面数据"""
        if not self.total_results:
            return
            
        table = self.query_one("#results-table", DataTable)
        status = self.query_one("#search-status", Static)
        
        # 清空表格数据和列
        table.clear(columns=True)
        
        # 重新添加列和当前页数据
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.total_results))
        
        if isinstance(self.total_results[0], dict):
            # 重新添加列
            for col in self.columns:
                table.add_column(str(col), key=str(col))
            
            # 添加当前页的数据行
            for i in range(start_idx, end_idx):
                row_data = self.total_results[i]
                # 为每个单元格创建带颜色的Text对象
                colored_cells = []
                for col in self.columns:
                    value = row_data.get(col, "")
                    # 检测并格式化_time字段
                    str_value = format_time_field(col, value)
                    field_type = detect_field_type(value)
                    color = get_color_for_type(field_type)
                    colored_text = Text(str_value, style=color)
                    colored_cells.append(colored_text)
                table.add_row(*colored_cells, key=str(i))
        
        # 计算总页数和当前页面条数
        total_pages = (len(self.total_results) - 1) // self.page_size + 1
        current_page_count = end_idx - start_idx
        status.update(f"搜索完成 - 找到 {len(self.total_results)} 条结果 (第 {self.current_page + 1}/{total_pages} 页，当前页 {current_page_count} 条)")
    
    def action_copy_cell(self) -> None:
        """复制当前选中单元格的值"""
        table = self.query_one("#results-table", DataTable)
        
        if not self.total_results or not self.columns:
            self.app.notify("没有可复制的数据")
            return
            
        try:
            # 获取当前光标位置
            cursor_row = table.cursor_coordinate.row
            cursor_col = table.cursor_coordinate.column
            
            # 计算实际数据索引
            actual_row_idx = self.current_page * self.page_size + cursor_row
            
            if actual_row_idx >= len(self.total_results):
                self.app.notify("无效的行索引")
                return
                
            if cursor_col >= len(self.columns):
                self.app.notify("无效的列索引")
                return
            
            # 获取单元格值
            row_data = self.total_results[actual_row_idx]
            column_name = self.columns[cursor_col]
            cell_value = str(row_data.get(column_name, ""))
            
            # 复制到剪贴板
            pyperclip.copy(cell_value)
            self.app.notify(f"已复制单元格值: {cell_value[:50]}{'...' if len(cell_value) > 50 else ''}")
            
        except Exception as e:
            self.app.notify(f"复制失败: {str(e)}")
    
    def action_copy_row(self) -> None:
        """复制当前选中行的数据为JSON格式"""
        table = self.query_one("#results-table", DataTable)
        
        if not self.total_results or not self.columns:
            self.app.notify("没有可复制的数据")
            return
            
        try:
            # 获取当前光标位置
            cursor_row = table.cursor_coordinate.row
            
            # 计算实际数据索引
            actual_row_idx = self.current_page * self.page_size + cursor_row
            
            if actual_row_idx >= len(self.total_results):
                self.app.notify("无效的行索引")
                return
            
            # 获取整行数据
            row_data = self.total_results[actual_row_idx]
            
            # 转换为JSON格式
            json_data = json.dumps(row_data, ensure_ascii=False, indent=2)
            
            # 复制到剪贴板
            pyperclip.copy(json_data)
            self.app.notify(f"已复制整行JSON数据 (行 {actual_row_idx + 1})")
            
        except Exception as e:
            self.app.notify(f"复制失败: {str(e)}")
    
    def action_page_up(self) -> None:
        """上一页"""
        self.navigate("page_up")
    
    def action_page_down(self) -> None:
        """下一页"""
        self.navigate("page_down")


# AutoCompleteList类已移除，使用Textual内置的suggester功能


# SPLTextArea类已移动到base模块中


class InteractiveSearch(App):
    """基于Textual的交互式搜索应用 - 纯Textual实现"""
    
    # 添加搜索锁，防止多次并发搜索
    _search_in_progress = False
    
    CSS = """
    .spl-input {
        height: 10;
        border: solid $primary;
        margin: 1;
        background: $surface;
        width: 1fr;
        min-height: 5;
    }
    
    .search-result {
        height: 1fr;
        border: solid $secondary;
        margin: 1;
        width: 100%;
    }
    
    .search-history {
        width: 30%;
        border: solid $accent;
        margin: 1;
    }
    
    .main-content {
        width: 1fr;
    }
    
    .hidden {
        display: none;
    }
    
    .history-title {
        text-align: center;
        background: $accent;
        color: $text;
        height: 1;
    }

    /* 搜索标题样式 */
    #search-title {
        text-align: center;
        color: $text;
        height: 3;
        text-style: bold;
        padding: 0;
        margin-bottom: 0;
        border: solid $accent;
    }
    
    /* 容器样式 */
    #search-container {
        width: 100%;
    }
    
    #input-row {
        width: 100%;
        height: auto;
    }
    
    #results-container {
        width: 100%;
    }
    
    #main-container {
        width: 100%;
    }
    
    .input-wrapper {
        width: 100%;
        position: relative;
    }

    /* 建议显示样式 */
    #suggestion-display {
        height: 1;
        width: 100%;
        background: $surface;
        color: $text-muted;
        margin: 0 1;
    }

    /* 按钮列样式 */
    .button-column {
        width: 20;
        height: 13;
        margin-left: 1;
        align: center middle;
        padding: 0;
    }
    
    /* 时间选择器样式 */
    #time-range-selector {
        width: 100%;
        height: 3;
        margin-bottom: 0;
        margin-top: 0;
        padding-bottom: 0;
    }
    
    #time-range-select {
        height: 3;
        max-height: 3;
        min-height: 3;
        width: 100%;
    }
    
    /* 搜索按钮样式 */
    Button {
        height: 3;
        max-height: 3;
        min-height: 3;
        padding: 0 0;
    }
    
    #search-button {
        width: 95%;
        height: 3;
        max-height: 3;
        min-height: 3;
        margin-top: 0;
        margin-left: 1;
        padding: 0 0;
    }
    
    Button.search-button {
        width: 100%;
        height: 3;
        max-height: 3;
        min-height: 3;
        margin-top: 0;
        padding: 0 0;
    }
    
    /* 搜索条数限制下拉选择器样式 */
    .limit-select {
        width: 100%;
        height: 3;
        max-height: 3;
        min-height: 3;
        margin-top: 0;
        margin-bottom: 0;
        padding: 0 0;
    }
    
    /* Input组件的建议样式 */
    Input {
        border: solid $primary;
    }
    
    Input:focus {
        border: solid $accent;
    }
    
    /* TextArea 特定样式 */
    TextArea {
        background: $surface;
        color: $text;
        width: 100%;
    }
    
    TextArea:focus {
        border: solid $accent;
    }
    
    /* DataTable 样式 */
    DataTable {
        background: $surface;
        width: 100%;
        border: solid $secondary;
    }
    
    DataTable > .datatable--header {
        background: $primary;
        color: $text;
        border-bottom: solid $secondary;
    }
    
    DataTable > .datatable--cursor {
        background: #4a90e2;
        color: white;
    }
    
    DataTable > .datatable--cell {
        height: auto;
        min-height: 2;
        padding: 1;
        border-right: solid $secondary;
        border-bottom: solid $secondary;
    }
    
    DataTable > .datatable--row {
        min-height: 3;
        height: auto;
    }
    
    /* 历史记录表格特定样式 */
    #history-table {
        height: 1fr;
        border: solid $secondary;
    }
    
    #history-table .datatable--cell {
        height: auto;
        min-height: 2;
        padding: 1;
        border-right: solid $secondary;
        border-bottom: solid $secondary;
    }
    
    #history-table .datatable--row {
        min-height: 3;
        height: auto;
    }
    
    /* 搜索结果表格特定样式 */
    #results-table {
        border: solid $secondary;
    }
    
    #results-table .datatable--cell {
        height: auto;
        min-height: 2;
        padding: 1;
        border-right: solid $secondary;
        border-bottom: solid $secondary;
    }
    
    #results-table .datatable--row {
        min-height: 3;
        height: auto;
    }
    
    /* 图表组件样式 */
    .chart-content {
        width: 100%;
        height: 1fr;
        border: solid $secondary;
        margin: 1;
    }
    
    .chart-widget {
        width: 100%;
        height: 100%;
        min-height: 20;
    }
    
    .chart-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    
    .chart-placeholder {
        text-align: center;
        color: $text-muted;
        margin: 2;
    }
    
    .chart-label {
        width: 15;
        text-align: right;
        margin-right: 1;
    }
    
    .chart-type-select {
        width: 20;
    }
    
    .config-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .field-label {
        width: 10;
        text-align: right;
        margin-right: 1;
    }
    
    .field-select {
        width: 20;
    }
    
    .y-field-select {
        width: 60;
    }
    
    SelectionList.y-field-select {
        width: 60;
        min-width: 60;
    }
    
    /* 标签页样式 */
    TabbedContent {
        height: 1fr;
    }
    
    TabPane {
        height: 1fr;
    }
    
    .hidden {
        display: none;
    }
    
    /* 弹窗样式 */
    ModalScreen {
        align: center middle;
    }
    
    .config-modal {
        align: center middle;
        width: 90;
        height: 35;
        background: $surface;
        border: thick $primary;
        border-title-align: center;
    }
    
    .config-content {
        width: 100%;
        height: 100%;
        padding: 2;
    }
    
    .modal-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 2;
        height: 1;
    }
    
    .field-row {
        width: 100%;
        height: auto;
        min-height: 3;
        margin-bottom: 1;
        align: left top;
    }
    
    .field-row .field-label {
        width: 12;
        text-align: right;
        margin-right: 2;
    }
    
    .field-row .field-select {
        width: 1fr;
    }
    
    .field-row .y-field-checkboxes {
        width: 1fr;
        height: auto;
        max-height: 12;
        min-height: 6;
        overflow-y: auto;
        border: solid $secondary;
        padding: 1;
    }
    
    .y-field-checkbox {
        margin-bottom: 0;
        height: auto;
        min-height: 1;
    }
    
    .button-row {
        width: 100%;
        height: auto;
        margin-top: 0;
        align: center middle;
    }
    
    .button-row Button {
        margin: 0 1;
        width: 15;
        min-width: 15;
    }
    
    .config-hint {
        text-align: center;
        color: $text-muted;
        text-style: italic;
        margin: 2;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "退出"),
        Binding("ctrl+h", "toggle_history", "切换历史"),
        Binding("up", "navigate_up", "向上"),
        Binding("down", "navigate_down", "向下"),
        
    ]
    
    def __init__(self, page_size=10, limit=500, overflow="ellipsis", **kwargs):
        super().__init__(**kwargs)
        self.page_size = page_size
        self.limit = limit
        self.overflow = overflow
        self.history_visible = False
        self.start = None
        self.end = None
        # 用于管理异步任务的集合
        self.running_tasks = set()
        
    def compose(self) -> ComposeResult:
        """构建UI布局"""
        with Horizontal():
            # 历史记录面板（默认隐藏）
            with Container(id="history-container", classes="search-history hidden"):
                yield SearchHistoryWidget(id="history-widget")
                
            # 主要内容区域
            with Vertical(id="main-container", classes="main-content"):
                # 搜索输入区域
                with Container(id="search-container"):
                    yield Static("ketacli 交互式搜索", id="search-title")
                    with Container(id="input-wrapper", classes="input-wrapper"):
                        # 时间范围选择器和输入框行
                        with Horizontal(id="input-row"):
                            yield SPLTextArea(id="spl-input", classes="spl-input")
                            with Vertical(id="button-column", classes="button-column"):
                                yield TimeRangeSelector(id="time-range-selector")
                                yield Select([("100", "100"), ("500", "500"), ("1000", "1000"), ("5000", "5000"), ("10000", "10000")], value="100", id="limit-select", classes="limit-select")
                                yield Button("搜索", id="search-button", variant="primary")
                        # 添加建议显示组件
                        yield Static("", id="suggestion-display")
                    
                # 搜索结果区域
                with Container(id="results-container", classes="search-result"):
                    # 创建原始搜索结果组件
                    original_search_widget = SearchResultWidget()
                    # 使用增强版本包装原始组件
                    yield EnhancedSearchResultWidget(original_search_widget, id="search-results")
                    
        yield Footer()
        
    def on_mount(self) -> None:
        """应用启动时的初始化"""
        search_results = self.query_one("#search-results", EnhancedSearchResultWidget)
        search_results.initialize_table(self.page_size, self.limit, self.overflow)
        
        # 设置默认查询（使用一个会触发测试数据的查询）
        spl_input = self.query_one("#spl-input", SPLTextArea)
        spl_input.set_spl_text("search repo=\"_internal\"")
        # 使用管理的异步任务执行初始搜索
        self.create_managed_task(self.action_search())
        
    def action_quit(self) -> None:
        """退出应用"""
        # 取消所有正在运行的异步任务
        for task in self.running_tasks:
            if not task.done():
                task.cancel()
        
        # 清空任务集合
        self.running_tasks.clear()
        
        # 退出应用
        self.exit()
    
    def create_managed_task(self, coro):
        """创建并管理异步任务"""
        task = asyncio.create_task(coro)
        self.running_tasks.add(task)
        
        # 添加任务完成回调，自动从集合中移除已完成的任务
        def task_done_callback(completed_task):
            self.running_tasks.discard(completed_task)
        
        task.add_done_callback(task_done_callback)
        return task

        
    def action_toggle_history(self) -> None:
        """切换历史记录面板显示/隐藏"""
        # 添加日志输出来调试按键事件
        with open("debug_bindings.log", "a") as f:
            f.write(f"[{datetime.now()}] action_toggle_history 被调用\n")
        
        history_container = self.query_one("#history-container")
        main_container = self.query_one("#main-container")
        self.history_visible = not self.history_visible
        
        if self.history_visible:
            history_container.remove_class("hidden")
            main_container.remove_class("main-content")
            history_widget = self.query_one("#history-widget", SearchHistoryWidget)
            history_widget.visible = True
            history_widget.refresh_history()
            # 将焦点设置到历史记录表格
            history_table = self.query_one("#history-table", DataTable)
            history_table.focus()

        else:
            history_container.add_class("hidden")
            main_container.add_class("main-content")
            # 将焦点返回到搜索输入框
            spl_input = self.query_one("#spl-input", SPLTextArea)
            spl_input.focus()

        
        with open("debug_bindings.log", "a") as f:
            f.write(f"[{datetime.now()}] action_toggle_history 执行完成，visible={self.history_visible}\n")
            
    def action_toggle_filter(self) -> None:
        """切换过滤功能"""
        search_results = self.query_one("#search-results", SearchResultWidget)
        search_results.filter_switch()
        


        
    def action_paste(self) -> None:
        """粘贴操作"""
        # 添加日志输出来调试按键事件
        with open("debug_bindings.log", "a") as f:
            f.write(f"[{datetime.now()}] action_paste 被调用\n")
        
        spl_input = self.query_one("#spl-input", SPLTextArea)
        spl_input.handle_paste()
        
        # 添加通知确认操作执行

        
        with open("debug_bindings.log", "a") as f:
            f.write(f"[{datetime.now()}] action_paste 执行完成\n")
        
    async def action_search(self) -> None:
        """异步执行搜索"""
        # 如果搜索已经在进行中，直接返回，防止并发搜索
        if self._search_in_progress:
            # 进度提示弱化为 info，减少噪音
            self.notify("搜索正在进行中，请稍候...", severity="info")
            return
            
        # 设置搜索锁
        self._search_in_progress = True
        
        try:
            spl_input = self.query_one("#spl-input", SPLTextArea)
            search_results = self.query_one("#search-results", EnhancedSearchResultWidget)
            time_selector = self.query_one("#time-range-selector", TimeRangeSelector)
            limit_select = self.query_one("#limit-select", Select)
            suggestion_display = self.query_one("#suggestion-display", Static)
            search_button = self.query_one("#search-button", Button)
            
            # 更新搜索按钮状态为搜索中并禁用
            search_button.label = "搜索中"
            search_button.disabled = True
            
            # 显示搜索中状态
            suggestion_display.update("搜索中...")
            
            # 清空搜索结果表格
            results_table = self.query_one("#results-table", DataTable)
            results_table.clear(columns=True)
            
            # 清空状态显示
            status = self.query_one("#search-status", Static)
            status.update("")
            
            # 如果历史记录可见，从历史记录中获取选中的查询
            if self.history_visible:
                history_widget = self.query_one("#history-widget", SearchHistoryWidget)
                selected_spl = history_widget.get_current_selection()
                if selected_spl:
                    spl_input.set_spl_text(selected_spl)
                    
            spl_text = spl_input.get_spl_text()
            
            # 获取时间范围参数
            start_time, end_time = time_selector.get_time_range()
            
            # 获取搜索条数限制
            try:
                limit = int(limit_select.value) if limit_select.value else 100
                if limit <= 0:
                    limit = 100
            except (ValueError, TypeError):
                limit = 100

            try:
                # 异步执行搜索，不阻塞UI
                await search_results.search_async(spl_text, start_time, end_time, limit)
                
                # 搜索完成后清除状态显示
                suggestion_display.update("搜索完成")
                self.notify("搜索完成", severity="success")
                
                # 如果历史记录可见，刷新历史记录显示
                if self.history_visible:
                    history_widget = self.query_one("#history-widget", SearchHistoryWidget)
                    history_widget.refresh_history()
                    
            except Exception as e:
                suggestion_display.update(f"搜索失败: {e}")
            finally:
                # 恢复搜索按钮状态
                search_button.label = "搜索"
                search_button.disabled = False
        except Exception as e:
            # 捕获所有异常，确保即使在图表上按回车键也不会阻塞程序
            self.notify(f"搜索操作出错: {str(e)}", severity="error")
            # 记录错误到日志
            with open("search_error.log", "a") as f:
                f.write(f"[{datetime.now()}] 搜索错误: {str(e)}\n")
        finally:
            # 无论如何都要释放搜索锁
            self._search_in_progress = False
        
    def action_navigate_up(self) -> None:
        """向上导航"""
        if self.history_visible:
            # 在历史记录中导航
            history_table = self.query_one("#history-table", DataTable)
            if history_table.cursor_coordinate.row > 0:
                history_table.cursor_coordinate = Coordinate(history_table.cursor_coordinate.row - 1, history_table.cursor_coordinate.column)
        else:
            search_results = self.query_one("#search-results", EnhancedSearchResultWidget)
            search_results.navigate("up")
            
    def action_navigate_down(self) -> None:
        """向下导航"""
        if self.history_visible:
            # 在历史记录中导航
            history_table = self.query_one("#history-table", DataTable)
            if history_table.cursor_coordinate.row < history_table.row_count - 1:
                history_table.cursor_coordinate = Coordinate(history_table.cursor_coordinate.row + 1, history_table.cursor_coordinate.column)
        else:
            search_results = self.query_one("#search-results", EnhancedSearchResultWidget)
            search_results.navigate("down")
    

    def on_text_area_changed(self, event) -> None:
        """TextArea内容变化时的处理"""
        # SPLTextArea会自己处理文本变化，这里不需要额外处理
        pass
            

        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击事件"""
        if event.button.id == "search-button":
            # 检查是否已经有搜索在进行中
            if self._search_in_progress:
                self.notify("搜索正在进行中，请稍候...", severity="info")
                return
            # 创建管理的异步任务来执行搜索
            self.create_managed_task(self.action_search())
            
    def on_search_history_widget_history_selected(self, message: SearchHistoryWidget.HistorySelected) -> None:
        """处理历史记录选择消息"""
        # 将选中的查询放到搜索框中
        spl_input = self.query_one("#spl-input", SPLTextArea)
        spl_input.set_spl_text(message.query)
        # 先关闭历史记录面板
        self.action_toggle_history()
        # 检查是否已经有搜索在进行中
        if self._search_in_progress:
            self.notify("搜索正在进行中，请稍候...", severity="info")
            return
        # 使用管理的异步任务执行搜索
        self.create_managed_task(self.action_search())
    
    def on_search_requested(self, message: SearchRequested) -> None:
        """处理SPLTextArea发送的搜索请求消息"""
        # 检查是否已经有搜索在进行中
        if self._search_in_progress:
            self.notify("搜索正在进行中，请稍候...", severity="warning")
            return
        
        # 将搜索文本设置到输入框中
        spl_input = self.query_one("#spl-input", SPLTextArea)
        spl_input.set_spl_text(message.spl_text)
        
        # 使用管理的异步任务执行搜索
        self.create_managed_task(self.action_search())
            
    @staticmethod
    def check_char(key):
        """检查字符是否允许输入"""
        allowed_pattern = r'^[\u4e00-\u9fa5A-Za-z0-9\w .,;!?()\'\"-\|_/\*=:<>\{\}\[\]\$#%@!&\*\^+~`;\\]+$'
        if re.match(allowed_pattern, key):
            return key
        return None
        
    def run_app(self):
        """运行应用的入口方法，保持与原始接口兼容"""
        self.run()
        
    # 为了保持与原始代码的兼容性，添加一些方法别名
    def loop(self):
        """兼容原始的loop方法"""
        self.run()
        

        
    def exit(self, code=0):
        """兼容原始的exit方法"""
        super().exit()


# 为了保持向后兼容性，保留原始类名
class InteractiveSearchLegacy(InteractiveSearch):
    """保持向后兼容的类名别名"""
    pass


if __name__ == "__main__":
    app = InteractiveSearch()
    app.run()
