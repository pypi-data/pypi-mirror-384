from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass



class BaseAIModel(ABC):
    """AI模型基类 - 定义所有模型必须实现的统一接口"""
    @abstractmethod
    def search(self, keyword: str, **kwargs) ->List[str]:
        """搜索功能 - 所有模型必须实现的搜索方法"""
        pass

    def set_config(self, **kwargs):
        """设置模型配置"""
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": self.__class__.__name__
        }
