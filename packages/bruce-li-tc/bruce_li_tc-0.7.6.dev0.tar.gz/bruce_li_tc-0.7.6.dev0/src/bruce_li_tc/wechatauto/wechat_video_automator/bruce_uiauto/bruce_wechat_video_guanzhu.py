import time
import uiautomation as auto
from .bruce_auto_log import library_logger

class VideoChannelOperator:
    """微信视频号关注/取消关注操作类"""

    def __init__(self, user_tab_name:str):
        self.username = user_tab_name
        self.user_document_control = auto.DocumentControl(searchDepth=8, Name=user_tab_name)

    def _backstage_click(self, control):
        """
        后台点击控件
        :param control: 要点击的控件对象
        """
        try:
            legacy_pattern = control.GetLegacyIAccessiblePattern()
            legacy_pattern.DoDefaultAction()
            return True
        except Exception as e:
            library_logger.warning(f"点击控件失败: {e}")
            return False

    def _find_visible_button(self, button_name, found_index=1):
        """
        查找可见的按钮控件（基于BoundingRectangle判断）
        :param button_name: 按钮名称
        :param found_index: 查找索引
        :return: 可见的按钮控件或None
        """
        try:
            button = auto.ButtonControl(
                searchFromControl=self.user_document_control,
                Name=button_name,
                foundIndex=found_index
            )

            if button.Exists(maxSearchSeconds=2):
                rect = button.BoundingRectangle
                # 检查边界矩形是否有效（不在(0,0,0,0)位置）
                if not (rect.left == 0 and rect.top == 0 and
                        rect.right == 0 and rect.bottom == 0):
                    return button

            return None
        except Exception as e:
            print(f"查找按钮失败: {e}")
            return None

    def _close_current_tab(self):
        """关闭当前标签页"""
        try:
            current_tab = auto.TabItemControl(Name=self.username)
            library_logger.debug(f"current_tab: {current_tab}")
            if current_tab:
                close_btn = auto.ButtonControl(searchFromControl=current_tab, Name="关闭")
                if close_btn.Exists(maxSearchSeconds=2):
                    self._backstage_click(close_btn)
                    return True
        except Exception as e:
            library_logger.debug(f"关闭标签页失败: {e}")
        return False

    def _execute_unfollow_operation(self):
        """
        执行取消关注操作
        :return: 操作结果 (True/False)
        """
        try:
            # 查找"已关注"按钮
            followed_button = self._find_visible_button("已关注", 1)
            if not followed_button:
                followed_button = self._find_visible_button("已关注", 2)

            if followed_button:
                # 点击"已关注"按钮
                if self._backstage_click(followed_button):
                    # 等待弹出菜单出现，然后查找"不再关注"选项
                    unfollow_option = auto.TextControl(
                        searchFromControl=self.user_document_control,
                        Name="不再关注"
                    )
                    if unfollow_option.Exists(maxSearchSeconds=3):
                        if self._backstage_click(unfollow_option):
                            library_logger.debug("成功取消关注用户")
                            return True
            return False
        except Exception as e:
            library_logger.warning(f"取消关注操作失败: {e}")
            return False
    def execute_follow_operation(self,enable_unfollow=False):
        """
        执行关注操作主逻辑
        :param enable_unfollow: 是否启用取消关注功能
        :return: 操作结果 (True/False)
        """
        # 首先尝试查找可见的"关注"按钮
        follow_button = self._find_visible_button("关注", 1)
        if not follow_button:
            follow_button = self._find_visible_button("关注", 2)

        if follow_button:
            # 执行关注操作
            if self._backstage_click(follow_button):
                library_logger.debug("成功关注用户")
                time.sleep(0.1)
                self._close_current_tab()
                return True

        # 查找已关注状态（取消关注逻辑，按你要求暂不执行）
        followed_button = self._find_visible_button("已关注", 1)
        if not followed_button:
            followed_button = self._find_visible_button("已关注", 2)

        if followed_button:
            if enable_unfollow:
                #执行取消关注操作
                if self._execute_unfollow_operation():
                    time.sleep(0.1)
                    self._close_current_tab()
                    return True
            else:
                library_logger.debug("用户已关注，跳过操作（取消关注功能未启用）")
                time.sleep(0.1)
                self._close_current_tab()
                return True
        print("未找到可操作的关注按钮")
        return False
