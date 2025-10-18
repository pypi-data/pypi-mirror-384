# 指标计算
指标计算是指对时间序列数据进行统计分析，得到有意义的指标值。需要注意的是：
1. 指标计算不需要添加search2命令，直接在mstats命令中进行。
2. 指标计算也不需要指定repo参数，默认会对所有仓库进行计算。
3. 【非常重要】SPL编写时字段名通过单引号包裹，字段值通过双引号包裹，比如：`xxx | where 'host'="web-01"`
4. where关键字不支持in操作符：`xxx | where 'host' in ["web-01", "web-02"]` 是错误的，需要使用`xxx | where 'host'="web-01" OR 'host'="web-02"` 来替代。

## 快速总览

- 元数据查询：`show tag names`、`show tag "<name>"`、`show metric names`、`show metric tags`、`show series`
- 指标聚合：`mstats`（支持 `avg|min|max|sum|count|latest|earliest|sumRate|hperc`）
- 时间序列聚合：`rollup(metric, "avg|sum|count|max|min|increase|rate|resets|latest")`
- 直方图百分位：`hperc(pct, metric)`
- 速率计算：`rate [unit=<duration>] [<input> as <output>] [by <field>...]`
- Top 时间序列筛选：`topseries [type=avg|sum|min|max|last] [reverse=true] <N> [field] [by ...]`

## 数据模型要点

- `_time`：毫秒级时间戳；指标按时间序列组织
- `<tags>...`：任意标签（字符串或数组）
- `<fields>...`：指标值（双精度浮点）
- `_series`：时间序列唯一标识（由指标名、标签名和值组合定义）
- 常见内置标签：`repo`、`sourcetype`、`host`、`origin`

## 元数据查询（速用语法）

```
show tag names [| where like(name, "%memory%")]     # 列出标签名，并过滤包含"memory"的标签，过滤条件中的匹配值必须使用双引号
show tag "<name>"       # 列出指定标签值
show metric names [| where like(name, "%cpu%")]     # 列出指标名，并过滤包含"cpu"的指标，过滤条件中的匹配值必须使用双引号
show metric tags [| where like(name, "%cpu%")]      # 指标名 + 关联标签名数组，过滤条件中的匹配值必须使用双引号
show series [| where like(series, "%memory%")]      # 列出时间序列（JSON），过滤条件中的匹配值必须使用双引号
show rest "<url>" [jsonpath="xxx"] # 列出指定URL的JSON响应，过滤条件中的匹配值必须使用双引号
show sql "<sql>" # 执行SQL查询，返回JSON结果

```

## mstats（核心）

语法：
```
mstats [start|end|span|timeshift ...] <agg_expr>... [where ...] [by <field>...]
```
【注意】：start等时间参数必须紧跟mstats，不允许写到其它位置

- 修饰符：
  - `start`（含）：如 `-1d`、`1666550415000`
  - `end`（不含）：如 `now()`、绝对时间戳
  - `span`：时间聚合粒度（如 `auto`、`1m`、`30s`）
  - `timeshift`：时间偏移（如 `-1h`）
- 聚合表达式示例：
  - `avg('cpu_usage_idle')`
  - `avg('cpu_usage_idle' host="host_0" service="*")`
  - `avg('disk_used')/avg('disk_total')*100`
- 支持函数：`avg|min|max|sum|count|latest|earliest|sumRate|hperc`
- 输出：按`by`分组列 + `_time`（有 `span` 时）升序；值列为各聚合结果

示例：
```spl
# 过滤与时间范围
mstats start="-2h" end="-1h" avg('cpu_usage_idle' host="host_0")

# 时间偏移
mstats timeshift="-1h" avg('cpu_usage_idle' host="host_0")

# 分组与时间聚合
mstats start="-2h" span="1m" avg(cpu_usage_idle) as 'avg_cpu_usage_idle' by 'host'

# 多指标计算
mstats start="-2h" avg('disk_used')/avg('disk_total')*100 by 'host'
```

## rollup（时间序列内聚合）

签名：
```
rollup(<metric>, "avg|sum|count|max|min|increase|rate|resets|latest")
```

- 语义提示：
  - 选择 `rollup` 会改变聚合含义：`count` 统计时间序列数；未 `rollup` 时统计采样点数
  - `avg` 经过 `rollup` 后不受不同采样频率影响，更精准
- 示例：
```spl
# 每小时先按序列求均值，再求全局最大
mstats start="-2h" span="1h" max(rollup(cpu_usage_idle, "avg"))

# 计数增量与速率
mstats start="-2h" sum(rollup(span_requests_total, "increase"))
mstats start="-2h" sum(rollup(span_requests_total, "rate"))
```

## 直方图百分位 hperc

- 用途：对 histogram 类型指标求百分位（常用于时延）
- 规格要求：
  - 必须有 `le` 标签，且包含 `+Inf`
  - 值为累计计数（桶间累加）
  - 计算依赖 `rollup rate`，区间至少需 2 个采样点
- 签名：
```
histogramPercentile(long pct, double metric)
hperc(long pct, double metric)
```
- 示例：
```spl
mstats hperc(95, span_latency_bucket) as p95
```

## sumRate（全序列速率之和）

- 定义：对累计计数型指标，求所有时间序列每秒增速之和
- 等价：`mstats sum(rollup(<metric>, "rate"))`
- 签名：
```
sumRate(double metric)
```
- 示例：
```spl
mstats sumRate(span_requests_total)
```

## rate（增量变化率）

语法：
```
rate [unit=<duration>] [<input> as <output>] [by <field>...]
```

- `unit`：默认 `1s`，可用 `1h|1m|1d` 等
- `input`/`output`：输入字段与输出重命名，可省略交由引擎推导
- `by`：分组字段

示例：
```spl
# 每秒磁盘增量变化率（按 host 分组）
mstats avg('disk_used') by 'host' | rate

# 显式写法
mstats avg('disk_used') by 'host' | rate unit="1s" 'avg(disk_used)' by host

# 每小时变化率
mstats avg('disk_used') by 'host' | rate unit="1h"
```

## topseries（Top N 时间序列）

语法：
```
topseries [type="avg|sum|min|max|last"] [reverse=true|false] <N> [field] [by grouping]
```

- `type`：聚合方式（默认 `avg`）
- `reverse`：是否反转（默认降序）
- `N`：保留序列数（1–1000）
- `field`/`by`：可省略交由引擎推导（当且仅当唯一指标字段时）

示例：
```spl
# 结合 mstats
mstats start="-2h" span="10m" avg('cpu_usage_idle') by 'host' | topseries 5

# 显式字段与分组
mstats start="-2h" span="10m" avg(cpu_usage_idle) as '_value' by 'host' | topseries type="avg" reverse=true 5 '_value' by 'host'

# 结合 timechart
search2 start="-2h" repo="devops" cpu_usage_idle=* | timechart span="1h" avg('cpu_usage_idle') as '_value' by 'host' | topseries 5 '_value' by 'host'

# 过滤结果
mstats start="-2h" span="10m" avg('docker_memory_total') by 'host' | where host="10-0-1-154" | topseries 5

# 排序
mstats start="-2h" span="10m" avg('docker_memory_total') by 'host' | where host="10-0-1-154" | topseries 5 | sort by '_value' desc
```
