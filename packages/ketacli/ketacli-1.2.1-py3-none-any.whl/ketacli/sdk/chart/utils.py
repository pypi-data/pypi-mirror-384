from datetime import datetime
from rich.text import Text
import time


def threshold(value: (float, int), **kwargs):
    """
    判断值是否在阈值范围内，返回对应的 key
    threshold = threshold(value, green=(0, 80), red=(80, 100))

    Args:
        value:
        **kwargs:

    Returns:

    """
    if not kwargs:
        return ""
    if not isinstance(value, (float, int)):
        return ""
    for style, threshold_value in kwargs.items():
        if threshold_value[0] is None and value <= threshold_value[1]:
            return style
        elif threshold_value[1] is None and value >= threshold_value[0]:
            return style
        elif threshold_value[0] <= value <= threshold_value[1]:
            return style


def duration(value: float, type: str):
    milliseconds = 0
    if type == "duration_ms":
        milliseconds = int(value)
        seconds, milliseconds = divmod(milliseconds, 1000)
    else:
        seconds = int(value)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    n = 0
    duration_str = ""
    if days > 0:
        n += 1
        duration_str += f"{days} 天 "
    if hours > 0:
        n += 1
        duration_str += f"{hours} 小时 "
    if minutes > 0:
        n += 1
        duration_str += f"{minutes} 分 "
    if seconds > 0 and n < 3:
        n += 1
        duration_str += f"{seconds} 秒"
    if milliseconds > 0 and n < 3:
        n += 1
        duration_str += f" {milliseconds} 毫秒"
    return duration_str


def bytes_to_human(value):
    """
    将字节转换为人类可读的格式
    :param value:
    :return:
    """
    value = float(value)
    if value < 1024:
        return f"{value} B"
    elif value < 1024 * 1024:
        return f"{value / 1024:.2f} KB"
    elif value < 1024 * 1024 * 1024:
        return f"{value / 1024 / 1024:.2f} MB"
    else:
        return f"{value / 1024 / 1024 / 1024:.2f} GB"


def kilobytes_to_human(value):
    value = float(value)
    if value < 1024:
        return f"{value} KB"
    elif value < 1024 * 1024:
        return f"{value / 1024:.2f} MB"
    elif value < 1024 * 1024 * 1024:
        return f"{value / 1024 / 1024:.2f} GB"
    else:
        return f"{value / 1024 / 1024 / 1024:.2f} TB"


def format(value, type=None, **kwargs):
    if not value:
        return value
    if type == "int":
        return int(value)
    elif type == "float":
        return round(float(value), 2)
    elif type == "bytes":
        return bytes_to_human(value)
    elif type == "kilobytes":
        return kilobytes_to_human(value)
    elif type == "timestamp_ms":
        return datetime.fromtimestamp(value / 1000).strftime(kwargs.get("format", "%Y-%m-%d %H:%M:%S"))
    elif type == "timestamp_s":
        return datetime.fromtimestamp(value).strftime(kwargs.get("format", "%Y-%m-%d %H:%M:%S"))
    elif type == "duration_ms":
        return duration(value, type="duration_ms")
    elif type == "duration_s":
        return duration(value, type="duration_s")
    elif type == "percentage100":
        return round(float(value), 2)
    elif type == "percentage":
        return round(float(value) * 100, 2)
    else:
        return value


def enum(value, **kwargs):
    if not kwargs or not value:
        return value
    for enum_value, map in kwargs.items():
        if enum_value == value:
            return map
    else:
        return {}


def sort_values_by_header(headers: list, values: list, attrs: dict, format_method, transpose=False,
                          simplify_show=False):
    """
    Given headers and values, along with an attrs dictionary, formats the values according to the configuration in attrs,
    assembles them with the values from headers, sorts them by the order in attrs.
    If a field is not defined in attrs, it is appended at the end.
    If transpose is True, transposes the values and then sorts them according to attrs.

    Args:
        headers (list): List of headers.
        values (list): List of lists where each sublist corresponds to a row of values.
        attrs (dict): Dictionary defining how to handle specific headers with additional attributes.
        format_method (callable): Function to format values with header and attributes.
        transpose (bool): Whether to transpose the values before processing.

    Returns:
        dict: A dictionary with headers as keys and formatted values as values, sorted by attrs order.
    """
    # Transpose values if required
    if transpose:
        values1 = list(map(list, zip(*values)))
        headers = values1[0]  # Update headers if transposed
        values = values1[1:]
        # Create a dictionary from headers and zipped values
    table_dict = dict(zip(headers, zip(*values)))  # Flatten values if transposed

    # Sort and format values according to attrs
    sorted_values = []
    for header in attrs:
        if header in table_dict:
            sorted_values.append(
                {header: format_method(key=header, value={"data": table_dict[header], "attributes": attrs[header]})})

    # Append fields not defined in attrs at the end
    if not simplify_show:
        for header in headers:
            if header not in [list(x.keys())[0] for x in sorted_values]:
                sorted_values.append(
                    {header: format_method(key=header, value={"data": table_dict[header], "attributes": {}})})
    if transpose:
        fields = {'Field Name': {'row_texts': [], 'justify': 'center', 'title': '字段名'}}
        values = {'Value': {'row_texts': [], 'justify': 'center', 'title': '字段值'}}
        sorted_values_to_transpose = []
        for sorted_value in sorted_values:
            v = list(sorted_value.values())[0]

            fields['Field Name']['row_texts'].append(v['title'])
            values['Value']['row_texts'] += v['row_texts']
        sorted_values_to_transpose.append(fields)
        sorted_values_to_transpose.append(values)
        sorted_values = sorted_values_to_transpose
    # search_from_table("keta", sorted_values)
    return sorted_values


def search_from_table(s, table_data: list):
    """
    从给定的table_data列表中，根据字符串s匹配每一行的row_texts字段内的元素。
    如果某一行的row_texts中有元素包含s，则保留该行；否则，从结果中移除该行。

    Args:
        s: 需要匹配的字符串。
        table_data: 列表，结构为[{'agent_id': {...}}, {...}], 其中row_texts是待匹配的字段。

    Returns:
        匹配成功后的table_data列表，其中不包含任何row_texts字段内元素与s不匹配的行。
    """
    col_total = len(list(table_data[0].values())[0]['row_texts'])
    n = 0
    # 使用列表推导式来过滤table_data，仅保留包含匹配项的行

    while n < col_total:

        row_texts = [list(x.values())[0]['row_texts'][n] for x in table_data]
        if not any(s in text for text in row_texts):
            for x in table_data:
                values = list(x.values())[0]
                del values['row_texts'][n]
            col_total -= 1
        else:
            n += 1
    col_total = len(list(table_data[0].values())[0]['row_texts'])
    return table_data, col_total


def file_debug(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(str(data) + "\n")


class ExecutionTimer:
    def __enter__(self):
        """在代码块开始前被调用，记录开始时间"""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """在代码块结束后被调用，计算并打印执行耗时"""
        end_time = time.time()
        execution_time = end_time - self.start_time
        with open("debug.txt", "a", encoding="utf-8") as f:
            f.write(f"代码块执行耗时: {execution_time:.6f} 秒")


if __name__ == '__main__':
    print(threshold(value=81, green=(0, 80), red=(80, 100)))
    print(format(value=60000, type="duration_ms"))
    print(format(value=1024 * 1024 * 1024, type="bytes"))
    print(f"Int: {format(222, 'int')}")
    print(f"Float: {format(3.14159, 'float')}")
    print(f"Bytes: {format(len(b'test'), 'bytes')}")
    print(f"Timestamp (ms): {format(1640000000000, 'timestamp_ms')}")
    print(f"Timestamp (s): {format(16400000, 'timestamp_s')}")
    print(f"Duration (ms): {format(16400000, 'duration_ms')}")
    print(f"Duration (s): {format(164000, 'duration_s')}")
    print(f"Percentage100: {format(75.01, 'percentage100')}")
    print(f"Percentage: {format(0.75, 'percentage')}")
    print(enum(value="online", online={"title": "在线", "style": "green"}))

    headers_example = ["Name", "Age", "Salary"]
    values_example = [["Alice", 30, 50000], ["Bob", 24, 40000]]
    attrs_example = {"Age": {"unit": "years"}, "Salary": {"currency": "USD"}}

    sorted_result = sort_values_by_header(headers_example, values_example, attrs_example, example_format_method,
                                          transpose=False)
    print(sorted_result)
