import time

import plotext as plt
from datetime import datetime
from ketacli.sdk.output.format import OutputTable
from ketacli.sdk.output.output import search_result_output
from ketacli.sdk.base.search import search_spl


class Plot:
    def __init__(self, chart_config: dict):
        field_y = chart_config.get("y_field", "")
        field_x = chart_config.get("x_field", "")
        plot_type = chart_config.get("plot_type", "line")
        if isinstance(field_y, str):
            field_y = [field_y]
        self.plot_type = plot_type
        spl = chart_config.get("spl", "")
        start = chart_config.get("start", None)
        end = chart_config.get("end", None)
        limit = chart_config.get("limit", 500)
        self.data = search_result_output(search_spl(spl=spl, start=start, end=end, limit=limit))
        self.field_x_index = 0
        self.field_y_index = []
        if field_x in self.data.header:
            self.field_x_index = self.data.header.index(field_x)

        for y in field_y:
            if y in self.data.header:
                self.field_y_index.append(self.data.header.index(y))

        self.field_x = field_x
        self.field_y = field_y
        self.time_format = chart_config.get("time_format", "%Y-%m-%d %H:%M:%S")
        self.title = chart_config.get("title", "")
        self.x_label = chart_config.get("x_label", "")
        self.y_label = chart_config.get("y_label", "")
        self.field_group = chart_config.get("field_group", "")
        self.marker = chart_config.get("marker", "hd")
        self.extra_config = chart_config.get("extra_config", {})
        self.theme = chart_config.get("theme", "")
        self.child = chart_config.pop("child", {})
        self.format = chart_config.pop("format", "")
        self.subtitle = chart_config.pop("subtitle", "")

        # 设置标题和坐标轴标签

    def build(self, width, height):
        if not self.data.header:
            return
        plt.clf()

        plt.title(self.title)
        plt.ylabel(self.field_y[0])
        plt.xlabel(self.field_x)

        # 绘制图形
        if self.field_group and self.field_group in self.data.header:
            field_group_index = self.data.header.index(self.field_group)
            group_names = tuple(set([x[field_group_index] for x in self.data.rows]))
            for group_name in group_names:
                if self.data.header[self.field_x_index] == "_time":
                    plt.date_form(self.time_format.replace("%", ""))
                    x = [datetime.utcfromtimestamp(x[self.field_x_index] / 1000).strftime(self.time_format) for x in
                         self.data.rows if x[field_group_index] == group_name]
                else:
                    x = [x[self.field_x_index] for x in self.data.rows if x[field_group_index] == group_name]

                ydata = []
                for y in self.field_y_index:
                    ydata.append(
                        [x[y] if x[y] is not None else 0 for x in self.data.rows if x[field_group_index] == group_name])
                for y in ydata:
                    if self.plot_type == "line":
                        if self.data.header[self.field_x_index] == "_time":
                            plt.plot(x, y, label=group_name, marker=self.marker, **self.extra_config)
                        else:
                            plt.plot(y, label=group_name, marker=self.marker, **self.extra_config)
                    elif self.plot_type == "bar":
                        plt.bar(x, y, label=group_name, marker=self.marker, **self.extra_config)
                    elif self.plot_type == "scatter":
                        plt.scatter(x, y, label=group_name, marker=self.marker, **self.extra_config)

        else:
            if self.data.header[self.field_x_index] == "_time":
                plt.date_form(self.time_format.replace("%", ""))
                x = [datetime.utcfromtimestamp(x[self.field_x_index] / 1000).strftime(self.time_format) for x in
                     self.data.rows]
            else:
                x = [x[self.field_x_index] for x in self.data.rows]
            ydata = []
            for y in self.field_y_index:
                ydata.append([x[y] if x[y] is not None else 0 for x in self.data.rows])
            for i in range(len(ydata)):
                y = ydata[i]
                if self.plot_type == "line":
                    if self.data.header[self.field_x_index] == "_time":
                        plt.plot(x, y, marker=self.marker, label=self.field_y[i], **self.extra_config)
                    else:
                        plt.plot(y, marker=self.marker, label=self.field_y[i], **self.extra_config)
                elif self.plot_type == "bar":
                    plt.bar(x, y, marker=self.marker, label=self.field_y[i], **self.extra_config)
                elif self.plot_type == "scatter":
                    plt.scatter(x, y, marker=self.marker, label=self.field_y[i], **self.extra_config)
        plt.grid(0, 1)  # 添加垂直网格线
        plt.plotsize(width, height)
        plt.theme(self.theme)
        return plt.build()

    def show(self):
        print(self.build(100, 100))


if __name__ == '__main__':
    table = OutputTable(["time", "value"], [[time.time() * 1000, 1], [time.time() * 1000, 2]])
    line_chart = Plot("time", "value", table, time_format="%Y-%m-%d %H:%M:%S",
                      title="Plot with Time on X-axis", )
    line_chart.show()
