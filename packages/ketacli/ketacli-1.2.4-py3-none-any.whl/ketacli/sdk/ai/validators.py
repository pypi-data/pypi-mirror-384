"""
AI响应数据验证模块

提供回调方法来验证AI大模型返回的数据格式。
"""

from typing import Any, Dict, Callable, Optional
import json
import re
from abc import ABC, abstractmethod


class BaseValidator(ABC):
    """验证器基类"""
    
    @abstractmethod
    def validate(self, response: Any) -> bool:
        """
        验证响应数据
        
        Args:
            response: 响应数据
            
        Returns:
            bool: 验证是否通过
        """
        pass
    
    @abstractmethod
    def get_error_message(self) -> str:
        """获取错误信息"""
        pass


class JSONValidator(BaseValidator):
    """JSON格式验证器"""
    
    def __init__(self, required_fields: list = None):
        """
        初始化JSON验证器
        
        Args:
            required_fields: 必需的字段列表
        """
        self.required_fields = required_fields or []
        self.error_message = ""
    
    def validate(self, response: Any) -> bool:
        """验证JSON格式和必需字段"""
        try:
            if isinstance(response, str):
                data = json.loads(response)
            elif isinstance(response, dict):
                data = response
            else:
                self.error_message = "响应数据不是有效的JSON格式"
                return False
            
            # 检查必需字段
            for field in self.required_fields:
                if field not in data:
                    self.error_message = f"缺少必需字段: {field}"
                    return False
            
            return True
        except json.JSONDecodeError as e:
            self.error_message = f"JSON解析错误: {e}"
            return False
    
    def get_error_message(self) -> str:
        return self.error_message


class RegexValidator(BaseValidator):
    """正则表达式验证器"""
    
    def __init__(self, pattern: str, flags: int = 0):
        """
        初始化正则验证器
        
        Args:
            pattern: 正则表达式模式
            flags: 正则表达式标志
        """
        self.pattern = re.compile(pattern, flags)
        self.error_message = ""
    
    def validate(self, response: Any) -> bool:
        """使用正则表达式验证响应"""
        try:
            text = str(response)
            if self.pattern.search(text):
                return True
            else:
                self.error_message = f"响应不匹配正则表达式: {self.pattern.pattern}"
                return False
        except Exception as e:
            self.error_message = f"正则验证错误: {e}"
            return False
    
    def get_error_message(self) -> str:
        return self.error_message


class LengthValidator(BaseValidator):
    """长度验证器"""
    
    def __init__(self, min_length: int = 0, max_length: int = None):
        """
        初始化长度验证器
        
        Args:
            min_length: 最小长度
            max_length: 最大长度
        """
        self.min_length = min_length
        self.max_length = max_length
        self.error_message = ""
    
    def validate(self, response: Any) -> bool:
        """验证响应长度"""
        try:
            text = str(response)
            length = len(text)
            
            if length < self.min_length:
                self.error_message = f"响应长度 {length} 小于最小长度 {self.min_length}"
                return False
            
            if self.max_length is not None and length > self.max_length:
                self.error_message = f"响应长度 {length} 大于最大长度 {self.max_length}"
                return False
            
            return True
        except Exception as e:
            self.error_message = f"长度验证错误: {e}"
            return False
    
    def get_error_message(self) -> str:
        return self.error_message


class CustomValidator(BaseValidator):
    """自定义验证器"""
    
    def __init__(self, validator_func: Callable[[Any], bool], error_message: str = "自定义验证失败"):
        """
        初始化自定义验证器
        
        Args:
            validator_func: 自定义验证函数
            error_message: 错误信息
        """
        self.validator_func = validator_func
        self.error_message = error_message
    
    def validate(self, response: Any) -> bool:
        """使用自定义函数验证响应"""
        try:
            return self.validator_func(response)
        except Exception as e:
            self.error_message = f"自定义验证错误: {e}"
            return False
    
    def get_error_message(self) -> str:
        return self.error_message


class ResponseValidator:
    """响应验证器管理器"""
    
    def __init__(self):
        self.validators = []
    
    def add_validator(self, validator: BaseValidator):
        """
        添加验证器
        
        Args:
            validator: 验证器实例
        """
        self.validators.append(validator)
    
    def add_json_validator(self, required_fields: list = None):
        """
        添加JSON验证器
        
        Args:
            required_fields: 必需的字段列表
        """
        self.add_validator(JSONValidator(required_fields))
    
    def add_regex_validator(self, pattern: str, flags: int = 0):
        """
        添加正则验证器
        
        Args:
            pattern: 正则表达式模式
            flags: 正则表达式标志
        """
        self.add_validator(RegexValidator(pattern, flags))
    
    def add_length_validator(self, min_length: int = 0, max_length: int = None):
        """
        添加长度验证器
        
        Args:
            min_length: 最小长度
            max_length: 最大长度
        """
        self.add_validator(LengthValidator(min_length, max_length))
    
    def add_custom_validator(self, validator_func: Callable[[Any], bool], error_message: str = "自定义验证失败"):
        """
        添加自定义验证器
        
        Args:
            validator_func: 自定义验证函数
            error_message: 错误信息
        """
        self.add_validator(CustomValidator(validator_func, error_message))
    
    def validate(self, response: Any) -> tuple[bool, list]:
        """
        验证响应数据
        
        Args:
            response: 响应数据
            
        Returns:
            tuple: (是否通过验证, 错误信息列表)
        """
        errors = []
        
        for validator in self.validators:
            if not validator.validate(response):
                errors.append(validator.get_error_message())
        
        return len(errors) == 0, errors
    
    def clear_validators(self):
        """清空所有验证器"""
        self.validators.clear()


# 预定义的常用验证器
def create_openai_validator() -> ResponseValidator:
    """创建OpenAI响应验证器"""
    validator = ResponseValidator()
    validator.add_json_validator(['choices'])
    return validator


def create_claude_validator() -> ResponseValidator:
    """创建Claude响应验证器"""
    validator = ResponseValidator()
    validator.add_json_validator(['content'])
    return validator


def create_text_validator(min_length: int = 1, max_length: int = None) -> ResponseValidator:
    """创建文本响应验证器"""
    validator = ResponseValidator()
    validator.add_length_validator(min_length, max_length)
    return validator