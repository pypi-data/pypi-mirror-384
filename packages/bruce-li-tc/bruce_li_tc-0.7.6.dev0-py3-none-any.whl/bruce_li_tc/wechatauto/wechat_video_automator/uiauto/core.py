import uiautomation as auto
import time
from typing import Optional, Dict, Any, List, Union, Callable
from .exceptions import ElementNotFoundError, ElementNotInteractableError, TimeoutError


class UIElement:
    """
    UI元素封装类 - 提供统一的元素操作接口

    参数说明：
    所有参数都来自Inspect.exe工具中查看的控件属性：
    - control_type: 控件类型 (如 auto.ButtonControl, auto.EditControl)
    - name: 控件的Name属性 (从Inspect中查看)
    - automation_id: 控件的AutomationId属性 (可选，从Inspect中查看)
    - class_name: 控件的ClassName属性 (可选，从Inspect中查看)
    - parent: 父元素对象 (可选，如果指定则在父元素内查找)
    - search_depth: 搜索深度 (默认1，表示只搜索直接子元素)
    """

    def __init__(self, control_type, name=None, automation_id=None,
                 class_name=None, parent=None, search_depth=1):
        self.control_type = control_type
        self.name = name
        self.automation_id = automation_id
        self.class_name = class_name
        self.parent = parent
        self.search_depth = search_depth
        self._element = None

    def find(self, timeout=10) -> auto.Control:
        """
        查找元素

        参数说明：
        - timeout: 查找超时时间(秒)

        返回值: 找到的uiautomation控件对象

        使用示例：
        # 查找名为"确定"的按钮
        button = UIElement(auto.ButtonControl, name="确定").find()
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                if self.parent:
                    # 在父元素内查找
                    criteria = {}
                    if self.name: criteria['Name'] = self.name
                    if self.automation_id: criteria['AutomationId'] = self.automation_id
                    if self.class_name: criteria['ClassName'] = self.class_name

                    if criteria:
                        element = self.parent.Control(ControlType=self.control_type,
                                                      searchDepth=self.search_depth,
                                                      **criteria)
                    else:
                        element = self.parent.Control(ControlType=self.control_type,
                                                      searchDepth=self.search_depth)
                else:
                    # 全局查找
                    criteria = {}
                    if self.name: criteria['Name'] = self.name
                    if self.automation_id: criteria['AutomationId'] = self.automation_id
                    if self.class_name: criteria['ClassName'] = self.class_name

                    if criteria:
                        element = self.control_type(**criteria)
                    else:
                        element = self.control_type()

                if element.Exists(maxSearchSeconds=1):
                    self._element = element
                    return element

            except Exception:
                pass

            time.sleep(0.5)

        # 构建查找条件描述
        criteria_desc = []
        if self.name: criteria_desc.append(f"Name='{self.name}'")
        if self.automation_id: criteria_desc.append(f"AutomationId='{self.automation_id}'")
        if self.class_name: criteria_desc.append(f"ClassName='{self.class_name}'")

        criteria_str = ", ".join(criteria_desc) if criteria_desc else "无特定条件"
        raise ElementNotFoundError(self.control_type.__name__, criteria_str)

    def click(self, click_type="left", ratio_x=0.5, ratio_y=0.5, wait_after=1.0):
        """
        点击元素

        参数说明：
        - click_type: 点击类型 ("left", "right", "double")
        - ratio_x: 点击位置的X比例 (0.0-1.0)
        - ratio_y: 点击位置的Y比例 (0.0-1.0)
        - wait_after: 点击后等待时间(秒)

        使用示例：
        # 点击按钮的中心位置
        UIElement(auto.ButtonControl, name="确定").click()
        """
        element = self.find()

        # 检查元素是否可交互
        rect = element.BoundingRectangle
        if rect.width() <= 0 or rect.height() <= 0:
            raise ElementNotInteractableError(f"元素大小无效: {rect}")

        if rect.left == 0 and rect.top == 0 and rect.right == 0 and rect.bottom == 0:
            raise ElementNotInteractableError("元素位置无效")

        if element.IsOffscreen:
            raise ElementNotInteractableError("元素在屏幕外")

        try:
            if click_type == "left":
                element.Click(ratioX=ratio_x, ratioY=ratio_y)
            elif click_type == "right":
                element.RightClick(ratioX=ratio_x, ratioY=ratio_y)
            elif click_type == "double":
                element.DoubleClick(ratioX=ratio_x, ratioY=ratio_y)

            time.sleep(wait_after)

        except Exception as e:
            raise ElementNotInteractableError(f"点击元素失败: {str(e)}")

    def input_text(self, text, clear_first=True, wait_after=0.5):
        """
        向元素输入文本 (适用于EditControl等可输入元素)

        参数说明：
        - text: 要输入的文本
        - clear_first: 是否先清空原有文本
        - wait_after: 输入后等待时间(秒)

        使用示例：
        # 向搜索框输入文本
        UIElement(auto.EditControl, name="搜索").input_text("关键词")
        """
        element = self.find()

        try:
            # 先点击元素获取焦点
            self.click(wait_after=0.5)

            # 清空原有文本
            if clear_first:
                element.SendKeys("{Ctrl}a{Delete}")
                time.sleep(0.5)

            # 输入新文本
            element.SendKeys(text)
            time.sleep(wait_after)

        except Exception as e:
            raise ElementNotInteractableError(f"输入文本失败: {str(e)}")

    def get_info(self) -> Dict[str, Any]:
        """
        获取元素的详细信息

        返回值: 包含元素信息的字典

        使用示例：
        # 获取按钮的详细信息
        info = UIElement(auto.ButtonControl, name="确定").get_info()
        print(info["name"], info["position"])
        """
        element = self.find()

        try:
            rect = element.BoundingRectangle
            return {
                "name": element.Name,
                "automation_id": element.AutomationId,
                "class_name": element.ClassName,
                "control_type": element.ControlTypeName,
                "position": (rect.left, rect.top, rect.right, rect.bottom),
                "size": (rect.width(), rect.height()),
                "is_enabled": element.IsEnabled,
                "is_visible": not element.IsOffscreen
            }
        except Exception as e:
            raise ElementNotFoundError(f"获取元素信息失败: {str(e)}")

    def wait_until(self, condition: Callable[[], bool], timeout=30, interval=0.5):
        """
        等待条件满足

        参数说明：
        - condition: 等待的条件函数，返回True表示条件满足
        - timeout: 超时时间(秒)
        - interval: 检查间隔(秒)

        使用示例：
        # 等待元素变为可点击状态
        element.wait_until(lambda: element.is_clickable())
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if condition():
                return True
            time.sleep(interval)

        raise TimeoutError("等待条件满足", timeout)

    def is_clickable(self) -> bool:
        """
        检查元素是否可点击

        返回值: 可点击返回True，否则返回False
        """
        try:
            element = self.find(timeout=1)
            rect = element.BoundingRectangle

            return (rect.width() > 0 and rect.height() > 0 and
                    not (rect.left == 0 and rect.top == 0 and
                         rect.right == 0 and rect.bottom == 0) and
                    not element.IsOffscreen)
        except:
            return False

    def exists(self, timeout=1) -> bool:
        """
        检查元素是否存在

        参数说明：
        - timeout: 检查超时时间(秒)

        返回值: 存在返回True，否则返回False
        """
        try:
            self.find(timeout=timeout)
            return True
        except ElementNotFoundError:
            return False