"""
Function Call 功能包装器

为ketacli的各种功能提供function call包装器。
"""

from .search_functions import *
from .data_functions import *
from .visualization_functions import *
from .asset_functions import *
from .script_functions import *
from .docs_functions import *

__all__ = [
    'register_all_functions'
]


def register_all_functions():
    """注册所有可用的function call函数"""
    # 导入时自动注册所有函数
    pass