from faker import Faker
from jinja2 import Environment, StrictUndefined
from jinja2.exceptions import UndefinedError
from rich.console import Console
import random
import time
import functools

# 创建全局Faker实例，避免重复创建
faker = Faker()
faker_zh = Faker(locale='zh_CN')

# 模板缓存，避免重复解析相同的模板
_template_cache = {}


def is_key(key, value_map=None):
    """精确匹配是否存在key

    Args:
        key (str): 字符串key
        value_map (dict, optional): 是否存在该key的字典. Defaults to {}.

    Returns:
        _type_: 最终的key，如果不存在则为None
    """
    if value_map is None:
        value_map = {}
    newkey = key.lower()
    if newkey in value_map:
        return newkey
    return None


def is_fuzzy_key(key, value_map=None):
    """
    检查key或者key的复数形式在map中，并返回最终map中的key
    """
    if value_map is None:
        value_map = {}
    newkey = key.lower()
    if newkey in value_map:
        return newkey
    if newkey.endswith('s'):
        newkey = newkey[:-1]
    else:
        newkey = newkey + 's'
    if newkey in value_map:
        return newkey
    return None


def parse_url_params(url_query):
    params = url_query.lstrip('?')  # 移除开头的问号
    pairs = params.split(',')  # 将参数对分割
    result = {}

    for pair in pairs:
        key, value = pair.split('=')  # 分割键和值
        try:
            value = int(value) if '.' not in value else float(value)  # 尝试转换为整数或浮点数
        except ValueError:
            pass  # 如果转换失败，保留原始字符串值
        result[key] = value  # 添加到结果字典
    return result


class Template:
    # 类级别的缓存，用于存储已编译的模板
    _template_cache = {}
    # 类级别的Faker实例缓存
    _faker_instances = {}

    def __init__(self, template):
        self.template = template
        
        # 使用缓存避免重复创建相同的模板
        if template in Template._template_cache:
            self.env = Template._template_cache[template]['env']
            self.temp = Template._template_cache[template]['temp']
        else:
            # 优化Jinja2环境配置以提高渲染速度
            self.env = Environment(
                undefined=StrictUndefined,
                cache_size=1024,  # 增加缓存大小
                auto_reload=False,  # 禁用自动重载，提高性能
                optimized=True,  # 启用优化
                autoescape=False,  # 禁用自动转义，除非需要HTML安全
                # trim_blocks=True,  # 移除块后的第一个换行符
                # lstrip_blocks=True  # 移除块前的空白
            )
            self.temp = self.env.from_string(template)
            
            # 添加全局变量
            all_package = {}
            if isinstance(__builtins__, dict):
                all_package.update(__builtins__)
            else:
                all_package.update(__builtins__.__dict__)
            
            # 使用缓存的Faker实例
            self.temp.globals.update({
                "time": time, 
                "random": random, 
                "faker": self._get_faker_instance('en_US'),
                "faker_zh": self._get_faker_instance('zh_CN'),
                **all_package
            })
            
            # 缓存模板
            Template._template_cache[template] = {'env': self.env, 'temp': self.temp}
    
    def _get_faker_instance(self, locale='en_US'):
        """获取或创建Faker实例，使用缓存避免重复创建
        
        Args:
            locale: 语言区域设置
            
        Returns:
            Faker实例
        """
        if locale not in Template._faker_instances:
            Template._faker_instances[locale] = Faker(locale)
        return Template._faker_instances[locale]

    def render(self, **kwargs):
        """渲染单个模板"""
        try:
            return self.temp.render(**kwargs)
        except UndefinedError as e:
            Console().print(
                f"[red]Template rendering failed: {self.template}."
                f" Please provide the [bold yellow]-e/--extra[/bold yellow] argument with required parameters.[/red]"
                f"{e}")
            exit(1)
            
    def batch_render(self, count, render=True):
        """批量渲染多个模板实例，优化性能
        
        Args:
            count: 需要渲染的实例数量
            
        Returns:
            list: 渲染后的字符串列表
        """
        # 预分配结果列表大小，避免动态扩展
        results = [None] * count
        
        # 批量渲染
        for i in range(count):
            try:
                if not render:
                    results[i] = self.template
                else:
                    results[i] = self.temp.render()
            except UndefinedError as e:
                Console().print(
                    f"[red]Template rendering failed: {self.template}."
                    f" Please provide the [bold yellow]-e/--extra[/bold yellow] argument with required parameters.[/red]"
                    f"{e}")
                exit(1)
        return results

# 将字节数转换为易读格式
def format_bytes(size):
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    return f"{size:.2f} {units[unit_index]}"