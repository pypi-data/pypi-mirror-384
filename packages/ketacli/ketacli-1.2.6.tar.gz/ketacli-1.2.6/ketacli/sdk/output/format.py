import json

from prettytable import PrettyTable
from datetime import datetime
from rich.table import Table, Column
from rich.console import Console
from ..converters import apply_field_converter

class OutputTable:

    def __init__(self, header, rows: list = None) -> None:
        self.header = header
        if rows is None:
            self.rows = []
        else:
            self.rows = rows
        self.console = Console()

    def add_row(self, row: list) -> None:
        self.rows.append(row)

    def add_rows(self, rows: list) -> None:
        self.rows.extend(rows)

    def prettify(self) -> any:
        newtable = OutputTable(self.header)
        for r in self.rows:
            value = []
            for i in range(len(self.header)):
                if i < len(r):
                    value.append(prettify_value(self.header[i], r[i]))
            newtable.add_row(value)
        return newtable

    def get_json_string(self) -> str:
        json_options = {"indent": 4, "separators": (
            ",", ": "), "sort_keys": True, "ensure_ascii": False}
        objects = []
        for row in self.rows:
            newrow = {k: v for k, v in dict(
                zip(self.header, row)).items() if v is not None}
            objects.append(newrow)
        return json.dumps(objects, **json_options)


    def get_pretty_table(self) -> PrettyTable:
        ret = PrettyTable(self.header)
        ret.add_rows(self.rows)
        ret.align = "l"
        return ret

    def get_formatted_string(self, format="text"):
        if format == "table":
            table = Table(show_header=True, header_style="bold magenta", expand=True,)
            for column in self.header:
                table.add_column(column, style="blink")
            for row in self.rows:
                row = [str(i) for i in row]
                table.add_row(*row)
            return table

        return self.get_pretty_table().get_formatted_string(format)


def prettify_value(key, value):
    if value is None:
        return value

    if key.lower().endswith("time") and isinstance(value, int):
        dt_object = datetime.fromtimestamp(value / 1000)
        return dt_object.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(value, str) or isinstance(value, int) or isinstance(value, bool) \
            or isinstance(value, float):
        return value
    else:
        return json.dumps(value, ensure_ascii=False)


def make_records_to_table(header=[], records=[], field_aliases=None, field_converters=None):
    if field_aliases is None:
        field_aliases = {}
    if field_converters is None:
        field_converters = {}
        
    # 处理字典格式的header配置
    field_names = []
    if header and isinstance(header[0], dict):
        # 如果header是字典格式，提取字段名
        for field_config in header:
            if isinstance(field_config, dict) and "name" in field_config:
                # 新格式：{"name": "field_name", "alias": "别名"}
                field_names.append(field_config["name"])
            else:
                field_names.append(field_config)
        header = field_names
    
    # 从第一条数据获取header
    if len(header) <= 0:
        if len(records) <= 0:
            return None
        else:
            for k in records[0]:
                header.append(k)
    
    # 生成显示用的表头（使用别名）
    display_header = []
    for field_name in header:
        if field_name in field_aliases:
            display_header.append(field_aliases[field_name])
        else:
            display_header.append(field_name)

    table = OutputTable(display_header)
    for row in records:
        value = []
        for k in header:
            if k in row:
                field_value = row[k]
                # 应用字段转换器
                if k in field_converters:
                    field_value = apply_field_converter(field_value, field_converters[k])
                value.append(field_value)
            else:
                value.append(None)
        table.add_row(value)
    return table


def make_table(header=None, rows=None, transpose=False):
    if rows is None:
        rows = []
    if header is None:
        header = []
    if transpose:
        table = OutputTable(["Field Name", "Values"])
        tmp = dict(zip(header, *rows))
        for k, v in tmp.items():
            table.add_row([k, v])
    else:
        table = OutputTable(header)
        table.add_rows(rows)
    return table


def format_table(table: OutputTable, format=None, prettify=True):
    if format is None:
        format = "table"
    if prettify:
        table = table.prettify()
    if format == "json":
        return table.get_json_string()
    return table.get_formatted_string(format)
