from abc import ABC, abstractmethod
from typing import Type, Any, Dict, List, Callable, Optional, Union
from copy import deepcopy


class B_SingletonMeta(type):
    """
    单例模式 (Singleton)
    确保一个类只有一个实例，并提供全局访问点

    使用场景:
    - 当类只能有一个实例且客户端需要访问该实例时
    - 控制共享资源（如数据库连接、日志记录器）

    示例:
        >>> class Database(metaclass=B_SingletonMeta):
        >>>     def __init__(self, connection_string):
        >>>         self.connection_string = connection_string
        >>>
        >>> db1 = Database("mysql://localhost")
        >>> db2 = Database("postgres://localhost")
        >>> db1 is db2  # True
    """
    _instances: Dict[Type, Any] = {}

    def __call__(cls, *args, **kwargs) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class B_FactoryMethod:
    """
    工厂方法模式 (Factory Method)
    定义一个创建对象的接口，但让子类决定实例化哪个类

    使用场景:
    - 当类不知道它需要创建哪些具体对象时
    - 当类希望其子类指定创建的对象时

    参数:
        creator_func (Callable): 创建对象的工厂函数
        *args: 工厂函数的参数
        **kwargs: 工厂函数的关键字参数

    返回:
        Any: 创建的对象实例

    示例:
        >>> def create_button(os_type):
        >>>     if os_type == "windows":
        >>>         return WindowsButton()
        >>>     elif os_type == "mac":
        >>>         return MacButton()
        >>>
        >>> button_factory = B_FactoryMethod(create_button, "windows")
        >>> button = button_factory.create()  # 返回WindowsButton实例
    """

    def __init__(self, creator_func: Callable, *args, **kwargs):
        self.creator_func = creator_func
        self.args = args
        self.kwargs = kwargs

    def create(self) -> Any:
        """创建并返回对象实例"""
        return self.creator_func(*self.args, **self.kwargs)


class B_AbstractFactory(ABC):
    """
    抽象工厂模式 (Abstract Factory)
    提供一个创建一系列相关或相互依赖对象的接口

    使用场景:
    - 系统需要独立于其产品的创建、组合和表示
    - 系统需要配置多个产品系列中的一个

    示例:
        >>> class GUIFactory(B_AbstractFactory):
        >>>     @abstractmethod
        >>>     def create_button(self): pass
        >>>     @abstractmethod
        >>>     def create_checkbox(self): pass
        >>>
        >>> class WinFactory(GUIFactory):
        >>>     def create_button(self): return WinButton()
        >>>     def create_checkbox(self): return WinCheckbox()
        >>>
        >>> factory = WinFactory()
        >>> button = factory.create_button()
    """

    @abstractmethod
    def create_product_a(self) -> Any:
        """创建产品A"""
        pass

    @abstractmethod
    def create_product_b(self) -> Any:
        """创建产品B"""
        pass


class B_Builder:
    """
    建造者模式 (Builder)
    将一个复杂对象的构建与其表示分离，使同样的构建过程可以创建不同的表示

    使用场景:
    - 当创建复杂对象的算法应该独立于该对象的组成部分以及它们的装配方式时
    - 当构造过程必须允许被构造的对象有不同的表示时

    示例:
        >>> class CarBuilder(B_Builder):
        >>>     def __init__(self):
        >>>         super().__init__()
        >>>         self.car = Car()
        >>>
        >>>     def set_seats(self, num):
        >>>         self.car.seats = num
        >>>         return self
        >>>
        >>>     def set_engine(self, engine_type):
        >>>         self.car.engine = engine_type
        >>>         return self
        >>>
        >>>     def build(self):
        >>>         return self.car
        >>>
        >>> builder = CarBuilder()
        >>> car = builder.set_seats(4).set_engine("V8").build()
    """

    def __init__(self):
        self._product = None

    def build(self) -> Any:
        """返回构建的产品"""
        return self._product


class B_Prototype:
    """
    原型模式 (Prototype)
    用原型实例指定创建对象的种类，并通过拷贝这些原型创建新的对象

    使用场景:
    - 当要实例化的类是在运行时指定时
    - 避免创建与产品类层次平行的工厂类层次

    参数:
        obj (Any): 需要克隆的对象

    返回:
        Any: 克隆后的新对象

    示例:
        >>> class Shape:
        >>>     def __init__(self, color):
        >>>         self.color = color
        >>>
        >>> circle = Shape("red")
        >>> prototype = B_Prototype(circle)
        >>> circle_clone = prototype.clone()
    """

    def __init__(self, obj: Any):
        self.obj = obj

    def clone(self) -> Any:
        """创建对象的深度拷贝"""
        return deepcopy(self.obj)