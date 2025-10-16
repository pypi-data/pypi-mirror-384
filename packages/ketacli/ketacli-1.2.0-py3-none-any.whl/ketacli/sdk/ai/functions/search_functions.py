"""
搜索功能的Function Call包装器
"""

import json
import os
from datetime import datetime
import re
from typing import Optional, Union
from ketacli.sdk.ai.function_call import function_registry
from ketacli.sdk.ai.client import AIClient
from ketacli.sdk.base.search import search_spl, search_spl_meta, search_summary
from ketacli.sdk.output.output import search_result_output, list_output
from ketacli.sdk.output.format import format_table
from ketacli.sdk.request.list import list_assets_request
from ketacli.sdk.base.client import request_get
from rich.console import Console

console = Console(markup=False)


def validate_spl_value_quotes(spl: str) -> None:
    """通用校验：SPL 中所有出现“字段值”的场景必须使用双引号。

    原则：
    - 字段名用单引号（例如：'host'）。
    - 字段值用双引号（例如："10-0-1"，包含双引号时可用三双引号）。
    - 校验范围覆盖：
      * search/search2 主段中的条件（如 repo、start、end 及任意 key=value）
      * where 子句中的比较、like/contains/match、in/not in 等
      * 其他命令中的赋值（如 span="10m" 等）
    - 避免误报：允许函数对字段名的单引号（如 avg('field')）、by/fields/as 后的字段名单引号、作为左值的单引号字段名（'field'=...）。
    出现违规时抛出 ValueError 并提供修复建议片段。
    """
    try:
        violations = []

        # 1) 全局：任何 key='value' 的赋值均违规
        for m in re.finditer(r"\b[\w.]+\s*=\s*'[^']*'", spl):
            frag = m.group(0)
            corrected = re.sub(r"=\s*'([^']*)'", r'="\1"', frag)
            violations.append((frag, corrected))

        # 2) where 子句：函数与比较操作的值不得为单引号
        for segment in spl.split("|"):
            seg = segment.strip()
            if not seg:
                continue
            is_where = seg.lower().startswith("where")
            expr = seg[len("where"):].strip() if is_where else seg

            # like/contains/match 第二个参数不应为单引号
            for pattern in [
                r"\blike\s*\(\s*[^,]+,\s*'[^']*'\s*\)",
                r"\bcontains\s*\(\s*[^,]+,\s*'[^']*'\s*\)",
                r"\bmatch\s*\(\s*[^,]+,\s*'[^']*'\s*\)"
            ]:
                for m in re.finditer(pattern, expr, flags=re.IGNORECASE):
                    frag = m.group(0)
                    # 仅替换第二个参数的引号，保留字段名的单引号
                    corrected = re.sub(
                        r"\b(like|contains|match)\s*\(\s*([^,]+),\s*'([^']*)'\s*\)",
                        r'\1(\2, "\3")',
                        frag,
                        flags=re.IGNORECASE,
                    )
                    violations.append((frag, corrected))

            # in/not in 列表值不得为单引号
            for m in re.finditer(r"\b(?:in|not\s+in)\s*\(\s*'[^']*'(?:\s*,\s*'[^']*')*\s*\)", expr, flags=re.IGNORECASE):
                frag = m.group(0)
                corrected = re.sub(r"'([^']*)'", r'"\1"', frag)
                violations.append((frag, corrected))

            # 等值/不等比较右值不得为单引号
            for m in re.finditer(r"(?:=|!=|<>|>=|<=|=~|!~|~)\s*'[^']*'", expr):
                frag = m.group(0)
                corrected = frag.replace("'", '"')
                violations.append((frag, corrected))

        # 3) search/search2 主段：裸单引号文本（自由文本值）不得使用单引号
        first_segment = spl.split("|")[0].strip()
        if first_segment.lower().startswith(("search2", "search")):
            for m in re.finditer(r"'[^']*'", first_segment):
                frag = m.group(0)
                start, end = m.start(), m.end()
                # 允许的上下文：函数参数、by/fields/as 后的字段名、作为左值的字段名（后面紧跟=）
                prefix = first_segment[max(0, start-30):start]
                suffix = first_segment[end:min(len(first_segment), end+10)]

                allowed_prefix_keywords = ["by", "fields", "as"]
                if any(re.search(rf"\b{kw}\s*$", prefix) for kw in allowed_prefix_keywords):
                    continue
                if re.search(r"\([\s]*$", prefix):  # 函数左括号紧邻
                    continue
                if re.match(r"^\s*=", suffix):  # 左值场景：'field'=
                    continue

                # 其他场景视为自由文本值，应改为双引号
                corrected = frag.replace("'", '"')
                violations.append((frag, corrected))

        if violations:
            lines = [
                "SPL语法错误：字段值必须使用双引号，检测到以下单引号值：",
                "建议修复片段："
            ]
            for frag, corrected in violations[:10]:
                lines.append(f"- {frag} -> {corrected}")
            if len(violations) > 10:
                lines.append(f"... 共发现 {len(violations)} 处")
            lines.append("规则：字段名用单引号，字段值用双引号（或三双引号）。")
            raise ValueError("\n".join(lines))
    except ValueError:
        # 违反规则时应向上抛出，让调用方中断执行并显示错误
        raise
    except Exception as e:
        # 校验实现异常时不影响正常查询，但记录到控制台便于排查
        console.print(f"[yellow]SPL语法校验异常：{str(e)}[/yellow]")



@function_registry.register(
    name="search_data_for_log",
    description=f"在KetaDB中搜索日志数据，支持SPL查询语言。请先使用`get_docs _type=log_search_syntax`函数获取SPL语法参考文档。",
    parameters={
        "type": "object",
        "properties": {
            "spl": {
                "type": "string",
                "description": "SPL查询语句，必须符合SPL语法规范。请先使用`get_docs _type=log_search_syntax`函数获取SPL语法参考文档。"
            },
            "limit": {
                "type": "integer",
                "description": "返回结果数量限制",
                "default": 100
            },
            "format_type": {
                "type": "string",
                "description": "输出格式 (text, json, csv)",
                "default": "csv"
            },
            "output_file": {
                "type": "string",
                "description": "输出文件路径；提供则将结果写入文件"
            }
        },
        "required": ["spl"]
    }
)
@function_registry.register(
    name="search_data_for_metric",
    description=f"在KetaDB中搜索指标数据，支持SPL查询语言。请先使用`get_docs _type=metric_search_syntax`函数获取SPL语法参考文档。",
    parameters={
        "type": "object",
        "properties": {
            "spl": {
                "type": "string",
                "description": "SPL查询语句，必须符合SPL语法规范。请先使用`get_docs _type=metric_search_syntax`函数获取SPL语法参考文档。"
            },
            "limit": {
                "type": "integer",
                "description": "返回结果数量限制",
                "default": 100
            },
            "format_type": {
                "type": "string",
                "description": "输出格式 (text, json, csv)",
                "default": "csv"
            },
            "output_file": {
                "type": "string",
                "description": "输出文件路径；提供则将结果写入文件"
            },
            "search_type": {
                "type": "string",
                "description": "搜索类型，log或metric或show",
                "enum": ["log", "metric", "show", "auto"],
                "default": "auto"
            }
        },
        "required": ["spl", "search_type"]
    }
)
def search_data(spl: str, limit: int = 100, format_type: str = "csv", output_file: Optional[str] = None, search_type: str = "auto") -> str:
    """搜索KetaDB中的数据"""
    if search_type not in ["log", "metric", "show", "auto"]:
        raise ValueError(f"不支持的搜索类型: {search_type}")
    spl_prefix = spl.strip().lower().split(" ")[0]
    if search_type == "log" and spl_prefix not in ["search2", "search"]:
        raise ValueError("日志搜索SPL语句必须以search2开头")
    
    if search_type == "metric" and spl_prefix not in ["mstats"]:
        if spl_prefix == "show":
            raise ValueError(f"指标搜索SPL语句必须以mstats开头，当前指令是{spl_prefix}，请将search_type设置为show")
        else:
            raise ValueError(f"指标搜索SPL语句必须以mstats开头，当前指令是{spl_prefix}，请将search_type设置为metric")

    if search_type == "show" and spl_prefix not in ["show"]:
        raise ValueError("展示搜索SPL语句必须以show开头")
        
    try:
        # 语法校验：确保 where 子句中的字段值使用双引号
        validate_spl_value_quotes(spl)
        resp = search_spl(spl=spl, limit=limit)
        result_output = search_result_output(resp)
        
        if format_type not in ["json", "csv", "text"]:
            print("format_type not support, use csv")
            format_type = "csv"
        
        text = result_output.get_formatted_string(format_type)
        if output_file and isinstance(output_file, str) and len(output_file.strip()) > 0:
            try:
                dir_name = os.path.dirname(output_file)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(text)
                return f"[green]搜索结果已写入: {output_file}[/green]"
            except Exception as fe:
                return f"[yellow]写入文件失败: {str(fe)}[/yellow]"
        if len(result_output.rows) == limit:
            text += "\n[yellow]注意：返回数量等于limit，可能还有更多数据，建议调整limit参数获取更多数据或者通过span等参数调整采样[/yellow]"
        return text
    except Exception as e:
        raise e


@function_registry.register(
    name="search_metadata",
    description="获取SPL查询的元数据信息",
    parameters={
        "type": "object",
        "properties": {
            "spl": {
                "type": "string",
                "description": "SPL查询语句"
            },
            "output_file": {
                "type": "string",
                "description": "输出文件路径；提供则将结果写入文件"
            }
        },
        "required": ["spl"]
    }
)
def search_metadata(spl: str, output_file: Optional[str] = None) -> str:
    """获取SPL查询的元数据"""
    try:
        if "show" in spl:
            return "show 命令不支持获取元数据，请直接使用search_data_for_metric函数获取指标元数据"
        meta = search_spl_meta(spl)
        text = json.dumps(meta, ensure_ascii=False, indent=2)
        if output_file and isinstance(output_file, str) and len(output_file.strip()) > 0:
            try:
                dir_name = os.path.dirname(output_file)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(text)
                console.print(f"[green]元数据已写入: {output_file}[/green]")
            except Exception as fe:
                console.print(f"[yellow]写入文件失败: {str(fe)}[/yellow]")
        return text
    except Exception as e:
        return f"获取元数据失败: {str(e)}"


@function_registry.register(
    name="get_repository_fields",
    description=f"""获取指定仓库的字段信息和数据摘要。""",
    parameters={
        "type": "object",
        "properties": {
            "repository": {
                "type": "string",
                "description": "目标仓库名称"
            },
            "limit": {
                "type": "integer",
                "description": "返回结果数量限制",
                "default": 100
            },
            "output_file": {
                "type": "string",
                "description": "输出文件路径；提供则将结果写入文件"
            }
        },
        "required": ["repository"]
    }
)
def get_repository_fields(repository: str, limit: int = 100, output_file: Optional[str] = None) -> str:
    """获取指定仓库的字段信息"""
    spl = f"search2 repo=\"{repository}\""
    try:
        # 构建SPL查询，将时间参数直接嵌入到查询中
        # 调用search_summary获取字段信息，不传递时间参数（因为已经在SPL中了）
        fields = list(search_summary(spl=spl, limit=limit).keys())
        
        # 格式化返回结果
        result = {
            "repository": repository,
            "fields": fields
        }
        
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if output_file and isinstance(output_file, str) and len(output_file.strip()) > 0:
            try:
                dir_name = os.path.dirname(output_file)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(text)
                console.print(f"[green]仓库字段信息已写入: {output_file}[/green]")
            except Exception as fe:
                console.print(f"[yellow]写入文件失败: {str(fe)}[/yellow]")
        return text
        
    except Exception as e:
        return f"获取仓库字段信息失败: {str(e)}"


def ai_match_repositories(search_requirement: str, repo_list: list) -> list:
    """
    使用AI智能匹配最相关的仓库
    
    Args:
        search_requirement: 用户搜索需求
        repo_list: 可用仓库列表
        
    Returns:
        匹配的仓库列表，按相关度排序
    """
    try:
        # 构建AI提示词
        prompt = f"""
你是一个数据仓库匹配专家。请根据用户的搜索需求，从给定的仓库列表中选择最相关的仓库。

用户搜索需求：{search_requirement}

可用仓库列表：
{json.dumps(repo_list, ensure_ascii=False, indent=2)}

请分析用户需求，选择最相关的1-3个仓库，并按相关度排序。

返回格式要求：
- 只返回JSON格式的仓库列表
- 每个仓库包含name、description字段
- 按相关度从高到低排序
- 如果没有明确匹配的仓库，选择最可能相关的仓库

示例返回格式：
[
  {{"name": "web_logs", "description": "网站访问日志"}},
  {{"name": "api_logs", "description": "API接口调用日志"}}
]
"""
        
        client = AIClient()
        response = client.chat(prompt)
        
        # 解析AI响应
        try:
            matched_repos = json.loads(response.content)
            if isinstance(matched_repos, list) and len(matched_repos) > 0:
                console.print(f"[green]AI匹配到 {len(matched_repos)} 个相关仓库: {[r['name'] for r in matched_repos]}[/green]")
                return matched_repos
        except json.JSONDecodeError:
            console.print(f"[yellow]AI响应解析失败，使用备用匹配逻辑[/yellow]")
    
    except Exception as e:
        console.print(f"[yellow]AI仓库匹配失败: {str(e)}，使用备用匹配逻辑[/yellow]")
    
    return matched_repos


def ai_analyze_fields_and_generate_spl(search_requirement: str, repo_info: dict, time_range: str, limit: int) -> str:
    """
    使用AI分析字段信息并生成SPL查询
    
    Args:
        search_requirement: 用户搜索需求
        repo_info: 仓库信息，包含字段信息
        time_range: 时间范围
        limit: 结果限制
        
    Returns:
        生成的SPL查询语句
    """

    # 构建AI提示词
    prompt = f"""
你是一个SPL查询专家。请根据用户的搜索需求和仓库字段信息，生成准确的SPL查询语句。

用户搜索需求：{search_requirement}

仓库信息：
{json.dumps(repo_info, ensure_ascii=False, indent=2)}

时间范围：{time_range}
结果限制：{limit}

SPL语法规范：
{get_spl_syntax_reference()}

请分析用户需求，识别关键的过滤条件，并生成符合SPL语法的查询语句。

注意事项：
1. 必须使用search2命令开始
2. 时间范围使用start参数
3. 仓库名称使用repo参数
4. 根据字段信息选择合适的过滤条件
5. 使用where子句进行条件过滤
6. 最后添加limit限制结果数量

只返回SPL查询语句，不要包含其他解释文字。

示例格式：
search2 start="-1h" repo="web_logs" | where status_code="500" | limit 100
"""
    
    client = AIClient()
    response = client.chat(prompt)
    
    # 清理响应内容，移除可能的markdown格式
    spl_query = response.content.strip()
    if spl_query.startswith('```'):
        lines = spl_query.split('\n')
        spl_query = '\n'.join([line for line in lines if not line.startswith('```')])
        spl_query = spl_query.strip()
    
    console.print(f"[green]AI生成的SPL查询: {spl_query}[/green]")
    return spl_query
        
    


# @function_registry.register(
#     name="smart_search",
#     description=f"""智能搜索功能，自动执行完整的搜索流程：
# 1. 获取所有可用的数据仓库列表
# 2. 根据用户需求匹配合适的仓库
# 3. 获取匹配仓库的字段信息
# 4. 根据仓库信息、字段信息和SPL语法生成最终的SPL查询
# 5. 执行搜索并返回结果

# 重要：此功能会自动处理整个搜索流程，用户只需要描述搜索需求即可。

# SPL语法参考：
# {get_spl_syntax_reference()}""",
#     parameters={
#         "type": "object",
#         "properties": {
#             "search_requirement": {
#                 "type": "string",
#                 "description": "用户的搜索需求描述，例如：'查找最近1小时的web访问日志中状态码为500的记录'"
#             },
#             "time_range": {
#                 "type": "string",
#                 "description": "时间范围，SPL时间格式如 '-1h', '-3d', '-7d' 等",
#                 "default": "-1h"
#             },
#             "limit": {
#                 "type": "integer",
#                 "description": "返回结果数量限制",
#                 "default": 100
#             },
#             "format_type": {
#                 "type": "string",
#                 "description": "输出格式 (text, json, csv)",
#                 "default": "csv"
#             }
#         },
#         "required": ["search_requirement"]
#     }
# )
def smart_search(search_requirement: str, time_range: str = "-1h", 
                limit: int = 100, format_type: str = "csv", output_file: Optional[str] = None) -> str:
    """智能搜索功能，自动执行完整的搜索流程"""
    try:
        # 步骤1: 获取所有可用的数据仓库列表
        console.print("[bold blue]步骤1: 获取数据仓库列表...[/bold blue]")
        req = list_assets_request("repo", pageSize=limit)
        resp = request_get(req["path"], req["query_params"],
                           req["custom_headers"]).json()
        repo_output = list_output("repo", None, resp)
        
        if not repo_output:
            return "未找到可用的数据仓库"
        
        # 提取仓库信息
        repo_list = []
        if hasattr(repo_output, 'rows'):
            for row in repo_output.rows:
                if isinstance(row, list) and len(row) >= 2:
                    repo_name = str(row[0])
                    repo_desc = str(row[1]) if len(row) > 1 else ""
                    repo_list.append({"name": repo_name, "description": repo_desc})
        
        if not repo_list:
            return "无法解析仓库列表信息"
        
        console.print(f"[green]找到 {len(repo_list)} 个数据仓库[/green]")
        
        # 步骤2: 使用AI分析用户需求，智能匹配相关仓库
        console.print("[bold blue]步骤2: 使用AI分析用户需求，智能匹配相关仓库...[/bold blue]")
        
        matched_repos = ai_match_repositories(search_requirement, repo_list)
        
        # 步骤3: 获取匹配仓库的字段信息
        console.print("[bold blue]步骤3: 获取仓库字段信息...[/bold blue]")
        
        all_fields = {}
        for repo in matched_repos[:2]:  # 限制最多分析2个仓库以避免过多输出
            try:
                # 构建基础SPL查询
                base_spl = f'search2 start="{time_range}" repo="{repo["name"]}" | limit 10'
                
                # 调用search_summary获取字段信息
                fields_result = search_summary(base_spl)
                all_fields[repo["name"]] = {
                    "description": repo["description"],
                    "fields": fields_result
                }
                console.print(f"[green]已获取 {repo['name']} 的字段信息[/green]")
            except Exception as e:
                console.print(f"[yellow]获取 {repo['name']} 字段信息失败: {str(e)}[/yellow]")
        
        # 步骤4: 使用AI分析字段信息并生成SPL查询
        console.print("[bold blue]步骤4: 使用AI分析字段信息并生成SPL查询...[/bold blue]")
        
        # 使用AI生成SPL查询
        spl_query = ai_analyze_fields_and_generate_spl(search_requirement, all_fields, time_range, limit)
        
        # 步骤5: 执行搜索
        console.print("[bold blue]步骤5: 执行搜索...[/bold blue]")
        
        # 执行搜索（先进行SPL语法校验）
        validate_spl_value_quotes(spl_query)
        resp = search_spl(spl=spl_query, limit=limit)
        result_output = search_result_output(resp)
        if format_type not in ["json", "csv", "text"]:
            print("format_type not support, use csv")
            format_type = "csv"
        
        # 格式化输出
        text = result_output.get_formatted_string(format=format_type)
        if output_file and isinstance(output_file, str) and len(output_file.strip()) > 0:
            try:
                dir_name = os.path.dirname(output_file)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(text)
                console.print(f"[green]智能搜索结果已写入: {output_file}[/green]")
            except Exception as fe:
                console.print(f"[yellow]写入文件失败: {str(fe)}[/yellow]")
        return text
        
        
    except Exception as e:
        return f"智能搜索失败: {str(e)}"