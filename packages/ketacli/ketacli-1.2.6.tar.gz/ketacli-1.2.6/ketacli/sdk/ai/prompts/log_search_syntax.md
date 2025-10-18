# SPL语法参考

## 基本语法结构
SPL采用管道式语法，优先使用search2引擎：
```
search2 repo="repository_name" <条件> | command1 | command2 | ...
```
### 字段引用规则
- 字段名通过单引号引用，字段值用双引号引用，如果值本身包含双引号，则用三双引号包裹。

### 时间语法
**重要：时间参数的位置规则**
- 时间参数（start、end）必须紧跟在search2命令之后
- 时间参数必须在repo参数和其他搜索条件之前
- 正确格式：`search2 start="时间" end="时间" repo="仓库名" 其他条件`

**示例：**
```spl
# 正确写法
search2 start="-3d" end="@d" repo="logs" 'status'=500

# 错误写法（时间参数位置错误）
search2 'repo'="logs" start="-3d" 'status'=500  # ❌ 错误
```

```
# 相对时间
start="-1h"          # 1小时前
start="-d@d" end="@d" # 昨天整天
start="-3d"          # 前3天（含今天）
start="-M@M" end="@M" # 上个月

# 时间单位：s(秒) m(分) h(小时) d(天) w(周) M(月) y(年)
# 对齐符号：@s @m @h @d @w @M @y
```

## 核心命令

### 搜索过滤
```spl
# 基础搜索
search2 start="-3d" end="@d" 'repo'="logs" 'status'=500 AND 'host'="web01" # 时间参数在repo之前，其他条件在最后
# 全文索引 
search2 'repo'="app_docker_log_tel" "error" # 搜索包含"error"的日志
search2 'repo'="app_docker_log_tel" "error" AND 'host'="web01" # 搜索包含"error"且主机为"web01"的日志
search2 'repo'="app_docker_log_tel" "error" OR "warning" # 搜索包含"error"或"warning"的日志

# 条件过滤，尽可能使用搜索时过滤，条件过滤的查询性能可能会受到影响
| where 'response_time' > 1000
```

### 字段操作
```spl

| fields 'timestamp', 'user', 'action' # 选择字段

| fields - '_raw', '_time'  # 排除字段

# 重命名
| rename 'user' as 'username'

# 计算字段
| eval 'response_sec' = 'response_time' / 1000
| eval 'full_name' = 'first_name' + " " + 'last_name'
| eval 'status_desc' = case('status'>=200 AND 'status'<300, "Success", 'status'>=400, "Error", 1=1, "Other")
| eval 'status_desc' = if('status'>=200 AND 'status'<300, "Success", "Error")
```

### 统计分析
```spl
# 基础统计
| stats count() as 'cnt' by 'status'
| stats avg('response_time'), max('response_time') by 'host'

# 时序分析
| timechart span="1h" count() as 'requests'
| timechart span="5m" avg('cpu_usage') by 'host', '_time'

# 常用统计函数
count(), sum(), avg(), min(), max(), distinct(), percentile(), earliest(), latest()
```

### 排序限制
```spl
| sort by 'response_time' asc  # 升序
| sort by 'timestamp' desc     # 降序
| limit 10
| dedup 'user'          # 去重
| top 10 'url'          # 前10
```

### 数据处理
```spl
# 正则提取
| rex field='_raw' "(?<method>\w+)\s+(?<url>\S+)"

# 类型转换
| convert num('response_time')

# 数组操作（SPL2）
| eval arr = [1,2,3]
| eval value = arr[0]
```

## 实用示例模板

### Web日志分析
```spl
# 错误分析
search2 repo="web_logs" 'status'>=400 
| stats count()  as 'cnt' by 'status', 'url' 
| sort by cnt desc

# 访问趋势
search2 start="-24h" 'repo'="web_logs"
| timechart span="1h" count() as 'cnt' by 'status'

# 慢请求分析
search2 'repo'="performance_logs" 'response_time'>1000
| stats avg('response_time') as 'avg_response_time', count() as 'cnt' by 'url'
| sort by 'avg_response_time'
```

### 异常检测
```spl
# 响应时间异常
search2 repo="api_logs"
| timechart span="5m" avg('response_time') as 'avg_time'
| eventstats avg(avg_time) as 'overall_avg', stdev(avg_time) as 'stdev'
| eval 'upper_bound' = 'overall_avg' + 2 * 'stdev'
| where 'avg_time' > 'upper_bound'
```

### 用户行为分析
```spl
# 用户活跃度
search2 start="-7d" repo="user_logs" 
| stats count() as 'actions', dc('session_id') as 'sessions' by 'user'
| eval 'avg_actions_per_session' = 'actions'/'sessions'
| sort by 'avg_actions_per_session'
```

## 性能优化要点

1. **必须使用repo参数**：`search2 repo="xxx"`，支持多仓库搜索，指定repo="*"即可
2. **尽早过滤**：使用全文索引进行快速过滤，避免全量扫描
3. **限制字段**：使用fields减少数据传输
4. **合理时间范围**：避免过大时间跨度
5. **分段调试**：复杂查询分步执行
6. **限制条数**：使用limit减少数据量

## 常用函数速查

### 字符串函数
- `len(str)` - 长度
- `substr(str, start, length)` - 子串
- `replace(str, old, new)` - 替换
- `match(str, regex)` - 正则匹配

### 数学函数
- `round(num, decimals)` - 四舍五入
- `ceil(num)`, `floor(num)` - 向上/向下取整
- `abs(num)` - 绝对值

### 时间函数
- `toReadableTime(time, format)` - 时间格式化
- `toTimestamp(X, TIMEFORMAT, ZoneOffset)` - 字符串转时间戳
- `now()` - 当前时间

### 条件函数
- `if(condition, true_value, false_value)` - 条件判断
- `case(condition1, value1, condition2, value2, default)` - 多条件
- `isnull(field)`, `isnotnull(field)` - 空值判断

## 调试技巧

1. 使用`| limit 1`快速测试，通过单条数据查看字段以及值
2. 逐步添加更多查询条件，如果条件过滤无数据，说明条件不匹配，需要调整条件

