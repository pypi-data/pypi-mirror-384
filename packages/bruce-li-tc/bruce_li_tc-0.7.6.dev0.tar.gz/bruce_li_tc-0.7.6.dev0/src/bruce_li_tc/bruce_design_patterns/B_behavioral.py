from abc import ABC, abstractmethod
from typing import Any, Callable, List, Dict, Type, Optional


class B_Observer:
    """
    观察者模式 (Observer)
    定义对象间的一种一对多的依赖关系，当一个对象的状态发生改变时，所有依赖于它的对象都得到通知并被自动更新

    使用场景:
    - 当一个抽象模型有两个方面，其中一个方面依赖于另一个方面
    - 当一个对象的改变需要同时改变其它对象

    示例:
        >>> subject = B_Observer()
        >>> class ConcreteObserver:
        >>>     def update(self):
        >>>         print("Observer updated")
        >>>
        >>> observer = ConcreteObserver()
        >>> subject.attach(observer)
        >>> subject.notify()  # Observer updated
    """

    def __init__(self):
        self._observers = []

    def attach(self, observer: Any) -> None:
        """附加观察者"""
        self._observers.append(observer)

    def detach(self, observer: Any) -> None:
        """分离观察者"""
        self._observers.remove(observer)

    def notify(self) -> None:
        """通知所有观察者"""
        for observer in self._observers:
            observer.update()


class B_Strategy:
    """
    策略模式 (Strategy)
    定义一系列的算法，把它们一个个封装起来，并且使它们可相互替换

    使用场景:
    - 许多相关的类仅仅是行为有异
    - 需要使用一个算法的不同变体

    参数:
        strategy_func (Callable): 策略函数

    返回:
        Any: 上下文对象

    示例:
        >>> def strategy_a(data): return sorted(data)
        >>> def strategy_b(data): return sorted(data, reverse=True)
        >>>
        >>> strategy = B_Strategy(strategy_a)
        >>> result = strategy.execute([3, 1, 2])  # [1, 2, 3]
        >>>
        >>> strategy = B_Strategy(strategy_b)
        >>> result = strategy.execute([3, 1, 2])  # [3, 2, 1]
    """

    def __init__(self, strategy_func: Callable):
        self.strategy_func = strategy_func

    def execute(self, *args, **kwargs) -> Any:
        """执行当前策略"""
        return self.strategy_func(*args, **kwargs)


class B_Command:
    """
    命令模式 (Command)
    将一个请求封装为一个对象，从而使你可用不同的请求对客户进行参数化

    使用场景:
    - 需要抽象出待执行的动作
    - 支持撤销操作

    参数:
        receiver (Any): 接收者对象
        action (str): 要执行的方法名
        *args: 方法参数
        **kwargs: 方法关键字参数

    返回:
        Any: 命令对象

    示例:
        >>> class Light:
        >>>     def turn_on(self): print("Light on")
        >>>     def turn_off(self): print("Light off")
        >>>
        >>> light = Light()
        >>> turn_on = B_Command(light, "turn_on")
        >>> turn_on.execute()  # Light on
    """

    def __init__(self, receiver: Any, action: str, *args, **kwargs):
        self.receiver = receiver
        self.action = action
        self.args = args
        self.kwargs = kwargs

    def execute(self) -> Any:
        """执行命令"""
        return getattr(self.receiver, self.action)(*self.args, **self.kwargs)


class B_State:
    """
    状态模式 (State)
    允许一个对象在其内部状态改变时改变它的行为

    使用场景:
    - 一个对象的行为取决于它的状态，并且它必须在运行时根据状态改变它的行为
    - 操作中有庞大的多分支的条件语句，且这些分支依赖于该对象的状态

    示例:
        >>> class StateA:
        >>>     def handle(self, context):
        >>>         print("State A handling")
        >>>         context.state = StateB()
        >>>
        >>> class StateB:
        >>>     def handle(self, context):
        >>>         print("State B handling")
        >>>         context.state = StateA()
        >>>
        >>> context = B_State()
        >>> context.state = StateA()
        >>> context.request()  # State A handling
        >>> context.request()  # State B handling
    """

    def __init__(self):
        self._state = None

    @property
    def state(self) -> Any:
        return self._state

    @state.setter
    def state(self, state: Any) -> None:
        self._state = state

    def request(self) -> None:
        """委托给当前状态处理"""
        self._state.handle(self)


class B_ChainOfResponsibility:
    """
    责任链模式 (Chain of Responsibility)
    使多个对象都有机会处理请求，从而避免请求的发送者和接收者之间的耦合关系

    使用场景:
    - 有多个对象可以处理一个请求，哪个对象处理该请求运行时自动确定
    - 想在不明确指定接收者的情况下，向多个对象中的一个提交请求

    示例:
        >>> class ConcreteHandlerA(B_ChainOfResponsibility):
        >>>     def handle(self, request):
        >>>         if request == "A":
        >>>             return "Handled by A"
        >>>         return super().handle(request)
        >>>
        >>> class ConcreteHandlerB(B_ChainOfResponsibility):
        >>>     def handle(self, request):
        >>>         if request == "B":
        >>>             return "Handled by B"
        >>>         return super().handle(request)
        >>>
        >>> chain = ConcreteHandlerA(ConcreteHandlerB())
        >>> result = chain.handle("B")  # "Handled by B"
    """

    def __init__(self, successor: Optional[Any] = None):
        self.successor = successor

    def handle(self, request: Any) -> Any:
        """处理请求或传递给下一个处理者"""
        if self.successor:
            return self.successor.handle(request)
        return None


class B_TemplateMethod(ABC):
    """
    模板方法模式 (Template Method)
    定义一个操作中的算法的骨架，而将一些步骤延迟到子类中

    使用场景:
    - 一次性实现一个算法的不变部分，将可变部分留给子类实现
    - 控制子类扩展

    示例:
        >>> class ReportGenerator(B_TemplateMethod):
        >>>     def step1(self):
        >>>         return "Header"
        >>>
        >>>     def step2(self):
        >>>         return "Body"
        >>>
        >>> report = ReportGenerator()
        >>> output = report.generate()  # "Header\nBody"
    """

    @abstractmethod
    def step1(self) -> Any:
        pass

    @abstractmethod
    def step2(self) -> Any:
        pass

    def generate(self) -> str:
        """模板方法定义算法结构"""
        return f"{self.step1()}\n{self.step2()}"


class B_Visitor:
    """
    访问者模式 (Visitor)
    表示一个作用于某对象结构中的各元素的操作，使你可以在不改变各元素的类的前提下定义作用于这些元素的新操作

    使用场景:
    - 对象结构中包含很多类对象，它们有不同的接口，需要对这些对象实施一些操作
    - 需要对一个对象结构中的对象进行很多不同的操作

    示例:
        >>> class ElementA:
        >>>     def accept(self, visitor):
        >>>         visitor.visit(self)
        >>>
        >>> class ConcreteVisitor(B_Visitor):
        >>>     def visit_elementa(self, element):
        >>>         print("Visiting ElementA")
        >>>
        >>> element = ElementA()
        >>> visitor = ConcreteVisitor()
        >>> element.accept(visitor)  # "Visiting ElementA"
    """

    def visit(self, element: Any) -> None:
        """访问元素"""
        method_name = f"visit_{type(element).__name__.lower()}"
        method = getattr(self, method_name, self.generic_visit)
        method(element)

    def generic_visit(self, element: Any) -> None:
        """通用访问方法"""
        print(f"Visiting {type(element).__name__}")


class B_Mediator:
    """
    中介者模式 (Mediator)
    用一个中介对象来封装一系列的对象交互

    使用场景:
    - 一组对象以定义良好但是复杂的方式进行通信
    - 想定制一个分布在多个类中的行为，而又不想生成太多的子类

    示例:
        >>> class ChatRoom(B_Mediator):
        >>>     def __init__(self):
        >>>         super().__init__()
        >>>         self.users = []
        >>>
        >>>     def register(self, user):
        >>>         self.users.append(user)
        >>>
        >>>     def notify(self, sender, event):
        >>>         for user in self.users:
        >>>             if user != sender:
        >>>                 user.receive(event)
        >>>
        >>> class User:
        >>>     def __init__(self, name, chatroom):
        >>>         self.name = name
        >>>         self.chatroom = chatroom
        >>>         chatroom.register(self)
        >>>
        >>>     def send(self, message):
        >>>         self.chatroom.notify(self, message)
        >>>
        >>>     def receive(self, message):
        >>>         print(f"{self.name} received: {message}")
        >>>
        >>> chatroom = ChatRoom()
        >>> user1 = User("Alice", chatroom)
        >>> user2 = User("Bob", chatroom)
        >>> user1.send("Hello!")  # Bob received: Hello!
    """

    def __init__(self):
        self.components = []

    def register(self, component: Any) -> None:
        """注册组件"""
        self.components.append(component)

    def notify(self, sender: Any, event: str) -> None:
        """通知其他组件"""
        for component in self.components:
            if component != sender:
                component.receive(event)


class B_Memento:
    """
    备忘录模式 (Memento)
    在不破坏封装性的前提下，捕获一个对象的内部状态，并在该对象之外保存这个状态

    使用场景:
    - 需要保存对象的状态以便以后恢复
    - 不希望暴露对象的实现细节

    示例:
        >>> class Originator:
        >>>     def __init__(self, state):
        >>>         self._state = state
        >>>
        >>>     def save(self) -> B_Memento:
        >>>         return B_Memento(self._state)
        >>>
        >>>     def restore(self, memento):
        >>>         self._state = memento.get_state()
        >>>
        >>> originator = Originator("State1")
        >>> memento = originator.save()
        >>>
        >>> originator._state = "State2"
        >>> originator.restore(memento)
        >>> print(originator._state)  # "State1"
    """

    def __init__(self, state: Any):
        self._state = state

    def get_state(self) -> Any:
        """获取保存的状态"""
        return self._state