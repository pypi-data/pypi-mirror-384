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

        # 4) 管道规则：where 等算子必须通过管道符引入（缺少时给出修复建议）
        try:
            stage_cmds = ["where"]
            for cmd in stage_cmds:
                if re.search(rf"\b{cmd}\b", first_segment, flags=re.IGNORECASE) and not re.match(rf"^\s*{cmd}\b", first_segment, flags=re.IGNORECASE):
                    for m in re.finditer(rf"\b{cmd}\b", first_segment, flags=re.IGNORECASE):
                        frag = first_segment[max(0, m.start()-30):min(len(first_segment), m.end()+30)]
                        corrected = first_segment[:m.start()].rstrip() + " | " + first_segment[m.start():]
                        violations.append((frag, corrected))
        except Exception:
            pass

        if violations:
            lines = [
                "SPL语法错误：字段值必须使用双引号或 where 等算子前缺少管道符",
                "建议修复片段："
            ]
            for frag, corrected in violations[:10]:
                lines.append(f"- {frag} -> {corrected}")
            if len(violations) > 10:
                lines.append(f"... 共发现 {len(violations)} 处")
            lines.append("规则：字段名用单引号，字段值用双引号（或三双引号）；where 等算子必须通过管道符 '|' 引入。")
            raise ValueError("\n".join(lines))
    except ValueError:
        # 违反规则时应向上抛出，让调用方中断执行并显示错误
        raise
    except Exception as e:
        # 校验实现异常时不影响正常查询，但记录到控制台便于排查
        console.print(f"[yellow]SPL语法校验异常：{str(e)}[/yellow]")



@function_registry.register(
    name="search_data",
    description=f"在KetaDB中搜索指标数据，支持SPL查询语言。请先使用`get_docs `函数获取SPL语法参考文档。",
    parameters={
        "type": "object",
        "properties": {
            "spl": {
                "type": "string",
                "description": "SPL查询语句，必须符合SPL语法规范。"
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
        },
        "required": ["spl"]
    }
)
def search_data(spl: str, limit: int = 100, format_type: str = "csv", output_file: Optional[str] = None) -> str:
    """搜索KetaDB中的数据"""

    # 先执行查询；仅在结果为空或查询/解析出错时触发语法校验并返回错误信息
    try:
        resp = search_spl(spl=spl, limit=limit)
    except Exception as se:
        # 查询失败时，尝试语法校验；若存在引号违规则返回更友好的错误提示
        try:
            validate_spl_value_quotes(spl)
        except ValueError as ve:
            return str(ve)
        return f"搜索失败: {str(se)}"

    # 构造结果输出对象可能抛错（返回结构异常等），同样走校验兜底
    try:
        result_output = search_result_output(resp)
    except Exception as pe:
        try:
            validate_spl_value_quotes(spl)
        except ValueError as ve:
            return str(ve)
        return f"结果解析失败: {str(pe)}"

    # 正常格式化输出（有数据时直接返回结果）
    if format_type not in ["json", "csv", "text"]:
        print("format_type not support, use csv")
        format_type = "csv"

    text = result_output.get_formatted_string(format_type)

    # 结果为空时才做语法校验，提示可能的引号问题；无违规则返回空结果文本
    try:
        rows_count = len(getattr(result_output, "rows", []) or [])
    except Exception:
        rows_count = 0
    if rows_count == 0:
        try:
            validate_spl_value_quotes(spl)
        except ValueError as ve:
            return str(ve)

    # 写文件输出
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

    if rows_count == limit:
        text += "\n[yellow]注意：返回数量等于limit，可能还有更多数据，建议调整limit参数获取更多数据或者通过span等参数调整采样[/yellow]"
    return text


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
    name="get_repo_fields",
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
                "description": "返回的字段数量",
                "default": 10
            }
        },
        "required": ["repository"]
    }
)
def get_repo_fields(repository: str, limit: int = 10) -> str:
    """获取指定仓库的字段信息"""
    get_fields_spl = f"search2 repo=\"{repository}\""
    
    try:
        # 构建SPL查询，将时间参数直接嵌入到查询中
        # 调用search_summary获取字段信息，不传递时间参数（因为已经在SPL中了）
        fields = list(search_summary(spl=get_fields_spl).keys())
        
        # 格式化返回结果
        field_values = {}
        for field in fields[:limit]:
            if field in ("_indexTime", "_time", "_raw", "_signature_id", "linenum", "repo"):
                continue
            get_fields_value_spl = f"""repo="{repository}"
| where isNotNull('{field}')    
| stats count() as countKey1 by '{field}' with count() as total, distinct('{field}', 0) as distinct
| sort 3 by countKey1
| eval value='{field}', key="{field}"
| fields key, value, countKey1
"""
            rsp = search_spl(spl=get_fields_value_spl)["rows"]

            for item in rsp:
                if item[0] not in field_values:
                    field_values[item[0]] = {}
                field_values[item[0]][item[1]] = str(item[2])[:50] 
        
        result = {
            "repository": repository,
            "fields": field_values
        }
        
        text = json.dumps(result, ensure_ascii=False, indent=2)
        return text
        
    except Exception as e:
        import traceback
        return f"获取仓库字段信息失败: {str(e)}\n{traceback.format_exc()}"
