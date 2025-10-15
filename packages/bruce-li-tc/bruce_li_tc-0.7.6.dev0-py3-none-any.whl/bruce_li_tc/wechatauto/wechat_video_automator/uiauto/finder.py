import uiautomation as auto
import time
from typing import List, Optional, Dict
from .core import UIElement
from .exceptions import ElementNotFoundError


class ElementFinder:
    """
    元素查找工具类 - 提供高级查找功能
    """

    @staticmethod
    def find_children(parent: UIElement, control_type=None,
                      name_pattern=None) -> List[UIElement]:
        """
        查找父元素下的所有子元素

        参数说明：
        - parent: 父元素对象
        - control_type: 要查找的子元素类型 (可选)
        - name_pattern: 名称模式 (可选，支持部分匹配)

        返回值: 找到的子元素列表

        使用示例：
        # 查找窗口中的所有按钮
        buttons = ElementFinder.find_children(window, auto.ButtonControl)
        """
        try:
            parent_element = parent.find()
            children = parent_element.GetChildren()
            result = []

            for child in children:
                # 按类型过滤
                if control_type and not isinstance(child, control_type):
                    continue

                # 按名称模式过滤
                if name_pattern and name_pattern not in child.Name:
                    continue

                # 创建UIElement对象
                child_element = UIElement(
                    control_type=type(child),
                    name=child.Name,
                    automation_id=child.AutomationId,
                    class_name=child.ClassName,
                    parent=parent_element
                )
                child_element._element = child
                result.append(child_element)

            return result
        except Exception as e:
            raise ElementNotFoundError("子元素", f"父元素: {parent.get_info()}")

    @staticmethod
    def find_by_tree_path(start_element: UIElement, path: List[dict]) -> UIElement:
        """
        按照元素树路径查找元素

        参数说明：
        - start_element: 起始元素
        - path: 路径列表，每个元素是包含查找条件的字典

        返回值: 找到的元素对象

        使用示例：
        # 按照路径查找: 窗口 -> 面板 -> 按钮
        button = ElementFinder.find_by_tree_path(
            start_element=window,
            path=[
                {"control_type": auto.PaneControl, "name": "导航面板"},
                {"control_type": auto.ButtonControl, "name": "视频号按钮"}
            ]
        )
        """
        current = start_element.find()

        for step in path:
            try:
                control_type = step.get("control_type")
                name = step.get("name")
                automation_id = step.get("automation_id")
                class_name = step.get("class_name")
                search_depth = step.get("search_depth", 1)

                # 创建临时UIElement进行查找
                temp_element = UIElement(
                    control_type=control_type,
                    name=name,
                    automation_id=automation_id,
                    class_name=class_name,
                    parent=current,
                    search_depth=search_depth
                )

                current = temp_element.find()
            except Exception as e:
                step_desc = f"{step.get('control_type', '未知')} '{step.get('name', '未知')}'"
                raise ElementNotFoundError("路径元素", f"步骤: {step_desc}")

        # 返回最后一个找到的元素
        last_element = UIElement(
            control_type=type(current),
            name=current.Name,
            automation_id=current.AutomationId,
            class_name=current.ClassName,
            parent=current.GetParentControl() if current.GetParentControl() else None
        )
        last_element._element = current
        return last_element

    @staticmethod
    def find_all(control_type, name_pattern=None, parent=None, timeout=10) -> List[UIElement]:
        """
        查找所有匹配条件的元素

        参数说明：
        - control_type: 控件类型
        - name_pattern: 名称模式 (可选，支持部分匹配)
        - parent: 父元素对象 (可选)
        - timeout: 查找超时时间(秒)

        返回值: 找到的元素列表
        """
        start_time = time.time()
        result = []

        while time.time() - start_time < timeout:
            try:
                if parent:
                    parent_element = parent.find()
                    elements = parent_element.GetChildren()
                else:
                    # 全局查找
                    if name_pattern:
                        # 使用FindAll查找所有匹配的元素
                        elements = []
                        all_elements = auto.GetRootControl().GetChildren()
                        for element in all_elements:
                            if isinstance(element, control_type) and name_pattern in element.Name:
                                elements.append(element)
                    else:
                        # 使用控件类型查找
                        elements = control_type.GetMultiple()

                for element in elements:
                    # 按名称模式过滤
                    if name_pattern and name_pattern not in element.Name:
                        continue

                    # 创建UIElement对象
                    ui_element = UIElement(
                        control_type=type(element),
                        name=element.Name,
                        automation_id=element.AutomationId,
                        class_name=element.ClassName,
                        parent=parent.find() if parent else None
                    )
                    ui_element._element = element
                    result.append(ui_element)

                if result:
                    return result

            except Exception:
                pass

            time.sleep(0.5)

        return result