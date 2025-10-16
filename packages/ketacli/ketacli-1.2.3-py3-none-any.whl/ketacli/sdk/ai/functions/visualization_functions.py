"""
可视化功能的 Function Call 包装器
"""

from typing import Optional, List, Dict, Tuple
from datetime import datetime
from ketacli.sdk.ai.function_call import function_registry
from ketacli.sdk.base.search import search_spl
from ketacli.sdk.ai.functions.search_functions import validate_spl_value_quotes
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static
from textual_plotext import PlotextPlot
from ketacli.sdk.output.output import search_result_output


class ChatChartWidget(Static):
    """聊天窗口专用的轻量图表组件（不依赖ChartVisualizationWidget）

    特性：
    - 仅渲染图表，无额外配置UI；适配消息内紧凑显示
    - 支持折线/柱状；自动选择X/Y字段（可通过参数覆盖）
    - 直接使用 textual_plotext 绘制
    """

    def __init__(
        self,
        chart_type: str = "line",
        data: Optional[List[Dict]] = None,
        x_field: Optional[str] = None,
        y_fields: Optional[List[str]] = None,
        group_field: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.chart_type = (chart_type or "line").lower() if chart_type else "line"
        self.data = data or []
        self.x_field = x_field
        self.y_fields = y_fields or []
        self.group_field = group_field
        


    def compose(self) -> ComposeResult:
        with Container(id="chat-chart-content", classes="chart-content"):
            # 占位，实际绘制在on_mount中进行
            yield PlotextPlot(id="chat-plot", classes="chart-widget")

    def on_mount(self) -> None:
        try:
            self.notify(f"data: {self.data}")
            plot_widget = self.query_one("#chat-plot", PlotextPlot)
            plot_widget.styles.height = "100%"
            plot_widget.styles.width = "100%"
            plot_widget.styles.min_height = "15"
            self._auto_select_fields()
            self._draw_plot(plot_widget)
        except Exception as e:
            content = self.query_one("#chat-chart-content")
            content.remove_children()
            content.mount(Static(f"图表绘制失败: {str(e)}", classes="chart-error"))


    def update_data(self, data: List[Dict]):
        self.data = data or []
        plot_widget = self.query_one("#chat-plot", PlotextPlot)
        self._auto_select_fields()
        self._draw_plot(plot_widget)


    # ---------- 内部工具方法 ----------
    def _auto_select_fields(self) -> None:
        fields = list(self.data[0].keys()) if self.data else []
        # X优先时间字段
        if not self.x_field:
            for cand in ["_time", "time", "timestamp"]:
                if cand in fields:
                    self.x_field = cand
                    break
            if not self.x_field and fields:
                self.x_field = fields[0]
        # Y选择数值字段（排除X）
        if not self.y_fields:
            numeric_candidates = [f for f in fields if f != self.x_field and self._is_numeric_field(f, self.data)]
            # 若找不到数值字段，退化为除X外的所有字段
            self.y_fields = numeric_candidates or [f for f in fields if f != self.x_field]
            # 控制数量，聊天中默认最多两条，避免拥挤
            self.y_fields = self.y_fields[:2]

    def _is_timestamp_field(self, field_name: str, data: List[Dict]) -> bool:
        if not field_name:
            return False
        time_keywords = ["time", "timestamp", "date", "datetime", "_time"]
        field_lower = field_name.lower()
        if any(k in field_lower for k in time_keywords):
            for row in data[:5]:
                if field_name in row and row[field_name] is not None:
                    v = row[field_name]
                    if isinstance(v, (int, float)):
                        if 0 < v < 2524608000000 or 0 < v < 2524608000:
                            return True
                    elif isinstance(v, str):
                        try:
                            datetime.fromisoformat(v.replace("Z", "+00:00"))
                            return True
                        except Exception:
                            pass
        return False

    def _is_numeric_field(self, field_name: str, data: List[Dict]) -> bool:
        for row in data[:5]:
            if field_name in row and row[field_name] is not None:
                v = row[field_name]
                if isinstance(v, (int, float)):
                    return True
                if isinstance(v, str):
                    try:
                        float(v)
                        return True
                    except Exception:
                        pass
        return False

    def _prepare_series(self, data: List[Dict], x_field: str, y_fields: List[str], group_field: Optional[str]) -> Dict[str, List[Tuple]]:
        if not data or not x_field or not y_fields:
            return {}
        series: Dict[str, List[Tuple]] = {}
        is_ts = self._is_timestamp_field(x_field, data)

        # 按分组或逐字段组织
        if group_field and group_field in data[0]:
            group_vals = sorted({str(row[group_field]) for row in data if group_field in row and row[group_field] is not None})
            for gv in group_vals:
                for y in y_fields:
                    key = f"{y}_{gv}" if len(y_fields) > 1 else gv
                    series[key] = []
        else:
            for y in y_fields:
                series[y] = []

        for row in data:
            if x_field not in row:
                continue
            x_val = row[x_field]
            # 规范化X值为数值以绘图
            if is_ts:
                try:
                    if isinstance(x_val, str):
                        dt = datetime.fromisoformat(x_val.replace('Z', '+00:00'))
                        x_num = dt.timestamp()
                    elif isinstance(x_val, (int, float)):
                        x_num = float(x_val) if x_val < 1e11 else float(x_val) / 1000.0
                    else:
                        x_num = 0.0
                except Exception:
                    x_num = 0.0
            else:
                # 非时间字段：保留数值；若为字符串类别，则直接使用字符串作为X值，
                # 以支持柱状图按类别绘制（例如服务名称）
                x_num = float(x_val) if isinstance(x_val, (int, float)) else str(x_val)

            if group_field and group_field in row and row[group_field] is not None:
                gv = str(row[group_field])
                for y in y_fields:
                    key = f"{y}_{gv}" if len(y_fields) > 1 else gv
                    y_val = row.get(y)
                    try:
                        y_num = float(y_val)
                    except Exception:
                        y_num = 0.0
                    series[key].append((x_num, y_num))
            else:
                for y in y_fields:
                    y_val = row.get(y)
                    try:
                        y_num = float(y_val)
                    except Exception:
                        y_num = 0.0
                    series[y].append((x_num, y_num))
        return series

    def _draw_plot(self, plot_widget: PlotextPlot) -> None:
        content = self.query_one("#chat-chart-content")
        # 清空并绘制
        plot_widget.plt.clear_data()

        if not self.data:
            content.remove_children()
            content.mount(Static("暂无数据可显示", classes="chart-placeholder"))
            return

        series = self._prepare_series(self.data, self.x_field, self.y_fields, self.group_field)
        self.notify(f"数据格式正确，共{len(self.data)}条记录，{len(series)}个序列， 前10个数据点: {list(series.values())[:10]}")
        if not series:
            content.remove_children()
            content.mount(Static("数据格式不正确或缺少字段", classes="chart-error"))
            return

        # 时间格式化（plotext）
        is_ts = self._is_timestamp_field(self.x_field, self.data)
        if is_ts:
            try:
                plot_widget.plt.date_form("Y-m-d H:M:S")
            except Exception:
                pass

        # 绘制
        try:
            # 过滤空序列；对于柱状图允许字符串X（类别），避免把类别误置为0导致只绘制一个柱
            if self.chart_type == "bar":
                filtered = {
                    name: [(x, y) for x, y in points if ((isinstance(x, (int, float)) or isinstance(x, str)) and isinstance(y, (int, float)))]
                    for name, points in series.items()
                }
            else:
                # 折线图保持数值X并按X排序
                filtered = {
                    name: sorted([(x, y) for x, y in points if isinstance(x, (int, float)) and isinstance(y, (int, float))], key=lambda t: t[0])
                    for name, points in series.items()
                }
            self.notify(f"filtered: {filtered}")
            filtered = {name: pts for name, pts in filtered.items() if len(pts) > 0}
            if not filtered:
                content.remove_children()
                # content.mount(Static("数据点为空，无法绘制图表", classes="chart-error"))
                return "数据点为空，无法绘制图表"

            series_names = list(filtered.keys())

            if self.chart_type == "bar" and len(filtered) > 1:
                # 分组柱状图：按所有X值对齐并并排显示
                all_x_values = set()
                for points in filtered.values():
                    for x, _ in points:
                        all_x_values.add(x)
                sorted_x_values = sorted(all_x_values)
                # 类别标签（时间戳转换为字符串）
                if is_ts:
                    x_labels = [self._format_timestamp_for_display(x) for x in sorted_x_values]
                else:
                    x_labels = [str(x) for x in sorted_x_values]

                y_data_arrays = []
                for name in series_names:
                    pts = filtered[name]
                    y_dict = {x: y for x, y in pts}
                    y_values = [y_dict.get(x, 0) for x in sorted_x_values]
                    y_data_arrays.append(y_values)

                try:
                    plot_widget.plt.multiple_bar(x_labels, y_data_arrays, label=series_names)
                except Exception:
                    # 兜底：逐系列绘制（并不会并排，仅保证可见）
                    for name, points in filtered.items():
                        xs = [p[0] for p in points]
                        ys = [p[1] for p in points]
                        if is_ts:
                            xs_labels = [self._format_timestamp_for_display(x) for x in xs]
                            try:
                                plot_widget.plt.bar(xs_labels, ys, label=name)
                            except Exception:
                                plot_widget.plt.bar(xs_labels, ys)
                        else:
                            try:
                                plot_widget.plt.bar(xs, ys, label=name)
                            except Exception:
                                plot_widget.plt.bar(xs, ys)
            else:
                # 单序列或非柱状图：常规绘制
                for name, points in filtered.items():
                    xs = [p[0] for p in points]
                    ys = [p[1] for p in points]
                    # 如果X为时间戳，转换为可读字符串以确保坐标显示
                    if is_ts:
                        xs_labels = [self._format_timestamp_for_display(x) for x in xs]
                        if self.chart_type == "bar":
                            try:
                                plot_widget.plt.bar(xs_labels, ys, label=name)
                            except Exception:
                                plot_widget.plt.bar(xs_labels, ys)
                        else:
                            try:
                                plot_widget.plt.plot(xs_labels, ys, label=name)
                            except Exception:
                                plot_widget.plt.plot(xs_labels, ys)
                    else:
                        if self.chart_type == "bar":
                            try:
                                plot_widget.plt.bar(xs, ys, label=name)
                            except Exception:
                                plot_widget.plt.bar(xs, ys)
                        else:
                            try:
                                plot_widget.plt.plot(xs, ys, label=name)
                            except Exception:
                                plot_widget.plt.plot(xs, ys)
            plot_widget.plt.xlabel(self.x_field or "x")
            if len(self.y_fields) == 1:
                plot_widget.plt.ylabel(self.y_fields[0])
            else:
                plot_widget.plt.ylabel("值")
            # 用标题简要展示序列名称，替代图例
            try:
                if series_names:
                    max_len = 80
                    title_text = ", ".join(series_names)
                    if len(title_text) > max_len:
                        title_text = title_text[:max_len] + "..."
                    plot_widget.plt.title(title_text)
            except Exception:
                self.notify("图表标题设置失败", severity="error")
            plot_widget.refresh()
        except Exception as e:
            content.remove_children()
            content.mount(Static(f"图表绘制失败: {str(e)}", classes="chart-error"))
            raise

    def _format_timestamp_for_display(self, x: float) -> str:
        try:
            # x 为秒级时间戳（在 _prepare_series 中已做毫秒到秒转换）
            dt = datetime.fromtimestamp(x)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(x)


@function_registry.register(
    name="display_chart_textual",
    description="通过Textual显示图表（折线/柱状），支持基于SPL的渲染。",
    parameters={
        "type": "object",
        "properties": {
            "spl": {"type": "string", "description": "SPL查询语句"},
            "chart_type": {
                "type": "string",
                "description": "图表类型：line（折线图）、bar（柱状图）",
                "enum": ["line", "bar"],
                "default": "line"
            },
            "x_field": {"type": "string", "description": "X轴字段名（可选）"},
            "y_fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Y轴字段列表（可选）"
            },
            "group_field": {"type": "string", "description": "分组字段名（可选）"},
            "start_time": {"type": "string", "description": "开始时间，YYYY-MM-DD HH:MM:SS"},
            "end_time": {"type": "string", "description": "结束时间，YYYY-MM-DD HH:MM:SS"},
            "limit": {"type": "integer", "description": "数据点数量限制", "default": 500}
        },
        "required": ["spl"]
    }
)
def display_chart_textual(
    spl: str,
    chart_type: str = "line",
    x_field: Optional[str] = None,
    y_fields: Optional[List[str]] = None,
    group_field: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 500,
) -> Dict:
    """运行SPL查询并返回可嵌入聊天窗口的图表数据结构。

    返回 ChartVisualizationWidget 实例
    """
    try:
        ct = (chart_type or "line").lower()
        if ct not in ("line", "bar"):
            ct = "line"

        # 查询前进行 SPL 值引号校验
        validate_spl_value_quotes(spl)

        # 解析时间范围
        def _parse_time(t: Optional[str]) -> Optional[datetime]:
            if not t:
                return None
            try:
                return datetime.fromisoformat(t.replace("Z", "+00:00"))
            except Exception:
                try:
                    return datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    return None

        start_dt = _parse_time(start_time)
        end_dt = _parse_time(end_time)

        # 执行查询
        resp = search_spl(spl, start=start_dt, end=end_dt, limit=limit)
        result_output = search_result_output(resp)
        # 转换为 list[dict]
        rows = result_output.rows or []
        columns = result_output.header or []
        data: List[Dict] = []
        for row in rows:
            item: Dict = {}
            for i, col in enumerate(columns):
                try:
                    item[col] = row[i]
                except Exception:
                    item[col] = None
            data.append(item)

        payload: Dict = {
            "chart_type": ct,
            "data": data,
            "x_field": x_field,
            "y_fields": y_fields or ([] if y_fields is None else y_fields),
            "group_field": group_field,
        }
        # 返回独立实现的聊天图表组件
        return ChatChartWidget(id="chart_widget", **payload)
    except Exception as e:
        # 抛异常由执行器标记失败
        import traceback
        traceback.print_exc()
        return {"error": traceback.format_exc()}

