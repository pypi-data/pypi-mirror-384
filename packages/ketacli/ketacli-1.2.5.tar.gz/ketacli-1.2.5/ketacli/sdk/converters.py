import datetime
import json
from typing import Any, Dict, List
from datetime import timezone, timedelta


def format_timestamp(value: Any, format: str = '%Y-%m-%d %H:%M:%S', tz: str = 'UTC') -> str:
    """
    格式化时间戳
    
    Args:
        value: 时间戳值（秒或毫秒）
        format: 时间格式字符串
        tz: 时区偏移，支持格式：'UTC', '+08:00', '-05:00' 或小时偏移如 '+8', '-5'

    Returns:
        str: 格式化后的时间字符串
    """
    if value is None:
        return ""
    
    try:
        # 处理不同类型的时间戳
        if isinstance(value, str):
            # 尝试解析字符串时间戳
            timestamp = float(value)
        elif isinstance(value, (int, float)):
            timestamp = float(value)
        else:
            return str(value)
        
        # 判断是秒还是毫秒时间戳
        if timestamp > 1e10:  # 毫秒时间戳
            timestamp = timestamp / 1000
        
        # 创建UTC时间对象
        utc_dt = datetime.datetime.fromtimestamp(timestamp, tz=timezone.utc)
        
        # 解析时区参数
        if tz.upper() == 'UTC':
            target_tz = timezone.utc
        elif tz.startswith(('+', '-')):
            # 处理 +08:00, -05:00 格式
            if ':' in tz:
                sign = 1 if tz[0] == '+' else -1
                hours, minutes = map(int, tz[1:].split(':'))
                offset = timedelta(hours=sign * hours, minutes=sign * minutes)
            else:
                # 处理 +8, -5 格式
                hours = int(tz)
                offset = timedelta(hours=hours)
            target_tz = timezone(offset)
        else:
            # 默认使用UTC
            target_tz = timezone.utc
        
        # 转换到目标时区
        local_dt = utc_dt.astimezone(target_tz)
        
        return local_dt.strftime(format)
    except (ValueError, OSError, OverflowError):
        return str(value)


def format_bytes(value: Any, unit: str = 'auto') -> str:
    """
    格式化字节大小
    
    Args:
        value: 字节数值
        unit: 单位 ('auto', 'B', 'KB', 'MB', 'GB', 'TB')
    
    Returns:
        str: 格式化后的大小字符串
    """
    if value is None:
        return ""
    
    try:
        bytes_value = float(value)
        
        if unit == 'auto':
            # 自动选择合适的单位
            units = ['B', 'KB', 'MB', 'GB', 'TB']
            unit_index = 0
            
            while bytes_value >= 1024 and unit_index < len(units) - 1:
                bytes_value /= 1024
                unit_index += 1
            
            if bytes_value >= 100:
                return f"{bytes_value:.0f} {units[unit_index]}"
            elif bytes_value >= 10:
                return f"{bytes_value:.1f} {units[unit_index]}"
            else:
                return f"{bytes_value:.2f} {units[unit_index]}"
        else:
            # 使用指定单位
            unit_map = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
            if unit in unit_map:
                converted_value = bytes_value / unit_map[unit]
                return f"{converted_value:.2f} {unit}"
            else:
                return str(value)
    except (ValueError, TypeError):
        return str(value)


def format_number(value: Any, precision: int = 2, thousands_sep: str = ',') -> str:
    """
    格式化数字
    
    Args:
        value: 数字值
        precision: 小数位数
        thousands_sep: 千位分隔符
    
    Returns:
        str: 格式化后的数字字符串
    """
    if value is None:
        return ""
    
    try:
        num_value = float(value)
        
        # 格式化数字
        if precision == 0:
            formatted = f"{int(num_value):,}"
        else:
            formatted = f"{num_value:,.{precision}f}"
        
        # 替换千位分隔符
        if thousands_sep != ',':
            formatted = formatted.replace(',', thousands_sep)
        
        return formatted
    except (ValueError, TypeError):
        return str(value)


def format_boolean(value: Any, true_text: str = '是', false_text: str = '否') -> str:
    """
    格式化布尔值
    
    Args:
        value: 布尔值
        true_text: True时显示的文本
        false_text: False时显示的文本
    
    Returns:
        str: 格式化后的布尔值字符串
    """
    if value is None:
        return ""
    
    if isinstance(value, bool):
        return true_text if value else false_text
    elif isinstance(value, str):
        lower_value = value.lower()
        if lower_value in ('true', '1', 'yes', 'on'):
            return true_text
        elif lower_value in ('false', '0', 'no', 'off'):
            return false_text
        else:
            return str(value)
    elif isinstance(value, (int, float)):
        return true_text if value != 0 else false_text
    else:
        return str(value)


def format_json(value: Any, indent: int = None) -> str:
    """
    格式化JSON
    
    Args:
        value: JSON值
        indent: 缩进空格数
    
    Returns:
        str: 格式化后的JSON字符串
    """
    if value is None:
        return ""
    
    try:
        if isinstance(value, str):
            # 尝试解析JSON字符串
            parsed = json.loads(value)
            return json.dumps(parsed, indent=indent, ensure_ascii=False)
        else:
            return json.dumps(value, indent=indent, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return str(value)


def format_truncate(value: Any, max_length: int = 50, suffix: str = '...') -> str:
    """
    截断文本
    
    Args:
        value: 文本值
        max_length: 最大长度
        suffix: 截断后缀
    
    Returns:
        str: 截断后的文本
    """
    if value is None:
        return ""
    
    text = str(value)
    if len(text) <= max_length:
        return text
    else:
        return text[:max_length - len(suffix)] + suffix


def format_enum(value: Any, enum_map: Dict[str, str]) -> str:
    """
    格式化枚举值
    
    Args:
        value: 枚举值
        enum_map: 枚举映射字典
    
    Returns:
        str: 格式化后的枚举值
    """
    if value is None:
        return ""
    
    str_value = str(value)
    return enum_map.get(str_value, str_value)

def format_duration(value: Any, src_unit: str = 's', dst_unit: str = 's') -> str:
    """
    格式化持续时间
    
    Args:
        value: 持续时间值
        src_unit: 源时间单位，可选值：s（秒）、m（分）、h（时）、d（天）、ms（毫秒）
        dst_unit: 目标时间单位，可选值：s（秒）、m（分）、h（时）、d（天）、ms（毫秒）  
    
    Returns:
        str: 格式化后的持续时间
    """
    if value is None:
        return ""
    
    try:
        duration = float(value)
        # 定义单位转换系数
        unit_factors = {
            's': {'s': 1, 'm': 1/60, 'h': 1/3600, 'd': 1/86400, 'ms': 1000},
            'm': {'s': 60, 'm': 1, 'h': 1/60, 'd': 1/1440, 'ms': 60000},
            'h': {'s': 3600, 'm': 60, 'h': 1, 'd': 1/24, 'ms': 3600000},
            'd': {'s': 86400, 'm': 1440, 'h': 24, 'd': 1, 'ms': 86400000}
        }
        
        # 定义单位显示文本
        unit_texts = {'s': '秒', 'm': '分', 'h': '时', 'd': '天', 'ms': '毫秒'}
        
        # 检查单位是否有效
        if src_unit not in unit_factors or dst_unit not in unit_factors[src_unit]:
            return str(value)
        
        # 获取转换系数和显示单位
        factor = unit_factors.get(src_unit, {}).get(dst_unit, 1)
        unit_text = unit_texts.get(dst_unit, '秒')
        
        # 计算并返回结果
        return f"{duration * factor:.2f}{unit_text}"
    except (ValueError, TypeError):
        return str(value)

# 转换函数注册表
CONVERTER_REGISTRY = {
    'format_timestamp': format_timestamp,
    'format_duration': format_duration,
    'format_bytes': format_bytes,
    'format_number': format_number,
    'format_boolean': format_boolean,
    'format_json': format_json,
    'format_truncate': format_truncate,
    'format_enum': format_enum,
}


def apply_field_converter(value: Any, convert_config: Dict) -> str:
    """
    应用字段转换器
    
    Args:
        value: 原始值
        convert_config: 转换配置
    
    Returns:
        str: 转换后的值
    """
    if not convert_config or 'function' not in convert_config:
        return str(value) if value is not None else ""
    
    function_name = convert_config['function']
    converter_func = CONVERTER_REGISTRY.get(function_name)
    
    if not converter_func:
        # 如果找不到转换函数，返回原始值
        return str(value) if value is not None else ""
    
    try:
        # 解析参数
        args = convert_config.get('args', [])
        kwargs = {}
        
        # 处理参数列表，支持字典格式的参数
        for arg in args:
            if isinstance(arg, dict):
                # 跳过field参数，因为value已经是字段值
                for key, val in arg.items():
                    if key != 'field':
                        kwargs[key] = val
            else:
                # 简单参数，暂时忽略
                pass
        
        # 调用转换函数
        return converter_func(value, **kwargs)
    except Exception as e:
        # 转换失败时返回原始值
        return str(value) if value is not None else ""