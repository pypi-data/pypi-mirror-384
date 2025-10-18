
【重要】指标数据查询流程：
1. 通过 `search_data` 函数执行SPL `show metric names | where like(name, "%<指标名称关键词>%")` 获取可用的指标列表，找到最相关的指标，%是通配符，模糊搜索时注意不要漏掉%%包裹关键词，另请注意使用双引号包裹。
2. 通过 `search_data` 函数执行SPL `show metric tags | where name="<指标key>"` 获取指标的标签信息
3. 通过 `get_docs("metrics")` 获取指标查询语法
4. 通过 `get_docs("metric_search_example")` 获取指标查询示例
5. 基于指标文档，以及获取的指标标签，生成符合SPL语法的查询语句  
6. 通过 `search_data` 函数执行SPL查询语句
