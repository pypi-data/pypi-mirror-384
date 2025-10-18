"""
AI大模型配置管理模块

支持从配置文件中读取AI大模型的相关配置信息。
"""

import yaml
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class AIModelConfig:
    """AI模型配置类"""
    name: str
    endpoint: str
    api_key: str
    model: str
    provider: str = "openai"  # 添加provider字段，默认为openai
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 300
    # 新增：工具迭代上限，默认20次
    max_iterations: int = 20
    headers: Optional[Dict[str, str]] = None
    extra_params: Optional[Dict[str, Any]] = None


class AIConfig:
    """AI配置管理器"""
    
    def __init__(self, config_path: str = None, allow_empty: bool = False):
        """
        初始化AI配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
            allow_empty: 是否允许空配置（用于添加模型时）
        """
        if config_path is None:
            # 使用默认配置目录
            config_dir = os.path.expanduser('~/.keta')
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, 'ai_config.yaml')
        
        self.config_path = config_path
        self._config = None
        self.allow_empty = allow_empty
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                    
                # 如果不允许空配置，检查配置是否为空或无效
                if not self.allow_empty and (not self._config or 'models' not in self._config or not self._config['models']):
                    raise Exception(f"AI配置文件为空或无效。请使用 'ketacli ai_config add' 命令添加模型配置。")
            else:
                if self.allow_empty:
                    # 允许空配置时，初始化为空字典
                    self._config = {}
                else:
                    raise Exception(f"AI配置文件不存在: {self.config_path}\n"
                                  f"请使用 'ketacli ai_config add -m <model_name> -e <endpoint> -k <api_key>' 命令创建配置。\n"
                                  f"例如: ketacli ai_config add -m openai -e https://api.openai.com/v1/chat/completions -k your-api-key")
        except Exception as e:
            raise Exception(f"加载AI配置文件失败: {e}")
    

    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            raise Exception(f"保存AI配置文件失败: {e}")
    
    def get_model_config(self, model_name: str = None) -> AIModelConfig:
        """
        获取指定模型的配置
        
        Args:
            model_name: 模型名称，如果为None则使用默认模型
            
        Returns:
            AIModelConfig: 模型配置对象
        """
        if model_name is None:
            default_model = self._config.get('default_model')
            if not default_model:
                raise ValueError("未设置默认模型。请使用 'ketacli ai_config set-default <model_name>' 命令设置默认模型。")
            model_name = default_model
        
        models = self._config.get('models', {})
        if model_name not in models:
            available_models = list(models.keys())
            if available_models:
                raise ValueError(f"未找到模型配置: {model_name}。可用模型: {', '.join(available_models)}")
            else:
                raise ValueError(f"未找到模型配置: {model_name}。请先使用 'ketacli ai_config add' 命令添加模型配置。")
        
        config_data = models[model_name]
        return AIModelConfig(
            name=config_data.get('name', model_name),
            endpoint=config_data.get('endpoint', ''),
            api_key=config_data.get('api_key', ''),
            model=config_data.get('model', ''),
            provider=config_data.get('provider', 'openai'),  # 添加provider字段处理
            max_tokens=config_data.get('max_tokens', 4096),
            temperature=config_data.get('temperature', 0.7),
            timeout=config_data.get('timeout', 30),
            max_iterations=config_data.get('max_iterations', 20),
            headers=config_data.get('headers'),
            extra_params=config_data.get('extra_params')
        )
    
    def list_models(self) -> list:
        """获取所有可用的模型名称"""
        return list(self._config.get('models', {}).keys())
    
    def add_model(self, model_config: AIModelConfig):
        """
        添加新的模型配置
        
        Args:
            model_config: 模型配置对象
        """
        # 如果配置为空，初始化基本结构
        if not self._config:
            self._config = {}
        
        if 'models' not in self._config:
            self._config['models'] = {}
        
        self._config['models'][model_config.name] = {
            'name': model_config.name,
            'endpoint': model_config.endpoint,
            'api_key': model_config.api_key,
            'model': model_config.model,
            'provider': model_config.provider,  # 添加provider字段
            'max_tokens': model_config.max_tokens,
            'temperature': model_config.temperature,
            'timeout': model_config.timeout,
            'max_iterations': model_config.max_iterations,
            'headers': model_config.headers,
            'extra_params': model_config.extra_params
        }
        
        # 如果这是第一个模型且没有默认模型，设置为默认
        if not self._config.get('default_model'):
            self._config['default_model'] = model_config.name
            
        self.save_config()
    
    def remove_model(self, model_name: str):
        """
        删除模型配置
        
        Args:
            model_name: 模型名称
        """
        if model_name not in self.list_models():
            raise ValueError(f"模型不存在: {model_name}")
            
        del self._config['models'][model_name]
        self.save_config()
    
    def set_default_model(self, model_name: str):
        """
        设置默认模型
        
        Args:
            model_name: 模型名称
        """
        if model_name not in self.list_models():
            raise ValueError(f"模型不存在: {model_name}")
        
        self._config['default_model'] = model_name
        self.save_config()
    
    def get_default_model(self) -> str:
        """获取默认模型名称"""
        default_model = self._config.get('default_model')
        if not default_model:
            raise ValueError("未设置默认模型。请使用 'ketacli ai_config set-default <model_name>' 命令设置默认模型。")
        return default_model