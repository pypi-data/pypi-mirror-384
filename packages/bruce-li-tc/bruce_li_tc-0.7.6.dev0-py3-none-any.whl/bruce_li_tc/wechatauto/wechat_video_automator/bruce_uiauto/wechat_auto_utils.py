
import uiautomation as auto
from .bruce_auto_log import library_logger

class WeChat_Auto_utils:
    def __init__(self):
        pass

    def find_sibling_tabs(self,name: str):
        """
        查找指定名称的标签页的兄弟节点（上一个和下一个）。
        :param name: 要查找的标签页的名称
        :return:
        """
        try:
            # 首先定位到目标标签页控件
            current_tab = auto.TabItemControl(Name=name)

            if not current_tab.Exists(maxSearchSeconds=10):
                library_logger.info(f"未找到名为 '{name}' 的标签页控件")
                return None, None

            # 获取上一个兄弟节点
            previous_sibling = current_tab.GetPreviousSiblingControl()

            # 获取下一个兄弟节点
            next_sibling = current_tab.GetNextSiblingControl()

            """
            用以下方法来导航和查找控件：
            获取上一个兄弟节点       control.GetPreviousSiblingControl()  返回同一层级中位于当前控件之前的控件对象，若不存在则返回 None
            获取下一个兄弟节点       control.GetNextSiblingControl()     返回同一层级中位于当前控件之后的控件对象，若不存在则返回 None
            获取所有直接子节点的列表  control.GetChildren()               返回一个包含所有直接子控件对象的列表  
            获取父节点             control.GetParentControl()           返回当前控件的父控件对象
            """
            library_logger.info(f"TAB标签页的上一个兄弟节点previous_sibling:{previous_sibling},下一个兄弟节点next_sibling:{next_sibling}")
            return previous_sibling, next_sibling
        except Exception as e:
            library_logger.info(f"查找兄弟节点时出错: {e}")
            return None, None
    def find_and_filter_children(self,parent_control, target_name: str = None, is_click=True,is_click_back=False):
        """
        查找父控件的所有直接子节点，并根据条件进行筛选。
        :param parent_control:父控件对象
        :param target_name:(可选) 要筛选的子节点名称。如果为None，则打印所有子节点信息。
        :return:
        """
        try:
            # 获取父控件的所有直接子节点
            children = parent_control.GetChildren()
            library_logger.info(f"  正在检查父控件 '{parent_control.Name}' 的子节点 (共{len(children)}个)...")

            for child in children:
                # 如果没有指定目标名称，则打印所有子节点信息
                if target_name is None:
                    library_logger.info(f"    - 子节点名称: '{child.Name}', 控件类型: '{child.ControlTypeName}'")
                else:
                    # 如果指定了目标名称，则进行匹配
                    if child.Name == target_name:
                        library_logger.info(f"    ✓ 找到目标子节点: '{child.Name}', 控件类型: '{child.ControlTypeName}'")
                        if is_click:
                            if is_click_back:
                                self.backstage_click(child)
                            else:
                                child.Click()
                                #self.default_click(child)

                        # child.Click()
                        return child  # 如果需要返回找到的控件，可以取消注释
        except Exception as e:
            library_logger.info(f"  获取或遍历子节点时发生错误: {e}")
    def is_control_clickable(self,control):
        """
         综合判断控件是否可点击
        Args:
            control: uiautomation 控件对象
        Returns:
            bool: True 表示可点击，False 表示不可点击
        """
        if control is None:
            return False
            # 检查控件是否存在
        if not control.Exists(maxSearchSeconds=1):
            return False
        # 获取控件的边界矩形
        rect = control.BoundingRectangle
        # 检查边界矩形是否有效（非零且宽度高度为正）
        if rect.width() <= 0 or rect.height() <= 0:
            return False
        if rect.left == 0 and rect.top == 0 and rect.right == 0 and rect.bottom == 0:
            return False
        # 检查控件是否在屏幕外
        if control.IsOffscreen:
            return False
        return True

    def default_click(self,control):
        """
        默认点击控件
        Args:
            control: uiautomation 控件对象
        Returns:
            None
        """
        if self.is_control_clickable(control):
            control.Click()
        else:
            library_logger.info(f"控件 '{control.Name}' 不可点击")
    def backstage_click(self,control):
        """
        后台点击控件
        :param control:
        :return:
        """

        legacy_pattern = control.GetLegacyIAccessiblePattern()  # 获取 LegacyIAccessiblePattern 对象
        legacy_pattern.DoDefaultAction()  # 触发默认操作（点击）