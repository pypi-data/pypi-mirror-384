import uiautomation as auto
import time
from typing import Optional
from .core import UIElement
from .exceptions import ElementNotInteractableError


class ElementActions:
    """
    元素操作工具类 - 提供高级操作功能
    """

    @staticmethod
    def scroll_element(element: UIElement, direction="down", amount=1, wait_after=0.5):
        """
        滚动元素 (适用于支持滚动的元素)

        参数说明：
        - element: 要滚动的元素
        - direction: 滚动方向 ("up", "down", "left", "right")
        - amount: 滚动次数
        - wait_after: 每次滚动后等待时间(秒)

        使用示例：
        # 向下滚动列表
        ElementActions.scroll_element(list_element, "down", 3)
        """
        ui_element = element.find()

        try:
            # 获取滚动模式
            scroll_pattern = ui_element.GetScrollPattern()
            if not scroll_pattern:
                raise ElementNotInteractableError("元素不支持滚动")

            # 执行滚动
            for i in range(amount):
                if direction == "up":
                    scroll_pattern.ScrollUp()
                elif direction == "down":
                    scroll_pattern.ScrollDown()
                elif direction == "left":
                    scroll_pattern.ScrollLeft()
                elif direction == "right":
                    scroll_pattern.ScrollRight()

                time.sleep(wait_after)

        except Exception as e:
            raise ElementNotInteractableError(f"滚动元素失败: {str(e)}")

    @staticmethod
    def highlight_element(element: UIElement, duration=2, color="red"):
        """
        高亮显示元素 (用于调试)

        参数说明：
        - element: 要高亮显示的元素
        - duration: 高亮持续时间(秒)
        - color: 高亮颜色
        """
        ui_element = element.find()

        try:
            # 保存原始边框
            original_border = getattr(ui_element, "_original_border", None)

            # 设置高亮边框
            if color == "red":
                ui_element.SetBorderColor(0xFFFF0000)  # 红色
            elif color == "green":
                ui_element.SetBorderColor(0xFF00FF00)  # 绿色
            elif color == "blue":
                ui_element.SetBorderColor(0xFF0000FF)  # 蓝色

            ui_element.SetBorderWidth(3)

            # 等待一段时间后恢复
            time.sleep(duration)

            # 恢复原始边框
            if original_border:
                ui_element.SetBorderColor(original_border["color"])
                ui_element.SetBorderWidth(original_border["width"])
            else:
                ui_element.SetBorderColor(0x00000000)  # 透明
                ui_element.SetBorderWidth(0)

        except Exception as e:
            print(f"高亮元素失败: {str(e)}")

    @staticmethod
    def capture_element_screenshot(element: UIElement, file_path: str):
        """
        捕获元素的屏幕截图

        参数说明：
        - element: 要截图的元素
        - file_path: 截图保存路径
        """
        ui_element = element.find()

        try:
            rect = ui_element.BoundingRectangle
            if rect.width() <= 0 or rect.height() <= 0:
                raise ElementNotInteractableError("元素大小无效")

            # 这里需要实现截图逻辑，可以使用pyautogui或其他截图库
            # 示例代码（需要安装pyautogui）:
            import pyautogui
            screenshot = pyautogui.screenshot(region=(rect.left, rect.top, rect.width(), rect.height()))
            screenshot.save(file_path)

            print(f"元素截图已保存到: {file_path}")

        except Exception as e:
            raise ElementNotInteractableError(f"捕获元素截图失败: {str(e)}")

    @staticmethod
    def drag_and_drop(source_element: UIElement, target_element: UIElement, duration=1.0):
        """
        拖放元素

        参数说明：
        - source_element: 源元素
        - target_element: 目标元素
        - duration: 拖放持续时间(秒)
        """
        source = source_element.find()
        target = target_element.find()

        try:
            # 获取元素中心点坐标
            source_rect = source.BoundingRectangle
            target_rect = target.BoundingRectangle

            source_center_x = (source_rect.left + source_rect.right) // 2
            source_center_y = (source_rect.top + source_rect.bottom) // 2

            target_center_x = (target_rect.left + target_rect.right) // 2
            target_center_y = (target_rect.top + target_rect.bottom) // 2

            # 执行拖放操作
            auto.DragDrop(source_center_x, source_center_y, target_center_x, target_center_y, duration)

        except Exception as e:
            raise ElementNotInteractableError(f"拖放元素失败: {str(e)}")