from .B_creational import *
from .B_structural import *
from .B_behavioral import *

# 定义要导出的所有公共接口
__all__ = [
    # 创建型模式
    'B_SingletonMeta', 'B_FactoryMethod', 'B_AbstractFactory', 'B_Builder', 'B_Prototype',

    # 结构型模式
    'B_Adapter', 'B_Decorator', 'B_Facade', 'B_Composite', 'B_Proxy', 'B_Flyweight',

    # 行为型模式
    'B_Observer', 'B_Strategy', 'B_Command', 'B_State', 'B_ChainOfResponsibility',
    'B_TemplateMethod', 'B_Visitor', 'B_Mediator', 'B_Memento'
]