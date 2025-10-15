import time
import uiautomation as auto
from typing import List, Optional,Dict, Any
from .bruce_wechat_video_guanzhu import VideoChannelOperator
from .bruce_auto_log import library_logger

"""
点击头像的几种情况
不能点击用户名字，不弹出个人资料
1.点击没有反应，进入不了个人主页
2.点击头像显示个人资料，点击视频号，进入个人主页
3.点击头像直接进入主页了
"""
class AvatarClickHandler:
    """头像点击处理器，封装点击头像后的各种情况判断"""

    @staticmethod
    def avatar_backstage_click(control):
        try:
            legacy_pattern = control.GetLegacyIAccessiblePattern()
            legacy_pattern.DoDefaultAction()  # 触发默认操作（点击）
        except Exception as e:
            print(f"DoDefaultAction() 执行失败: {e}")



    @staticmethod
    def monitor_tab_status(tab_control_name: str = "cdn_搜索",seconds: int = 10) -> Optional[List[auto.Control]]:
        """
        监控Tab页面状态，在超时时间内等待页面加载完成
        :param tab_control_name: Tab控件名称，默认"cdn_搜索"
        :param seconds: 超时时间（秒），默认10秒
        :return: 加载完成后的tabs列表，超时返回None
        """
        loading_texts = ["正在加载", "视频号"]
        start_time = time.time()
        last_state = None

        while True:
            if time.time() - start_time > seconds:
                return None
            try:
                item_tab = auto.TabItemControl(Name=tab_control_name)
                parent = UINavigationHelper.get_father(item_tab)
                tabs = parent.GetChildren()
                if not tabs:
                    continue
                current_tab = tabs[-1]
                current_state = current_tab.Name if current_tab else "未知"

                if current_state != last_state:
                    last_state = current_state

                if current_state in loading_texts:
                    time.sleep(0.5)
                    continue
                else:
                    time.sleep(0.2)
                    tabs_refreshed = parent.GetChildren()
                    if tabs_refreshed and tabs_refreshed[-1].Name not in loading_texts:
                        return tabs_refreshed
                    else:
                        continue
            except Exception as e:
                time.sleep(1)
                continue

    @staticmethod
    def handle_avatar_click(avatar_control: auto.Control,
                            tab_control_name: str = "cdn_搜索",
                            model: bool = True,
                            max_retries: int = 2) -> Dict[str, Any]:
        """
        处理头像点击事件并判断页面类型
        :param avatar_control: 头像控件对象
        :param tab_control_name: Tab控件名称，默认"cdn_搜索"
        :param user_name: 用户名，用于结果记录
        :param model:是否后台运行,True是后台运行，False是前台运行
        :param max_retries: 最大重试次数，默认2次
        :return: 包含处理结果的字典
        """
        avatar_control = UINavigationHelper.get_prev_nth(avatar_control, 2).GetChildren()[0]
        result = {
            "success": False,
            "type": "unknown",
            "message": "",
        }
        for attempt in range(max_retries):
            try:
                library_logger.debug(f"第 {attempt + 1} 次尝试点击头像")

                # 使用传入的头像控件进行点击
                if not avatar_control or not avatar_control.Exists(maxSearchSeconds=0.5):
                    result["type"] = "no_avatar"
                    result["message"] = "头像控件不存在或不可用"
                    return result

                if model:
                    AvatarClickHandler.avatar_backstage_click(avatar_control)
                else:
                    avatar_control.Click()
                # 这里不能使用后台点击操作，修改后又可以了
                time.sleep(0.5)  # 等待页面响应

                # 监控页面状态，传入Tab控件名称
                tabs = AvatarClickHandler.monitor_tab_status(tab_control_name)

                # 判断页面类型
                if len(tabs) == 4:
                    result["success"] = True
                    result["type"] = "direct_homepage"
                    result["message"] = "直接打开主页成功"
                    library_logger.debug("直接打开主页成功")
                    # 执行关注操作
                    VideoChannelOperator(tabs[-1].Name).execute_follow_operation()
                    return result  # 成功，直接返回

                elif len(tabs) == 3:
                    temp_item_video_contorl_name = tabs[-1].Name
                    temp_item_video_contorl = auto.DocumentControl(Name=temp_item_video_contorl_name)
                    video_account_1 = auto.TextControl(searchFromControl=temp_item_video_contorl,
                                                       Name="视频号",
                                                       foundIndex=1)

                    if video_account_1.Exists(maxSearchSeconds=2):
                        video_account_2 = auto.TextControl(searchFromControl=temp_item_video_contorl, Name="视频号",
                                                           foundIndex=2)
                        if video_account_2.Exists(maxSearchSeconds=3):
                            if model:
                                AvatarClickHandler.avatar_backstage_click(video_account_2)
                            else:
                                video_account_2.Click()
                            time.sleep(0.5)

                            # 获取更新后的tabs
                            new_tabs = AvatarClickHandler.monitor_tab_status(tab_control_name)
                            if len(new_tabs) == 4:
                                result["success"] = True
                                result["type"] = "profile_to_homepage"
                                result["message"] = "通过个人资料打开主页成功"
                                library_logger.debug("通过个人资料打开主页成功")
                                library_logger.debug(f"updated_tabs{(new_tabs[-1].Name)}")
                                VideoChannelOperator(new_tabs[-1].Name).execute_follow_operation()
                                return result  # 成功，直接返回
                            else:
                                # 点击视频号后仍无法打开主页，准备重试
                                if attempt < max_retries - 1:
                                    library_logger.debug("点击视频号后仍无法打开主页，准备重试")
                                    time.sleep(1)  # 等待一段时间再重试
                                    continue
                                else:
                                    result["type"] = "cannot_open"
                                    result["message"] = "点击视频号后仍无法打开主页"
                        else:
                            # 找不到第二个视频号控件，准备重试
                            if attempt < max_retries - 1:
                                library_logger.debug("找不到第二个视频号控件，准备重试")
                                time.sleep(1)  # 等待一段时间再重试
                                continue
                            else:
                                result["type"] = "cannot_open"
                                result["message"] = "找不到第二个视频号控件"
                    else:
                        # 找不到个人资料视频号控件，准备重试
                        if attempt < max_retries - 1:
                            library_logger.debug("找不到个人资料视频号控件，准备重试")
                            time.sleep(1)  # 等待一段时间再重试
                            continue
                        else:
                            result["type"] = "cannot_open"
                            result["message"] = "找不到个人资料视频号控件"
                            library_logger.warning("找不到个人资料，打开个人主页失败")
                else:
                    result["type"] = "unknown_layout"
                    result["message"] = "未知的页面布局"
                    # 未知布局也重试一次
                    if attempt < max_retries - 1:
                        library_logger.debug("未知页面布局，准备重试")
                        time.sleep(1)
                        continue

                # 如果执行到这里，说明当前尝试已经完成且不需要重试，直接跳出循环
                break

            except Exception as e:
                result["message"] = f"处理过程中出现异常: {str(e)}"
                # 异常情况下也重试
                if attempt < max_retries - 1:
                    library_logger.debug(f"出现异常，准备重试: {str(e)}")
                    time.sleep(1)
                    continue
        library_logger.debug(f"最终结果: {result}")
        return result

class UINavigationHelper:
    """UI控件导航助手类，封装常用控件关系查找方法"""

    @staticmethod
    def get_prev(control: auto.Control) -> Optional[auto.Control]:
        """
        获取上一个兄弟节点
        :param control: 当前控件对象
        :return: 同一层级中位于当前控件之前的控件对象，若不存在则返回 None
        """
        try:
            sibling = control.GetPreviousSiblingControl()
            return sibling if sibling and sibling.Exists(maxSearchSeconds=1) else None
        except Exception as e:
            print(f"获取上一个兄弟节点失败: {e}")
            return None

    @staticmethod
    def get_next(control: auto.Control) -> Optional[auto.Control]:
        """
        获取下一个兄弟节点
        :param control: 当前控件对象
        :return: 同一层级中位于当前控件之后的控件对象，若不存在则返回 None
        """
        try:
            sibling = control.GetNextSiblingControl()
            return sibling if sibling and sibling.Exists(maxSearchSeconds=1) else None
        except Exception as e:
            print(f"获取下一个兄弟节点失败: {e}")
            return None

    @staticmethod
    def get_all_children(control: auto.Control) -> List[auto.Control]:
        """
        获取所有直接子节点的列表
        :param control: 父控件对象
        :return: 包含所有直接子控件对象的列表
        """
        try:
            children = control.GetChildren()
            return [child for child in children if child and child.Exists(maxSearchSeconds=1)]
        except Exception as e:
            print(f"获取子节点列表失败: {e}")
            return []

    @staticmethod
    def get_father(control: auto.Control) -> Optional[auto.Control]:
        """
        获取父节点
        :param control: 当前控件对象
        :return: 当前控件的父控件对象，若不存在则返回 None
        """
        try:
            parent = control.GetParentControl()
            return parent if parent and parent.Exists(maxSearchSeconds=1) else None
        except Exception as e:
            print(f"获取父节点失败: {e}")
            return None

    @staticmethod
    def get_prev_nth(control: auto.Control, n: int = 1) -> Optional[auto.Control]:
        """
        获取前第n个兄弟节点
        :param control: 当前控件对象
        :param n: 向前追溯的兄弟节点数量 (n>=1)
        :return: 同一层级中位于当前控件之前的第n个控件对象，若不存在则返回 None
        """
        if n < 1:
            return control

        try:
            current = control
            for _ in range(n):
                sibling = current.GetPreviousSiblingControl()
                if not sibling or not sibling.Exists(maxSearchSeconds=0.5):
                    return None
                current = sibling
            return current
        except Exception as e:
            print(f"获取前第{n}个兄弟节点失败: {e}")
            return None

    @staticmethod
    def get_next_nth(control: auto.Control, n: int = 1) -> Optional[auto.Control]:
        """
        获取后第n个兄弟节点
        :param control: 当前控件对象
        :param n: 向后追溯的兄弟节点数量 (n>=1)
        :return: 同一层级中位于当前控件之后的第n个控件对象，若不存在则返回 None
        """
        if n < 1:
            return control

        try:
            current = control
            for _ in range(n):
                sibling = current.GetNextSiblingControl()
                if not sibling or not sibling.Exists(maxSearchSeconds=1):
                    return None
                current = sibling
            return current
        except Exception as e:
            print(f"获取后第{n}个兄弟节点失败: {e}")
            return None



