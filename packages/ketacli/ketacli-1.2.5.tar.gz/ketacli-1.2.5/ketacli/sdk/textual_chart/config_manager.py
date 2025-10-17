"""
模型配置管理数据模型

提供模型配置的CRUD操作和数据验证功能。
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from ketacli.sdk.ai.config import AIConfig, AIModelConfig
import copy


@dataclass
class ModelConfigFormData:
    """模型配置表单数据类"""
    name: str = ""
    endpoint: str = ""
    api_key: str = ""
    model: str = ""
    provider: str = "openai"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 300
    max_iterations: int = 20
    headers: Optional[Dict[str, str]] = field(default_factory=dict)
    extra_params: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def to_ai_model_config(self) -> AIModelConfig:
        """转换为AIModelConfig对象"""
        return AIModelConfig(
            name=self.name,
            endpoint=self.endpoint,
            api_key=self.api_key,
            model=self.model,
            provider=self.provider,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            timeout=self.timeout,
            max_iterations=self.max_iterations,
            headers=self.headers if self.headers else None,
            extra_params=self.extra_params if self.extra_params else None
        )
    
    @classmethod
    def from_ai_model_config(cls, config: AIModelConfig) -> 'ModelConfigFormData':
        """从AIModelConfig对象创建"""
        return cls(
            name=config.name,
            endpoint=config.endpoint,
            api_key=config.api_key,
            model=config.model,
            provider=config.provider,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            timeout=config.timeout,
            max_iterations=getattr(config, 'max_iterations', 20),
            headers=config.headers or {},
            extra_params=config.extra_params or {}
        )
    
    def validate(self) -> List[str]:
        """验证表单数据，返回错误信息列表"""
        errors = []
        
        if not self.name.strip():
            errors.append("模型名称不能为空")
        
        if not self.endpoint.strip():
            errors.append("API端点不能为空")
        elif not (self.endpoint.startswith('http://') or self.endpoint.startswith('https://')):
            errors.append("API端点必须以http://或https://开头")
        
        if not self.api_key.strip():
            errors.append("API密钥不能为空")
        
        if not self.model.strip():
            errors.append("模型标识不能为空")
        
        if self.max_tokens <= 0:
            errors.append("最大token数必须大于0")
        
        if not (0.0 <= self.temperature <= 2.0):
            errors.append("温度参数必须在0.0-2.0之间")
        
        if self.timeout <= 0:
            errors.append("超时时间必须大于0")

        if self.max_iterations <= 0:
            errors.append("最大迭代次数必须大于0")
        
        return errors


class ModelConfigManager:
    """模型配置管理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self.config_path = config_path
        self._ai_config = None
        self._refresh_config()
    
    def _refresh_config(self):
        """刷新配置"""
        self._ai_config = AIConfig(config_path=self.config_path, allow_empty=True)
    
    def get_all_models(self) -> List[Dict[str, Any]]:
        """获取所有模型配置"""
        try:
            models = []
            model_names = self._ai_config.list_models()
            default_model = None
            
            try:
                default_model = self._ai_config.get_default_model()
            except ValueError:
                pass  # 没有默认模型
            
            for name in model_names:
                try:
                    config = self._ai_config.get_model_config(name)
                    model_dict = asdict(config)
                    model_dict['is_default'] = (name == default_model)
                    models.append(model_dict)
                except Exception:
                    continue
            
            return models
        except Exception:
            return []
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfigFormData]:
        """获取指定模型的配置"""
        try:
            config = self._ai_config.get_model_config(model_name)
            return ModelConfigFormData.from_ai_model_config(config)
        except Exception:
            return None
    
    def add_model(self, form_data: ModelConfigFormData) -> tuple[bool, str]:
        """
        添加新模型配置
        
        Args:
            form_data: 表单数据
            
        Returns:
            (成功标志, 错误信息)
        """
        try:
            # 验证数据
            errors = form_data.validate()
            if errors:
                return False, "；".join(errors)
            
            # 检查模型名称是否已存在
            if form_data.name in self._ai_config.list_models():
                return False, f"模型名称 '{form_data.name}' 已存在"
            
            # 添加模型
            ai_config = form_data.to_ai_model_config()
            self._ai_config.add_model(ai_config)
            # 注意：不需要调用 _refresh_config()，因为 add_model 已经保存了配置
            
            return True, "模型配置添加成功"
        except Exception as e:
            return False, f"添加模型配置失败: {str(e)}"
    
    def update_model(self, original_name: str, form_data: ModelConfigFormData) -> tuple[bool, str]:
        """
        更新模型配置
        
        Args:
            original_name: 原始模型名称
            form_data: 表单数据
            
        Returns:
            (成功标志, 错误信息)
        """
        try:
            # 验证数据
            errors = form_data.validate()
            if errors:
                return False, "；".join(errors)
            
            # 检查原始模型是否存在
            if original_name not in self._ai_config.list_models():
                return False, f"模型 '{original_name}' 不存在"
            
            # 如果名称发生变化，检查新名称是否已存在
            if form_data.name != original_name and form_data.name in self._ai_config.list_models():
                return False, f"模型名称 '{form_data.name}' 已存在"
            
            # 检查是否为默认模型
            is_default = False
            try:
                default_model = self._ai_config.get_default_model()
                is_default = (original_name == default_model)
            except ValueError:
                pass
            
            # 删除原配置
            self._ai_config.remove_model(original_name)
            
            # 添加新配置
            ai_config = form_data.to_ai_model_config()
            self._ai_config.add_model(ai_config)
            
            # 如果原来是默认模型，更新默认模型设置
            if is_default and form_data.name != original_name:
                self._ai_config.set_default_model(form_data.name)
            
            # 注意：不需要调用 _refresh_config()，因为相关方法已经保存了配置
            return True, "模型配置更新成功"
        except Exception as e:
            return False, f"更新模型配置失败: {str(e)}"
    
    def delete_model(self, model_name: str) -> tuple[bool, str]:
        """
        删除模型配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            (成功标志, 错误信息)
        """
        try:
            # 检查模型是否存在
            if model_name not in self._ai_config.list_models():
                return False, f"模型 '{model_name}' 不存在"
            
            # 检查是否为默认模型
            is_default = False
            try:
                default_model = self._ai_config.get_default_model()
                is_default = (model_name == default_model)
            except ValueError:
                pass
            
            # 删除模型
            self._ai_config.remove_model(model_name)
            
            # 如果删除的是默认模型，清除默认模型设置
            if is_default:
                remaining_models = self._ai_config.list_models()
                if remaining_models:
                    # 设置第一个剩余模型为默认
                    self._ai_config.set_default_model(remaining_models[0])
            
            # 注意：不需要调用 _refresh_config()，因为相关方法已经保存了配置
            return True, "模型配置删除成功"
        except Exception as e:
            return False, f"删除模型配置失败: {str(e)}"
    
    def set_default_model(self, model_name: str) -> tuple[bool, str]:
        """
        设置默认模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            (成功标志, 错误信息)
        """
        try:
            self._ai_config.set_default_model(model_name)
            # 注意：不需要调用 _refresh_config()，因为 set_default_model 已经保存了配置
            return True, f"已设置 '{model_name}' 为默认模型"
        except Exception as e:
            return False, f"设置默认模型失败: {str(e)}"
    
    def get_default_model(self) -> Optional[str]:
        """获取默认模型名称"""
        try:
            return self._ai_config.get_default_model()
        except ValueError:
            return None
    
    def duplicate_model(self, source_name: str, new_name: str) -> tuple[bool, str]:
        """
        复制模型配置
        
        Args:
            source_name: 源模型名称
            new_name: 新模型名称
            
        Returns:
            (成功标志, 错误信息)
        """
        try:
            # 获取源模型配置
            source_config = self.get_model_config(source_name)
            if not source_config:
                return False, f"源模型 '{source_name}' 不存在"
            
            # 检查新名称是否已存在
            if new_name in self._ai_config.list_models():
                return False, f"模型名称 '{new_name}' 已存在"
            
            # 创建新配置
            new_config = copy.deepcopy(source_config)
            new_config.name = new_name
            
            # 添加新模型
            return self.add_model(new_config)
        except Exception as e:
            return False, f"复制模型配置失败: {str(e)}"