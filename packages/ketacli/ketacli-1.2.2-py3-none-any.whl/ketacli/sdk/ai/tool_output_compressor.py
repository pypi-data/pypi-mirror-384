"""工具输出压缩

提供针对不同类型文本（JSON、表格、日志/通用文本）的结构化压缩，
在尽可能保留关键信息的前提下显著降低文本体积。
"""

import json
import csv
import io
import hashlib
import re
from typing import Any, Tuple


DEFAULT_MAX_CHARS = 8000
HEAD_TAIL_RATIO = (0.6, 0.4)  # 通用文本：前后片段比例


def _fingerprint(text: str) -> str:
    h = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
    return h[:16]


def _safe_str(val: Any, limit: int = 300) -> str:
    s = json.dumps(val, ensure_ascii=False) if not isinstance(val, str) else val
    s = s if isinstance(s, str) else str(s)
    if len(s) <= limit:
        return s
    return f"{s[: int(limit*0.7) ]}...{s[- int(limit*0.3) :]} (len={len(s)})"


def _is_likely_json(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    if (t.startswith("{") and t.endswith("}")) or (t.startswith("[") and t.endswith("]")):
        return True
    # 也可能是带前缀的JSON
    return False


def _try_parse_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def _compress_json_obj(obj: Any, max_items: int = 20, max_string: int = 300, depth: int = 0) -> Any:
    """结构化压缩JSON对象：
    - 限制数组展示项数量；
    - 长字符串截断；
    - 仅保留对象的前若干键；
    返回用于展示的压缩版对象（不保证还原），用于传给模型理解结构。
    """
    if isinstance(obj, dict):
        keys = list(obj.keys())
        result = {}
        limit = max(8, max_items // 2)
        for k in keys[:limit]:
            result[k] = _compress_json_obj(obj[k], max_items=max_items, max_string=max_string, depth=depth+1)
        if len(keys) > limit:
            result["__meta__"] = {
                "type": "object",
                "keys_total": len(keys),
                "keys_shown": keys[:limit]
            }
        return result
    elif isinstance(obj, list):
        shown = obj[:max_items]
        compressed = [
            _compress_json_obj(v, max_items=max_items//2 if max_items>4 else max_items, max_string=max_string, depth=depth+1)
            for v in shown
        ]
        meta = {
            "__meta__": {
                "type": "array",
                "items_total": len(obj),
                "items_shown": len(shown)
            }
        }
        return compressed + ([meta] if len(obj) > len(shown) else [])
    elif isinstance(obj, str):
        if len(obj) <= max_string:
            return obj
        return f"{obj[: int(max_string*0.6) ]}...{obj[- int(max_string*0.4) :]} (len={len(obj)})"
    else:
        # 数字/布尔/None 等直接返回
        return obj


def _detect_delimiter(line: str) -> str:
    for d in [",", "\t", "|", ";"]:
        if d in line:
            return d
    return ","


def _is_likely_table(text: str) -> bool:
    lines = text.splitlines()
    if len(lines) < 3:
        return False
    header = lines[0]
    delim = _detect_delimiter(header)
    # 简单判断：前几行列数一致
    try:
        cols = len(header.split(delim))
        samples = [len(l.split(delim)) for l in lines[1: min(6, len(lines))]]
        return cols >= 2 and all(c == cols for c in samples)
    except Exception:
        return False


def _compress_table(text: str, head_rows: int = 10, tail_rows: int = 5) -> str:
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return "(空表格)"
    header = lines[0]
    row_count = len(lines) - 1
    delim = _detect_delimiter(header)
    # 取样
    head = lines[1: 1 + min(head_rows, row_count)]
    tail = lines[max(1, len(lines) - tail_rows):]

    out = []
    out.append(f"[表格摘要] 行数: {row_count}, 分隔符: '{delim}'")
    out.append(f"列: {header}")
    if head:
        out.append("示例(前):")
        out.extend(head)
    if tail and (len(head) + len(tail) < row_count):
        out.append("示例(后):")
        out.extend(tail)
    if (len(head) + len(tail)) < row_count:
        out.append(f"... 其余 {row_count - len(head) - len(tail)} 行已省略")
    return "\n".join(out)


def _compress_generic_text(text: str, max_chars: int) -> str:
    # 去除超长连续空白、合并重复行
    lines = [re.sub(r"\s+", " ", l).strip() for l in text.splitlines()]
    freq = {}
    uniq_lines = []
    for l in lines:
        if not l:
            continue
        freq[l] = freq.get(l, 0) + 1
        if freq[l] == 1:
            uniq_lines.append(l)

    normalized = "\n".join(uniq_lines)
    if len(normalized) <= max_chars:
        return normalized

    # 截取前后片段
    head_len = int(max_chars * HEAD_TAIL_RATIO[0])
    tail_len = max(0, max_chars - head_len)
    head = normalized[:head_len]
    tail = normalized[-tail_len:] if tail_len > 0 else ""
    fp = _fingerprint(text)

    # 附加频次信息（保留高频前N条）
    top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
    top_str = ", ".join([f"{_safe_str(k, 80)} x{v}" for k, v in top]) if top else "无"

    return (
        f"[通用文本摘要] 原始长度: {len(text)}, 指纹: {fp}\n"
        f"高频片段: {top_str}\n"
        f"——前片段——\n{head}\n"
        f"——后片段——\n{tail}\n"
        f"(中间内容已省略)"
    )


def compress_tool_output(result: Any, max_chars: int = DEFAULT_MAX_CHARS) -> Tuple[str, bool]:
    """压缩工具执行结果。

    返回 (文本, 是否压缩)。当结果体积较小或不需要压缩时，返回原始文本且标记False。
    """
    # 统一为字符串
    text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
    if not isinstance(text, str):
        text = str(text)

    if len(text) <= max_chars:
        return text, False

    # 优先尝试JSON压缩
    if _is_likely_json(text):
        obj = _try_parse_json(text)
        if obj is not None:
            compressed_obj = _compress_json_obj(obj)
            prefix = text[:200]
            suffix = text[-200:]
            fp = _fingerprint(text)
            compact_json = json.dumps(compressed_obj, ensure_ascii=False, separators=(",", ":"))
            out = (
                f"[JSON摘要] 指纹: {fp}, 原始长度: {len(text)}\n"
                f"结构示例: {compact_json}\n"
                f"原始片段(前): {prefix}\n"
                f"原始片段(后): {suffix}\n"
                f"(中间JSON已省略)"
            )
            return out, True

    # 表格压缩（CSV/TSV/管道分隔等）
    if _is_likely_table(text):
        out = _compress_table(text)
        return out, True

    # 通用文本压缩
    out = _compress_generic_text(text, max_chars=max_chars)
    return out, True


def compress_if_large(result: Any, threshold: int = DEFAULT_MAX_CHARS) -> Tuple[str, bool]:
    """若结果超阈值则压缩，否则原样返回。"""
    text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
    if not isinstance(text, str):
        text = str(text)
    if len(text) <= threshold:
        return text, False
    return compress_tool_output(text, max_chars=threshold)