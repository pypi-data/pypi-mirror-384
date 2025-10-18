
【重要】日志数据搜索必须遵循的流程：
1. 调用 `get_docs("log_search_syntax")` 获取仓库的查询手册 
2. 调用 `get_docs("log_search_example")` 获取仓库的查询示例
3. 调用 `list_assets("repos")` 获取可用的数据仓库，查询时指定仓库名称
4. 通过 `get_repo_fields` 获取仓库的字段信息和结构
5. 基于实际的字段信息生成准确的SPL查询语句
6. 通过字段进行过滤时，可以通过 `search_data` 函数执行SPL `search2 repo="repository_name" | stats count() by <field_name> | fields <field_name>` 获取指定字段的取值范围。
7. 通过 `search_data` 函数执行SPL查询语句
