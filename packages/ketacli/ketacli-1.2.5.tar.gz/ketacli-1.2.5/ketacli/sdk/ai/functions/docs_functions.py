"""
文档获取功能的Function Call包装器

提供读取SPL相关提示词文档的工具函数。
"""

import os
from ketacli.sdk.ai.function_call import function_registry


@function_registry.register(
    name="get_docs",
    description="获取SPL语法参考或步骤指导文档内容",
    parameters={
        "type": "object",
        "properties": {
            "_type": {
                "type": "string",
                "description": "文档类型，支持：log_search_syntax、metric_search_syntax、resource_search_steps、log_search_steps、metric_search_steps、log_search_example、metric_search_example",
                "enum": ["log_search_syntax", "metric_search_syntax", "resource_search_steps", "log_search_steps", "metric_search_steps", "log_search_example", "metric_search_example"],
            }
        },
        "required": ["_type"]
    }
)
def get_spl_syntax_reference(_type: str = "log") -> str:
    """获取SPL语法参考或步骤指导文档内容"""
    try:
        # 归一化类型并映射到具体文档
        current_dir = os.path.dirname(os.path.abspath(__file__))
        normalized = (_type or "").strip().lower()
        alias = {
            "logs": "log",
            "metrics": "metric",
            "repos": "log"  # 兼容提示中对仓库查询手册的调用
        }
        normalized = alias.get(normalized, normalized)

        doc_map = {
            "log_search_syntax": "log_search_syntax.md",
            "metric_search_syntax": "metric_search_syntax.md",
            "resource_search_steps": "resource_search_steps.md",
            "log_search_steps": "log_search_steps.md",
            "metric_search_steps": "metric_search_steps.md",
            "log_search_example": "log_search_example.md",
            "metric_search_example": "metric_search_example.md",
        }

        filename = doc_map.get(normalized)
        if not filename:
            raise ValueError(f"不支持的类型: {_type}")

        spl_doc_path = os.path.join(current_dir, "..", "prompts", filename)
        spl_doc_path = os.path.normpath(spl_doc_path)
        
        if os.path.exists(spl_doc_path):
            with open(spl_doc_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return f"{_type}文档未找到: {filename}"
    except Exception as e:
        return f"读取{_type}文档失败: {str(e)}"