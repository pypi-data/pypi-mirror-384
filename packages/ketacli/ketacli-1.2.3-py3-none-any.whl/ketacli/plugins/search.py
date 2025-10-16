"""
搜索相关命令模块
"""
import sys
import time
from datetime import datetime
from mando import command, arg
from rich.console import Console
from rich.live import Live
from rich.progress import Progress
from concurrent.futures import ProcessPoolExecutor
from ketacli.sdk.base.search import search_spl, search_spl_meta, search_pql
from ketacli.sdk.output.output import search_result_output
from ketacli.sdk.output.format import format_table

console = Console()


@command
@arg("format", type=str,
     completer=lambda prefix, **kwd: [x for x in ["table", "text", "json", "csv", "html", "latex"] if
                                      x.startswith(prefix)])
def search(spl, start=None, end=None, limit=100, format=None, raw=False, watch=False, interval=3.0):
    """Search spl from ketadb

    :param spl: The spl query
    :param --start: The start time. Time format "2024-01-02 10:10:10"
    :param --end: The start time. Time format "2024-01-02 10:10:10"
    :param -l, --limit: The limit size of query result
    :param -f, --format: The output format, table|text|json|csv|html|latex
    :param --raw: Prettify the time field or output the raw timestamp, if specified, output the raw format
    :param -w, --watch: Watch the resource change
    :param --interval: refresh the resource change
    """
    if start is not None:
        start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
    if end is not None:
        end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')

    def generate_table():
        resp = search_spl(spl=spl, start=start, end=end, limit=limit)
        return format_table(search_result_output(resp), format, not raw)

    if watch:
        with Live(generate_table(), console=console, refresh_per_second=1) as live:
            while True:
                try:
                    table = generate_table()
                    live.update(table)
                    time.sleep(interval)
                except KeyboardInterrupt:
                    live.stop()
                    sys.exit()

    else:
        table = generate_table()
        if table is None:
            console.print(f"we cannot find any data")
        else:
            console.print(table, overflow="fold")


@command
def benchmark(type="spl", query=None, start: float = 0.0, end: float = None, limit=None, cnt=1, workers=1, base_url="",
              window=0):
    """benchmark spl from ketadb
    :param spl: The spl query
    :param --start: The start time
    :param --end: The start time
    :param -l, --limit: The limit size of query result
    :param -c, --cnt: The count of benchmark
    :param -w, --workers: The count of workers
    :param -b, --base_url: The base url of pql
    :param --window: The window of benchmark
    """

    result = {
        "type": type,
        "query": query,
        "cnt": cnt,
        "results": [],
        "waiting": 0,
        'request_cnt': cnt
    }
    futures = []
    started = time.time()
    if not end:
        end = time.time()
    if isinstance(query, str):
        querys = [query]
    elif isinstance(query, list):
        querys = query
    else:
        raise Exception("query must be str or list")
    with Progress() as progress:
        if window:
            new_cnt = int((end - start) / window) * cnt * len(querys)
            result['request_cnt'] = new_cnt
        else:
            new_cnt = cnt * len(querys)
            result['request_cnt'] = new_cnt
        task = progress.add_task(f"[green]Benchmarking total: {new_cnt}...", total=new_cnt)
        with ProcessPoolExecutor(max_workers=workers) as executor:

            if not window:
                for _ in range(cnt):
                    for query in querys:
                        if type == "spl":
                            futures.append(
                                executor.submit(search_spl_meta, spl=query, start=start, end=end, limit=limit))
                        elif type == "pql":
                            futures.append(
                                executor.submit(search_pql, base_url=base_url, pql=query, start=start, end=end,
                                                limit=limit))
            else:

                while True:
                    new_end = start + window
                    print(datetime.fromtimestamp(start).strftime('%d-%H:%M:%S'),
                          datetime.fromtimestamp(new_end).strftime('%H:%M:%S'), )
                    if new_end > end:
                        break
                    for query in querys:
                        if type == "spl":
                            for _ in range(cnt):
                                futures.append(
                                    executor.submit(search_spl_meta, spl=query, start=start, end=new_end, limit=limit))
                        elif type == "pql":
                            for _ in range(cnt):
                                futures.append(
                                    executor.submit(search_pql, base_url=base_url, pql=query, start=start, end=new_end,
                                                    limit=limit))
                    start += window

            for future in futures:
                resp = future.result()
                result["results"].append(resp)
                result["avg_duration"] = sum([x["duration"] for x in result["results"]]) / len(result["results"])
                progress.update(task, advance=1)
    result["waiting"] = time.time() - started
    result["total_duration"] = round(sum([x["duration"] for x in result["results"] if "duration" in x]))
    result['totalSize'] = sum([x["resultSize"] for x in result["results"] if "resultSize" in x])
    console.print(result, markup=False)


@command
def benchmark_for_file(type='spl', file_path=None, start=0, end=0, limit=None, cnt=1, workers=1, base_url="",
                       window=0):
    """从文件批量执行性能测试
    通过读取包含多个查询语句的文件，进行批量压力测试

    :param type: 测试类型 spl/pql
    :param file_path: 包含查询语句的文件路径，每行一个查询
    :param start: 测试时间范围起始时间戳
    :param end: 测试时间范围结束时间戳
    :param limit: 单次查询结果限制数
    :param cnt: 每个查询的重复测试次数
    :param workers: 并发工作进程数
    :param base_url: PQL服务基础地址（当type=pql时生效）
    :param window: 时间窗口大小（秒），0表示不分割时间范围

    示例：
    ketacli benchmark_for_file --file queries.txt --type spl --workers 4 --cnt 10
    """
    with open(file_path, "r") as f:
        querys = f.readlines()

    benchmark(type=type, query=querys, start=start, end=end, limit=limit, cnt=cnt, workers=workers, base_url=base_url,
              window=window)