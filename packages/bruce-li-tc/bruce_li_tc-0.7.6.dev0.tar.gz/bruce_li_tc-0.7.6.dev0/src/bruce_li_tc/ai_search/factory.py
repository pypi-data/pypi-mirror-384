from typing import Dict, List

class AIModelFactory:
    """AI模型工厂 - 简洁版本"""

    _models: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str):
        """注册装饰器"""

        def wrapper(model_class):
            cls._models[name] = model_class
            return model_class

        return wrapper

    @classmethod
    def create(cls, name: str,*args, **kwargs):
        """创建模型实例"""
        if name not in cls._models:
            raise ValueError(f"模型 '{name}' 不存在。可用模型: {list(cls._models.keys())}")
        return cls._models[name](*args, **kwargs)

    @classmethod
    def list_models(cls) -> List[str]:
        """列出所有可用模型"""
        return list(cls._models.keys())


# 创建全局工厂实例
model_factory = AIModelFactory()