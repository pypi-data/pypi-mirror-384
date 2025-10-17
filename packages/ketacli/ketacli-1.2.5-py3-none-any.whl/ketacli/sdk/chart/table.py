import math

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.console import Text
from rich.layout import Layout

from ketacli.sdk.chart import utils
from ketacli.sdk.chart.base import BaseChart
from ketacli.sdk.output.output import search_result_output
from ketacli.sdk.base.search import search_spl
from ketacli.sdk.util import Template
from ketacli.sdk.chart.utils import search_from_table
import copy

SPECIAL_CHAR = ["\x08", "\x7f", "\n", "\r", "\x1b[A", "\x1b[B", "\x1b[C", "\x1b[D", '\x1b\x1b[C', '\x1b\x1b[D']


class KTable(BaseChart):
    def __init__(self, chart_config: dict, mark="", **kwargs):
        spl = chart_config.get("spl", "")
        self.chart_config = chart_config
        self.spl = Template(spl).render(**kwargs)
        start = chart_config.get("start", None)
        end = chart_config.get("end", None)
        limit = chart_config.get("limit", 500)
        self.transpose = chart_config.get("transpose", False)
        self.title = chart_config.get("title", "")
        self.columns_config = chart_config.get("columns", {})
        self.border_style = ""
        self.subtitle = chart_config.pop("subtitle", "")
        self.child = chart_config.pop("child", {})

        self.line_childs = chart_config.get("line_childs", [])
        self.simplify_show = chart_config.get("simplify_show", False)
        self.layout = Layout(name="table", ratio=1)
        self.overflow = chart_config.get("overflow", "ellipsis")
        self.page_size = chart_config.get("page_size", 10)
        self.row_styles = None
        self.row_index = 0
        self.col_index = 0
        self.page_num = 1
        self.max_page_size = 0
        self.table_texts = []
        self.width = 0
        self.height = 0
        self.console = None
        self.options = None
        self.need_show_line_chart = False
        self.child_panel = None
        self.child_chart = None
        self.search_text = ""
        self.search_visible = False
        self.start = start
        self.end = end
        self.limit = limit
        if mark:
            self.mark = f" | {mark}"
        else:
            self.mark = ""
        self.choice_text = ""
        self.m_table_data = []
        self.table_data = {}
        self.data = None
        self.child_charts = None
        self.init_page_size = 0
        self.total_row = 0
        self.err = None

    def search(self, spl=None):
        self.page_size = self.chart_config.get("page_size", 10)
        if spl:
            self.spl = spl
            self.title = spl
        try:
            self.data = search_result_output(
                search_spl(spl=str(self.spl), start=self.start, end=self.end, limit=self.limit),
                transpose=self.transpose)
            self.total_row = len(self.data.rows)
            self.child_charts = self.show_child()

            if len(self.data.rows) < self.page_size:
                self.page_size = len(self.data.rows)
            self.init_page_size = self.page_size
            self.row_index = 0

            if self.line_childs and not self.mark:
                self.mark = " | 按 [bold green]D[/bold green] 查看子视图 ｜ 按 \"[bold green]/[/bold green]\" 关键字过滤"
            self.err = None
        except Exception as e:
            self.err = e

    def get_data(self, page_num=1, page_size=10):
        self.m_table_data = utils.sort_values_by_header(
            self.data.header,
            self.data.rows[(page_num - 1) * page_size:page_num * page_size],
            self.columns_config, format_method=self.render_text, transpose=self.transpose,
            simplify_show=self.simplify_show)

    @staticmethod
    def render_text(key, value: dict):
        column_attributes = value.get("attributes", {})
        style = column_attributes.get("style", "")
        threshold = column_attributes.get("threshold", None)
        _format = column_attributes.get("format", None)
        suffix = column_attributes.get("suffix", "")
        prefix = column_attributes.get("prefix", "")
        justify = column_attributes.get("justify", "center")
        enum = column_attributes.get("enum", None)
        title = column_attributes.get('alias', key)
        identification = column_attributes.get('identification', False)

        row_texts = []
        for data in value['data']:
            if threshold:
                style = utils.threshold(data, **threshold)
            if _format:
                data = utils.format(data, type=_format)
            if enum:
                enum_values = utils.enum(data, **enum)
                data = enum_values.get("alias", data)
                style = enum_values.get("style", style)
            text = ((f"{prefix}{data}{suffix}", style),)

            text = Text.assemble(*text, justify=justify)
            row_texts.append(text)
        return {"title": title, "justify": justify, "row_texts": row_texts, "identification": identification}

    def get_current_raw_data(self):
        return self.data.rows[self.page_size * (self.page_num - 1) + self.row_index]

    def get_table(self):
        self.get_data(self.page_num, self.page_size)
        table = Table(show_header=True, header_style="bold magenta", width=self.width, expand=True, padding=0,
                      show_lines=True, row_styles=self.row_styles, highlight=True)
        tmp_data = {}
        self.table_data = {}
        identification = ""
        if self.search_text:
            mtable_data, self.total_row = search_from_table(self.search_text, copy.deepcopy(self.m_table_data))

        else:
            mtable_data = self.m_table_data
            self.total_row = len(self.data.rows)

        # if self.total_row < self.init_page_size:
        #     self.page_size = self.total_row
        # else:
        #     self.page_size = self.init_page_size

        if self.total_row <= 0:
            return table
        for data in mtable_data:
            key, value = next(iter(data.items()))

            if value.get("identification"):
                identification = f": {value['title']}:{value['row_texts'][self.row_index]}"
            table.add_column(value.get('title'), style="blink", justify=value.get('justify'), overflow=self.overflow)
            for row_text in value.get('row_texts')[self.row_index:]:

                if key not in self.table_data:
                    self.table_data[key] = row_text

                if key not in tmp_data:
                    tmp_data[key] = []
                tmp_data[key].append(row_text)

        for row_texts in [x for x in zip(*list(tmp_data.values()))]:
            table.add_row(*row_texts)
        up_down = "上下键切换行"
        left_right = "左右键或 CMD + 左右键切换页码"
        self.subtitle = (f"[#808080][bold green]{self.row_index + 1}/{self.page_size}[/bold green]"
                         f" {up_down} | [bold green]{self.page_num}/{math.ceil(self.total_row / self.init_page_size)}[/bold green]"
                         f" {left_right}{identification}{self.mark}[/#808080]")

        return table

    def main_table(self, console, options):
        self.console = console
        self.options = options
        self.table_texts = []
        self.width = options.max_width or console.width
        self.height = options.height or console.height
        self.max_page_size = (self.height - 4) // 2
        if not self.page_size:
            return
        self.row_styles = [""] * self.page_size
        self.row_styles[0] = "on blue"
        table = self.get_table()
        title_text = Text(f"{self.title}({len(self.data.rows)})", justify="center", style="bold")

        if self.child_chart:
            return self.child_chart.layout
        else:
            search_panel = Panel("🐩> [bold]" + self.search_text + "[/bold]", expand=True,
                                 title="[bold]过滤[/bold][#808080] / 输入字符匹配任意字段进行过滤[/#808080]",
                                 height=3)
            search_layout = Layout("search", visible=self.search_visible, size=3)
            search_layout.split(search_panel)
            if self.search_visible:
                table_height = self.height - 3
            else:
                table_height = self.height
            table_panel = Panel(table, expand=True, padding=0, title=title_text,
                                border_style=self.border_style,
                                subtitle=self.subtitle, height=table_height)
            table_layout = Layout("table", visible=True)
            table_layout.split(table_panel)
            self.layout.split_column(search_layout, table_layout)

            return self.layout

    def __rich_console__(self, console, options):
        this = self
        if self.child_chart:
            this = self.child_chart
        if not this.data.header:
            yield this.nodata_panel(console, options)
        elif self.err:
            yield Text(f"{self.err}\n {self.spl}", style="red")
        else:
            yield this.main_table(console, options)

    def row_add(self):
        if self.row_index < self.page_size - 1:
            self.row_index += 1

    def row_sub(self):
        if self.row_index > 0:
            self.row_index -= 1

    def col_add(self):
        self.col_index += 1

    def col_sub(self):
        self.col_index -= 1

    def search_input(self, key):
        self.search_text += key

    def backspace(self):
        self.search_text = self.search_text[:-1]

    def details(self):
        if not self.child_chart:
            self.child_chart = self.show_child()
            next(self.child_charts)
        else:
            self.child_chart = None

    def next_chart(self):
        try:
            next(self.child_charts)
        except StopIteration:
            self.child_charts = self.show_child()
            next(self.child_charts)

    def filter_switch(self):
        self.search_visible = not self.search_visible

    def page_add(self):
        from ketacli.sdk.chart.utils import file_debug
        file_debug('keyboard_handler.txt', "page_add")
        this = self
        if this.page_num < this.total_row / this.init_page_size:
            this.row_index = 0
            this.page_num += 1
            if this.total_row - (this.init_page_size * (this.page_num - 1)) < this.init_page_size:
                this.page_size = this.total_row - (this.init_page_size * (this.page_num - 1))

    def page_sub(self):
        this = self
        if self.page_num > 1:
            this.row_index = 0
            this.page_num -= 1
            this.page_size = this.init_page_size

    def keyboard_handler(self, key):

        this = self
        if self.child_chart:
            this = self.child_chart

        if key == "\x1b[A" and this.row_index > 0:
            this.row_index -= 1
        elif key == "\x1b[B" and this.row_index < this.page_size - 1:
            this.row_index += 1
        elif key == "\x1b[C" and this.page_num < this.total_row / this.init_page_size:
            this.row_index = 0
            this.page_num += 1
            if this.total_row - (this.init_page_size * (this.page_num - 1)) < this.init_page_size:
                this.page_size = this.total_row - (this.init_page_size * (this.page_num - 1))
        elif key == "\x1b[D" and this.page_num > 1:
            this.row_index = 0
            this.page_num -= 1
            this.page_size = this.init_page_size
        elif this.search_visible and key not in SPECIAL_CHAR:
            this.search_text += key
        elif key in ["\x08", "\x7f"]:
            this.search_text = this.search_text[:-1]
        elif key == "d" and not self.child_chart:
            try:
                next(self.child_charts)
            except StopIteration:
                self.child_charts = self.show_child()
                next(self.child_charts)
        elif self.child_chart and key == "n":
            try:
                next(self.child_charts)
            except StopIteration:
                self.child_charts = self.show_child()
                next(self.child_charts)
        elif key == "d" and self.child_chart:
            self.child_chart = None
        elif key == '/':
            this.search_visible = True

        elif key in ['\r', '\n']:
            this.search_visible = False
        else:
            return key

    def show_child(self):
        # pass
        if not self.line_childs:
            yield

        for child in self.line_childs:
            if child.get("type") == "table":
                self.child_chart = KTable(child, mark="按 [bold green]D[/bold green] 键退出子视图，"
                                                      "按 [bold yellow]N[/bold yellow] 键切换到下一个子视图",
                                          **self.table_data)
                self.child_chart.search()
                self.child_chart.border_style = self.border_style
                self.child_chart.main_table(self.console, self.options)
                yield


if __name__ == '__main__':
    import yaml

    data1 = yaml.safe_load(open("../../charts/infra-host.yaml", "r"))
    table = KTable(data1.get('charts')[0])
    table.search()
    table.row_index = 0
    table.search_text = "aa"
    table.main_table(Console(), Console().options)
    table.get_current_raw_data()

    next(table.show_child())
    table.child_chart.row_index = 9
    table.child_chart.main_table(Console(), Console().options)
