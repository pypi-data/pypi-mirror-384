class UIAutomationError(Exception):
    """UI自动化基础异常"""
    pass

class ElementNotFoundError(UIAutomationError):
    """元素未找到异常"""
    def __init__(self, element_type, criteria):
        super().__init__(f"未找到{element_type}元素，查找条件: {criteria}")
        self.element_type = element_type
        self.criteria = criteria

class ElementNotInteractableError(UIAutomationError):
    """元素不可交互异常"""
    def __init__(self, element_info):
        super().__init__(f"元素不可交互: {element_info}")
        self.element_info = element_info

class TimeoutError(UIAutomationError):
    """操作超时异常"""
    def __init__(self, operation, timeout):
        super().__init__(f"{operation} 操作在 {timeout} 秒内超时")
        self.operation = operation
        self.timeout = timeout

class ProcessError(UIAutomationError):
    """进程操作异常"""
    def __init__(self, operation, error):
        super().__init__(f"{operation} 操作失败: {error}")
        self.operation = operation
        self.error = error

class ImageRecognitionError(UIAutomationError):
    """图像识别失败异常"""
    def __init__(self, template_path, error):
        super().__init__(f"图像识别失败，模板: {template_path}, 错误: {error}")
        self.template_path = template_path
        self.error = error