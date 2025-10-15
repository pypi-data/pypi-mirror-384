from abc import ABC, abstractmethod
from typing import Any, Callable, Type, Dict, List, Optional


class B_Adapter:
    """
    适配器模式 (Adapter)
    将一个类的接口转换成客户希望的另外一个接口

    使用场景:
    - 需要使用现有的类，但其接口与需求不匹配
    - 创建可重用的类，与不相关或不可预见的类协作

    参数:
        adaptee (Any): 需要适配的对象
        adapted_methods (Dict[str, str]): 方法映射字典

    返回:
        Any: 适配后的对象

    示例:
        >>> class EuropeanSocket:
        >>>     def voltage(self): return 220
        >>>
        >>> adapter = B_Adapter(EuropeanSocket(), {'voltage': 'voltage'})
        >>> adapter.voltage()  # 220
    """

    def __init__(self, adaptee: Any, adapted_methods: Dict[str, str]):
        self.adaptee = adaptee
        self.__dict__.update(adapted_methods)

    def __getattr__(self, attr):
        """访问未适配的方法时转发到原始对象"""
        return getattr(self.adaptee, attr)


class B_Decorator:
    """
    装饰器模式 (Decorator)
    动态地给一个对象添加一些额外的职责

    使用场景:
    - 在不影响其他对象的情况下，以动态、透明的方式给单个对象添加职责
    - 处理那些可以撤销的职责

    参数:
        obj (Any): 要装饰的对象
        wrapper (Callable): 装饰函数

    返回:
        Any: 装饰后的对象

    示例:
        >>> def greet(name):
        >>>     return f"Hello, {name}!"
        >>>
        >>> def uppercase_decorator(func, name):
        >>>     return func(name).upper()
        >>>
        >>> decorated_greet = B_Decorator(greet, uppercase_decorator)
        >>> print(decorated_greet("Alice"))  # "HELLO, ALICE!"
    """

    def __init__(self, obj: Any, wrapper: Callable):
        self.obj = obj
        self.wrapper = wrapper

    def __call__(self, *args, **kwargs) -> Any:
        return self.wrapper(self.obj, *args, **kwargs)


class B_Facade:
    """
    外观模式 (Facade)
    为子系统中的一组接口提供一个一致的界面

    使用场景:
    - 为复杂的子系统提供一个简单的接口
    - 构建多层结构的系统时，使用Facade定义每层的入口点

    参数:
        subsystems (Dict[str, Any]): 子系统组件字典

    返回:
        Any: 外观对象

    示例:
        >>> class CPU:
        >>>     def execute(self): print("CPU: 执行指令")
        >>>
        >>> class Memory:
        >>>     def load(self): print("内存: 加载数据")
        >>>
        >>> facade = B_Facade({'cpu': CPU(), 'memory': Memory()})
        >>> facade.start()
        >>> # 输出:
        >>> # 内存: 加载数据
        >>> # CPU: 执行指令
    """

    def __init__(self, subsystems: Dict[str, Any]):
        self.subsystems = subsystems

    def start(self) -> None:
        """简化启动过程"""
        self.subsystems['memory'].load()
        self.subsystems['cpu'].execute()


class B_Composite:
    """
    组合模式 (Composite)
    将对象组合成树形结构以表示"部分-整体"的层次结构

    使用场景:
    - 表示对象的整体与部分层次结构
    - 希望用户忽略组合对象与单个对象的不同

    示例:
        >>> class File:
        >>>     def __init__(self, name):
        >>>         self.name = name
        >>>     def display(self):
        >>>         print(f"文件: {self.name}")
        >>>
        >>> class Folder(B_Composite):
        >>>     def __init__(self, name):
        >>>         self.name = name
        >>>         self.children = []
        >>>
        >>>     def add(self, child):
        >>>         self.children.append(child)
        >>>
        >>>     def remove(self, child):
        >>>         self.children.remove(child)
        >>>
        >>>     def display(self):
        >>>         print(f"文件夹: {self.name}")
        >>>         for child in self.children:
        >>>             child.display()
        >>>
        >>> root = Folder("根目录")
        >>> file1 = File("文档.txt")
        >>> root.add(file1)
        >>> root.display()
        >>> # 输出:
        >>> # 文件夹: 根目录
        >>> # 文件: 文档.txt
    """

    def __init__(self):
        self.children = []

    def add(self, component: Any) -> None:
        """添加子组件"""
        self.children.append(component)

    def remove(self, component: Any) -> None:
        """移除子组件"""
        self.children.remove(component)

    @abstractmethod
    def operation(self) -> None:
        """执行操作"""
        pass


class B_Proxy:
    """
    代理模式 (Proxy)
    为其他对象提供一种代理以控制对这个对象的访问

    使用场景:
    - 远程代理：为不同地址空间的对象提供本地代表
    - 虚拟代理：根据需要创建开销很大的对象
    - 安全代理：控制对原始对象的访问

    参数:
        real_subject (Any): 真实主题对象

    返回:
        Any: 代理对象

    示例:
        >>> class RealImage:
        >>>     def __init__(self, filename):
        >>>         self.filename = filename
        >>>         print(f"加载大图像: {filename}")
        >>>
        >>>     def display(self):
        >>>         print(f"显示图像: {self.filename}")
        >>>
        >>> class ImageProxy(B_Proxy):
        >>>     def __init__(self, filename):
        >>>         self.filename = filename
        >>>         self.real_image = None
        >>>
        >>>     def display(self):
        >>>         if self.real_image is None:
        >>>             self.real_image = RealImage(self.filename)
        >>>         self.real_image.display()
        >>>
        >>> proxy = ImageProxy("large_photo.jpg")
        >>> # 此时尚未加载真实图像
        >>> proxy.display()  # 第一次调用时加载并显示图像
    """

    def __init__(self, real_subject: Any):
        self.real_subject = real_subject

    def __getattr__(self, name):
        """代理所有方法调用到真实对象"""
        return getattr(self.real_subject, name)


class B_Flyweight:
    """
    享元模式 (Flyweight)
    运用共享技术有效地支持大量细粒度的对象

    使用场景:
    - 一个应用程序使用了大量的对象
    - 对象的大多数状态可以外部化

    参数:
        factory (Callable): 享元工厂函数

    返回:
        Any: 享元对象

    示例:
        >>> class TreeType:
        >>>     def __init__(self, name, color):
        >>>         self.name = name
        >>>         self.color = color
        >>>
        >>> tree_factory = B_Flyweight(lambda name, color: TreeType(name, color))
        >>> oak1 = tree_factory.get("Oak", "Green")
        >>> oak2 = tree_factory.get("Oak", "Green")
        >>> maple = tree_factory.get("Maple", "Red")
        >>>
        >>> print(oak1 is oak2)  # True，相同参数的享元对象是同一个
        >>> print(oak1 is maple)  # False
    """

    def __init__(self, factory: Callable):
        self.flyweights = {}
        self.factory = factory

    def get(self, *args) -> Any:
        """获取或创建享元对象"""
        key = tuple(args)
        if key not in self.flyweights:
            self.flyweights[key] = self.factory(*args)
        return self.flyweights[key]