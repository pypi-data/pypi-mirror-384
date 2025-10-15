import time
from typing import Callable
from .exceptions import TimeoutError


class WaitConditions:
    """
    等待条件工具类 - 提供常用的等待条件
    """

    @staticmethod
    def wait_for_condition(condition: Callable[[], bool],
                           timeout=30,
                           interval=0.5,
                           condition_desc="条件"):
        """
        等待条件满足

        参数说明：
        - condition: 等待的条件函数，返回True表示条件满足
        - timeout: 超时时间(秒)
        - interval: 检查间隔(秒)
        - condition_desc: 条件描述 (用于错误信息)

        使用示例：
        # 等待元素变为可点击状态
        WaitConditions.wait_for_condition(
            lambda: element.is_clickable(),
            timeout=10,
            condition_desc="元素可点击"
        )
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if condition():
                return True
            time.sleep(interval)

        raise TimeoutError(f"等待{condition_desc}", timeout)

    @staticmethod
    def wait_for_element(element, timeout=30):
        """
        等待元素存在

        参数说明：
        - element: 要等待的元素
        - timeout: 超时时间(秒)

        使用示例：
        # 等待按钮出现
        WaitConditions.wait_for_element(button_element, timeout=10)
        """

        def condition():
            try:
                element.find(timeout=1)
                return True
            except:
                return False

        return WaitConditions.wait_for_condition(
            condition, timeout, 0.5, f"元素存在: {element.name}"
        )

    @staticmethod
    def wait_for_element_clickable(element, timeout=30):
        """
        等待元素可点击

        参数说明：
        - element: 要等待的元素
        - timeout: 超时时间(秒)

        使用示例：
        # 等待按钮可点击
        WaitConditions.wait_for_element_clickable(button_element, timeout=10)
        """

        def condition():
            return element.is_clickable()

        return WaitConditions.wait_for_condition(
            condition, timeout, 0.5, f"元素可点击: {element.name}"
        )

    @staticmethod
    def wait_for_element_visible(element, timeout=30):
        """
        等待元素可见

        参数说明：
        - element: 要等待的元素
        - timeout: 超时时间(秒)

        使用示例：
        # 等待按钮可见
        WaitConditions.wait_for_element_visible(button_element, timeout=10)
        """

        def condition():
            try:
                element_info = element.get_info()
                return element_info["is_visible"]
            except:
                return False

        return WaitConditions.wait_for_condition(
            condition, timeout, 0.5, f"元素可见: {element.name}"
        )

    @staticmethod
    def wait_for_element_enabled(element, timeout=30):
        """
        等待元素启用

        参数说明：
        - element: 要等待的元素
        - timeout: 超时时间(秒)

        使用示例：
        # 等待按钮启用
        WaitConditions.wait_for_element_enabled(button_element, timeout=10)
        """

        def condition():
            try:
                element_info = element.get_info()
                return element_info["is_enabled"]
            except:
                return False

        return WaitConditions.wait_for_condition(
            condition, timeout, 0.5, f"元素启用: {element.name}"
        )