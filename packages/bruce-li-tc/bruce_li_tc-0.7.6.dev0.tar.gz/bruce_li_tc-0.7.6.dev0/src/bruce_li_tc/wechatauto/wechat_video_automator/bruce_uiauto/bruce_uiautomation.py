from typing import List, Dict, Any
import pyautogui
import uiautomation as auto
import time
import subprocess
from typing import Optional
import importlib.resources
from .bruce_auto_log import library_logger
import re
from datetime import datetime, timedelta
from .bruce_random import FairSelector
from .wechat_auto_utils import WeChat_Auto_utils
import cProfile
import pstats
from io import StringIO
from enum import Enum
from enum import auto as enum_auto
from .bruce_wecaht_video_click_user import AvatarClickHandler

class OperationState(Enum):
    IDLE = enum_auto()      # 空闲状态，可滚动
    REPLYING = enum_auto()  # 回复中
    FOLLOWING = enum_auto() # 关注中
    UNFOLDING = enum_auto() # 展开折叠评论中
    SCROLLING= enum_auto()    # 滚动中

class Automator_utils:

    @staticmethod
    def _get_control_type_name(control_type: int) -> str:
        """
        将控件类型ID转换为可读的名称
        """
        # 使用控件类型的整数值进行映射，避免直接访问ControlType的属性
        control_type_map = {
            50000: "Button",
            50001: "Calendar",
            50002: "CheckBox",
            50003: "ComboBox",
            50004: "Custom",
            50005: "DataGrid",
            50006: "DataItem",
            50007: "Document",
            50008: "Edit",
            50009: "Group",
            50010: "Header",
            50011: "HeaderItem",
            50012: "Hyperlink",
            50013: "Image",
            50014: "List",
            50015: "ListItem",
            50016: "Menu",
            50017: "MenuBar",
            50018: "MenuItem",
            50019: "Pane",
            50020: "ProgressBar",
            50021: "RadioButton",
            50022: "ScrollBar",
            50023: "SemanticZoom",
            50024: "Separator",
            50025: "Slider",
            50026: "Spinner",
            50027: "SplitButton",
            50028: "StatusBar",
            50029: "Tab",
            50030: "TabItem",
            50031: "Table",
            50032: "Text",
            50033: "Thumb",
            50034: "TitleBar",
            50035: "ToolBar",
            50036: "ToolTip",
            50037: "Tree",
            50038: "TreeItem",
            50039: "Window"
        }

        return control_type_map.get(control_type, f"Unknown({control_type})")
    @staticmethod
    def _safe_get_control_attribute(control, attr_name, default=None):
        try:
            return getattr(control, attr_name)
        except Exception:
            return default
    @staticmethod
    def explore_controls(wechat_window, max_depth: int = 5) -> List[Dict[str, Any]]:
        """
        探索微信窗口中的所有控件，返回控件信息列表

        Args:
            max_depth: 最大探索深度

        Returns:
            包含控件信息的字典列表
        """
        if not wechat_window:
            pass

        controls_info = []

        def _explore_recursive(parent, depth):
            if depth > max_depth:
                return

            try:
                children = parent.GetChildren()
                for child in children:
                    try:
                        # 获取控件信息
                        control_info = {
                            'depth': depth,
                            'name': Automator_utils._safe_get_control_attribute(child, 'Name', ''),
                            'control_type': Automator_utils._get_control_type_name(
                                Automator_utils._safe_get_control_attribute(child, 'ControlType', 0)),
                            'automation_id': Automator_utils._safe_get_control_attribute(child, 'AutomationId', ''),
                            'class_name': Automator_utils._safe_get_control_attribute(child, 'ClassName', ''),
                            'is_enabled': Automator_utils._safe_get_control_attribute(child, 'IsEnabled', False),
                            'is_visible': not Automator_utils._safe_get_control_attribute(child, 'IsOffscreen', True),
                            'bounding_rectangle': Automator_utils._safe_get_control_attribute(child, 'BoundingRectangle', (0, 0, 0, 0)),
                            'process_id': Automator_utils._safe_get_control_attribute(child, 'ProcessId', 0),
                            'runtime_id': Automator_utils._safe_get_control_attribute(child, 'RuntimeId', []),  # 安全访问RuntimeId
                            'control': child
                        }

                        controls_info.append(control_info)

                        # 递归探索子控件
                        _explore_recursive(child, depth + 1)

                    except Exception as e:
                        # 忽略无法访问的控件
                        error_info = {
                            'depth': depth,
                            'name': f'ERROR: {str(e)}',
                            'control_type': 'Unknown',
                            'automation_id': '',
                            'class_name': '',
                            'is_enabled': False,
                            'is_visible': False,
                            'bounding_rectangle': (0, 0, 0, 0),
                            'process_id': 0,
                            'runtime_id': [],
                            'control': None
                        }
                        controls_info.append(error_info)
                        continue

            except Exception as e:
                # 处理获取子控件时的异常
                error_info = {
                    'depth': depth,
                    'name': f'ERROR getting children: {str(e)}',
                    'control_type': 'Unknown',
                    'automation_id': '',
                    'class_name': '',
                    'is_enabled': False,
                    'is_visible': False,
                    'bounding_rectangle': (0, 0, 0, 0),
                    'process_id': 0,
                    'runtime_id': [],
                    'control': None
                }
                controls_info.append(error_info)

        # 开始探索
        _explore_recursive(wechat_window, 0)
        return controls_info

    @staticmethod
    def log_control_tree(controls_info: List[Dict[str, Any]]):
        """
        以树形结构打印控件信息

        Args:
            controls_info: 控件信息列表
        """
        library_logger.info("controls_info", controls_info)
        region = None
        for info in controls_info:
            indent = "  " * info['depth']
            library_logger.info(f"{indent}[{info['control_type']}] {info['name']}")
            library_logger.info(f"{indent}  AutomationId: {info['automation_id']}")
            library_logger.info(f"{indent}  ClassName: {info['class_name']}")
            library_logger.info(f"{indent}  Enabled: {info['is_enabled']}, Visible: {info['is_visible']}")
            library_logger.info(f"{indent}  Bounds: {info['bounding_rectangle']}")
            library_logger.info(f"{indent}  ProcessId: {info['process_id']}")
            region = info['bounding_rectangle']
        return region

    @staticmethod
    def find_and_click_template(template_path, region=None, confidence=0.7, max_retries=3, retry_interval=1.0):
        """
        在屏幕上查找模板图片，找到后点击其中心位置。

        Args:
            template_path (str): 模板图片的路径
            region (tuple, optional): 搜索区域 (left, top, width, height)。默认为全屏。
            confidence (float, optional): 匹配置信度，0-1之间。越高越严格。
            max_retries (int, optional): 最大重试次数。
            retry_interval (float, optional): 重试间隔（秒）。

        Returns:
            bool: 成功找到并点击返回True，否则返回False。
        """
        for attempt in range(max_retries):
            try:
                # 使用pyautogui的locateOnScreen函数进行图像识别
                location = pyautogui.locateOnScreen(template_path, region=region, confidence=confidence)

                if location is not None:
                    center = pyautogui.center(location)
                    pyautogui.click(center)
                    library_logger.info(f"成功点击模板：{template_path}，位置：{center}")
                    return True
                else:
                    library_logger.info(f"第{attempt + 1}次尝试未找到模板：{template_path}，将在{retry_interval}秒后重试")
                    time.sleep(retry_interval)

            except pyautogui.ImageNotFoundException:
                library_logger.info(f"第{attempt + 1}次尝试未找到模板（ImageNotFoundException）：{template_path}")
                time.sleep(retry_interval)
            except Exception as e:
                library_logger.info(f"在查找模板 {template_path} 时发生未知错误: {e}")
                break

        library_logger.info(f"已达到最大重试次数 {max_retries}，未能找到并点击 {template_path}")
        return False

class WeChat_VideoData_utils:
    @staticmethod
    def format_time(input_data):
        """
        格式化各种时间格式为标准时间字符串（YYYY-MM-DD HH:MM:SS）

        参数:
            input_data: 可能是None, 空字符串, 中文日期或相对时间字符串

        返回:
            标准格式的时间字符串，或原始输入（当无法解析时）
        """
        # 处理空值情况
        if input_data is None or input_data == '':
            return input_data

        now = datetime.now()

        # 1. 处理相对时间格式（X天/小时/分钟/秒钟前）
        relative_match = re.match(r'^(\d+)(天|小时|分钟|秒钟)前$', input_data)
        if relative_match:
            num = int(relative_match.group(1))
            unit = relative_match.group(2)

            if unit == '天':
                result = now - timedelta(days=num)
            elif unit == '小时':
                result = now - timedelta(hours=num)
            elif unit == '分钟':
                result = now - timedelta(minutes=num)
            elif unit == '秒钟':
                result = now - timedelta(seconds=num)
            else:
                return input_data  # 未知单位返回原值

            return result.strftime('%Y-%m-%d %H:%M:%S')

        # 2. 处理完整中文日期（带年份）
        full_date_match = re.match(r'^(\d{4})年(\d{1,2})月(\d{1,2})日$', input_data)
        if full_date_match:
            year = int(full_date_match.group(1))
            month = int(full_date_match.group(2))
            day = int(full_date_match.group(3))

            try:
                return datetime(year, month, day).strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                return input_data  # 无效日期返回原值

        # 3. 处理简写中文日期（无年份）
        short_date_match = re.match(r'^(\d{1,2})月(\d{1,2})日$', input_data)
        if short_date_match:
            month = int(short_date_match.group(1))
            day = int(short_date_match.group(2))
            year = now.year

            try:
                # 创建日期对象并检查是否在未来
                date_obj = datetime(year, month, day)
                if date_obj > now:
                    date_obj = datetime(year - 1, month, day)
                return date_obj.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                return input_data  # 无效日期返回原值

        # 4. 其他未识别格式直接返回
        return input_data
    def extract_number_from_string(self,s):
        """
        从字符串中提取数字部分，支持整数、小数和带'万'或'万+'的数字。
        会尽量保留原始格式（如包含'万'或'万+'字），仅在无数字时返回"0"。

        参数:
            s (str): 输入的字符串，例如"喜欢，170", "分享，17万", "点赞, 8.8万", "喜欢10万+"

        返回:
            str: 提取出的数字字符串。如果没有数字则返回"0"。
        """
        # 匹配模式：数字（可能含小数点）+可能紧跟的'万'字+可能紧跟的'+'号
        pattern = r'\d+\.?\d*\s*万\+?|\d+\.?\d+|\b\d+\b'
        matches = re.findall(pattern, s)

        if not matches:
            return "0"

        # 取第一个匹配项
        matched_str = matches[0]

        # 移除数字和单位之间的任何空格（保留原始格式但规范化）
        matched_str = re.sub(r'(\d)\s*万', r'\1万', matched_str)

        return matched_str

class WeChatAutomator:
    """微信自动化示例类"""

    def __init__(self,scroll_video_comment_time: float=1.0,back_click_model: bool=False):
        """
        微信窗口和微信窗格独立分开的，微信主页面就是窗口，打开其他页面就是窗格
        """
        self.WECHAT_WINDOW = None                               #微信窗口
        self.WECHAT_PANE=None                                   #微信窗格
        self.TEXT_CONTROL= None                                 #视频号里面的"动态"文本控件
        self.IS_GLOBAL_SEARCH=False                             #是否全局搜索
        self.SEARCH_KEYWORD=None                                #视频号搜索关键字
        self.AutomatorUtils=Automator_utils()
        self.WeChat_Auto_utils=WeChat_Auto_utils()
        self.WeChat_VideoData_utils=WeChat_VideoData_utils()
        self.comment_callback = None                            #初始化回调函数为None
        self.scroll_video_comment_time=scroll_video_comment_time#评论滚动速度
        self.back_click_model=back_click_model                  #是否后台点击
        self.FairSelector_class=None                            #随机选择器类
        self.COMMENT_LIST=[]                                    #想要评论的,评论列表
        self.NEXT_SIBLING=None                                  #滚动评论所需的参数
        self.COMMENT_KEY=None                                   #评论中带这些关键字的
        self.REPLAY_COUNT = 0                                   #回复评论的数量
        self.VIDEO_LIST_DATA_CONFIG = {}
        self.CONTINUE_SRCOLL_CONTORL=  {}                       #不需要滚动的控件

    def video_list_data_config(self,
                            skip_comment,
                            comment_key,
                            comment_list,
                            comment_day,
                            comment_datetime,
                            Interval_count,
                            Interval_seconds):
        """
        给这个函数设置全局配置
        """
        self.VIDEO_LIST_DATA_CONFIG["skip_comment"]=skip_comment
        self.VIDEO_LIST_DATA_CONFIG["comment_key"] = comment_key
        self.VIDEO_LIST_DATA_CONFIG["comment_list"] = comment_list
        self.VIDEO_LIST_DATA_CONFIG["comment_day"] = comment_day
        self.VIDEO_LIST_DATA_CONFIG["comment_datetime"] = comment_datetime
        self.VIDEO_LIST_DATA_CONFIG["Interval_count"] = Interval_count
        self.VIDEO_LIST_DATA_CONFIG["Interval_seconds"] = Interval_seconds
    def start_webchat(self,wechat_path: str=r"C:\Program Files\Tencent\Weixin\Weixin.exe") -> Optional[int]:
        """
        启动微信并返回其进程PID

        Args:
            wechat_path (str): 微信客户端的完整路径

        Returns:
            Optional[int]: 成功则返回进程PID，失败则返回None
        """
        try:
            # 使用subprocess.Popen启动进程，并获取进程对象
            process = subprocess.Popen([wechat_path])
            library_logger.info(f"微信启动成功，PID: {process.pid}")
            return process.pid
        except FileNotFoundError:
            library_logger.warning(f"错误：未找到微信程序，请检查路径 '{wechat_path}' 是否正确")
        except Exception as e:
            library_logger.warning(f"启动微信时发生未知错误: {e}")
        return None
    def search_wechat(self):
        """打开微信,并激活窗口"""
        library_logger.info("查找微信窗口")
        try:
            self.WECHAT_WINDOW = auto.WindowControl(Name="微信")
            # 这里应该是启动微信的逻辑

            if not self.WECHAT_WINDOW.Exists(maxSearchSeconds=10):
                library_logger.info("未找到微信主窗口")
                return False
            else:
                library_logger.info("已找到微信主窗口")

            # 激活窗口确保可见
            self.WECHAT_WINDOW.SetFocus()
            time.sleep(1)
            return True
        except Exception as e:
            library_logger.info(f"查找微信窗口失败: {e}")
            return False
    def open_video_channel(self):
        """点击打开视频号"""
        library_logger.info("点击打开视频号窗口")
        try:
            controls_info = self.AutomatorUtils.explore_controls(self.WECHAT_WINDOW, max_depth=20)
            #weixin_controls_bounds = self.AutomatorUtils.log_control_tree(controls_info)
            #library_logger.info()(f"微信客户端坐标", weixin_controls_bounds)
            library_logger.info(f"对微信客户端区域实行图像识别")
            with importlib.resources.path('bruce_li_tc.wechatauto.wechat_video_automator.bruce_uiauto','video_channel_icon.png') as template_path:
            # 调用图像识别函数进行点击
                wechat_region = ()
                success = self.AutomatorUtils.find_and_click_template(str(template_path), region=wechat_region, confidence=0.8)
            if success:
                library_logger.info("成功点击视频号频道")
                time.sleep(2)  # 等待页面加载
                return True
            else:
                library_logger.warning("无法找到视频号图标")
                return False
        except Exception as e:
            library_logger.info(f"点击打开视频号窗口失败: {e}")
            return False
    def find_video_channel(self):
        """
        查找视频号窗口
        注:要在微信窗格下查找比较安全一点，如果查不到再换全局查找
        is_global_search=False #不在全局查找
        is_global_search=True #在全局查找
        :return:
        """
        try:
            library_logger.info("开始查找视频号窗口......")
            self.WECHAT_PANE = auto.PaneControl(ClassName='Chrome_WidgetWin_0', Name='微信')
            if self.WECHAT_PANE.Exists(maxSearchSeconds=3):
                library_logger.info("成功找到微信主窗格")
                # 2. 在找到的微信窗格内，查找名为"动态"的文本控件
                # 使用searchFromControl参数将搜索范围限制在这个窗格内
            else:
                library_logger.info("未找到微信主窗格")
            if self.IS_GLOBAL_SEARCH:
                viedo_account_window = auto.DocumentControl(Name="视频号",ClassName="Chrome_RenderWidgetHostHWND")  # 来自Inspect信息
            else:
                viedo_account_window = auto.DocumentControl(searchFromControl=self.WECHAT_PANE ,Name="视频号",ClassName="Chrome_RenderWidgetHostHWND")  # 来自Inspect信息
            if not viedo_account_window.Exists(maxSearchSeconds=60):
                library_logger.info("未找到视频号窗口")
                return False
            else:
                library_logger.info("已找到视频号窗口")
                return True
        except Exception as e:
            library_logger.info("找视频号窗口失败",e)
            return False
    def input_keyword_search(self,search_keyword:str):
        """
        视频号-输入关键字并搜索
        :param search_keyword:
        :return:
        """
        try:
            # 这里需要优化在指定区域对比搜索框
            # template_path = r"./search_input.png"
            # wechat_region = () #默认是全屏，可以指定范围进行查找
            # success = self.AutomatorUtils.find_and_click_template(template_path, region=wechat_region, confidence=0.8)
            with importlib.resources.path('bruce_li_tc.wechatauto.wechat_video_automator.bruce_uiauto','search_input.png') as template_path:
                wechat_region = ()  # 默认是全屏，可以指定范围进行查找
                success = self.AutomatorUtils.find_and_click_template(str(template_path), region=wechat_region,confidence=0.8)
            if success:
                library_logger.info("成功点击视频号搜索框")
                time.sleep(2)  # 等待页面加载
            else:
                library_logger.warning("无法点击视频号搜索框")
            try:
                library_logger.info("开始输入关键字并回车......")
                #search_keyword = "阅兵"
                # 直接向当前激活的控件发送按键消息
                self.SEARCH_KEYWORD=search_keyword
                auto.SendKeys(search_keyword + "{Enter}")  # 使用 {Enter} 模拟回车键
                # auto.SendKeys(search_keyword)  # 如果不想立即回车，只输入关键字
                library_logger.info(f"已输入关键字: {search_keyword}")
            except Exception as e:
                library_logger.warning(f"点击视频号搜索框,输入关键字并回车时发生错误: {e}")
            return True
        except Exception as e:
            library_logger.info(f"点击视频号里面的搜索控件时发生错误: {e}")
            return False
    def video_channel_lodding(self):
        """
        视频号-搜索关键字-判断加载是否完成，，如果出现动态两个字就是加载完成了，但是也不能一直等
        #  --情况1:判断当前窗体内是否有动态,有就是加载完成了
        #  --情况2:暂无搜索结果,那就关闭这个标签页重新搜(先不考虑)
        :return:
        """
        try:
            while True:
                self.TEXT_CONTROL = auto.TextControl(searchFromControl=self.WECHAT_PANE, Name="动态")
                if self.TEXT_CONTROL.Exists(maxSearchSeconds=3):
                    library_logger.info("成功在微信窗格内找到'动态'文本控件")
                    self.TEXT_CONTROL.Click()  # 如果支持点击操作
                    return True
                    # rect = text_control.BoundingRectangle
                    # # 打印坐标信息
                    # library_logger.info()(f"控件坐标: left={rect.left}, top={rect.top}, right={rect.right}, bottom={rect.bottom}")
                    # # 计算中心点坐标（如果需要点击等操作）
                    # center_x = (rect.left + rect.right) // 2
                    # center_y = (rect.top + rect.bottom) // 2
                    # library_logger.info()(f"中心点坐标: ({center_x}, {center_y})")
                else:
                    library_logger.warning("在微信窗格内未找到'动态'文本控件")
                time.sleep(1)
        except Exception as e:
            library_logger.warning(f"判断视频号加载完成时发生错误: {e}")
            return False
    def video_list_data(self,
                        skip_comment,
                        comment_key,
                        comment_list,
                        comment_day,
                        comment_datetime,
                        Interval_count,
                        Interval_seconds)->list:
        """
        视频号-搜索关键字-判断加载是否完成-找到视频列表
        skip_comment是否跳过不获取评论数据，默认不获取评论数据，只获取视频标题的数据
        :return:
        """

        try:
            #初始化随机函数
            self.COMMENT_LIST=comment_list
            self.COMMENT_KEY=comment_key
            self.FairSelector_class=FairSelector(items=comment_list)
            self.video_list_data_config(
                skip_comment,
                comment_key,
                comment_list,
                comment_day,
                comment_datetime,
                Interval_count,
                Interval_seconds)

            parent_group = self.TEXT_CONTROL.GetParentControl()
            # # 2. 获取该父控件的下一个兄弟节点（我们推测它就是视频容器）
            target_video_group = parent_group.GetNextSiblingControl()
            if target_video_group.Exists(maxSearchSeconds=3):
                library_logger.info("成功找到视频容器组")
                data=self.video_item_scroll_click(target_video_group,skip_comment,comment_list)
                return data
            else:
                library_logger.warning("未找到视频容器组")
        except Exception as e:
            library_logger.warning(f"判断视频号加载完成-找到视频列表时发生错误: {e}")
            return  []
    def video_item_scroll_click(self,target_video_group,skip_comment,comment_list,max_attempts=10):
        """
        视频号-搜索关键字-判断加载是否完成-找到视频列表-滚动-自动点击
         max_attempts = 10  # 最大尝试滚动次数
        :return:
        """
        max_sib = 0
        # 我们将从第一个视频容器开始处理，temp初始化为target_video_group
        temp = target_video_group
        video_data=[]
        while True:
            try:

                # 对于第一个视频容器(max_sib == 0)，我们不需要获取下一个兄弟控件，因为temp已经是它了
                # 对于后续的(max_sib >= 1)，我们需要获取下一个兄弟控件
                attempt_count = 0  # 第几次滚动
                clicked = False  # 是否可点击
                if max_sib >= 1:
                    temp = temp.GetNextSiblingControl()
                    if temp.Name == "没有更多了":
                        library_logger.info(f"没有更多了,结束点击,总共有{max_sib}个视频容器,循环结束")
                        break
                    if not temp.Exists(maxSearchSeconds=1):  # 检查控件是否存在，等待最多1秒
                        library_logger.info(f"总共有{max_sib + 1} 个视频容器，已经没有找到更多的兄弟标签页，循环终止")
                        break
                while attempt_count < max_attempts and not clicked:
                    temp_click_status = self.WeChat_Auto_utils.is_control_clickable(temp)
                    library_logger.info(f"第 {max_sib + 1} 个视频容器点击状态: {temp_click_status}")
                    if temp_click_status:
                        try:
                            if self.back_click_model:
                                self.WeChat_Auto_utils.backstage_click(temp)
                            else:
                                temp.Click(ratioX=0.001, ratioY=0.001)
                            library_logger.info(f"成功点击第 {max_sib + 1} 个视频容器")
                            clicked = True
                            time.sleep(1)  # 等待UI响应
                            item_video_data=self.comment_func(self.WECHAT_PANE)  # 假设comment_func返回True表示完成，False表示未完成/失败
                            video_data.append(item_video_data)
                            # 如果不跳过评论且设置了回调函数，则获取评论数据
                            if skip_comment and self.comment_callback:
                                try:
                                    # self.video_item_comment(next_sibling)
                                    previous_sibling, next_sibling = self.WeChat_Auto_utils.find_sibling_tabs(self.SEARCH_KEYWORD + "_搜索")
                                    # 传递视频数据给评论处理函数，以便回调时能关联评论和视频
                                    self.video_item_comment(next_sibling, item_video_data,comment_list,self.COMMENT_KEY)
                                except Exception as e:
                                    print(f"第 {max_sib + 1} 个视频容器 获取评论失败: {str(e)}")


                        except Exception as click_error:
                            library_logger.info(f"第 {max_sib + 1} 个视频容器 点击操作失败: {str(click_error)}")
                            # 即使控件可点击，实际点击可能仍会失败，考虑滚动后重试
                            attempt_count += 1
                    else:
                        library_logger.info(f"第 {max_sib + 1} 个视频容器不可点击，尝试滚动 (尝试 {attempt_count + 1}/{max_attempts})")
                        # 执行滚动操作 - 这里需要你实现具体的滚动逻辑
                        self.scroll_video_container(self.SEARCH_KEYWORD)  # 假设你有一个滚动函数
                        attempt_count += 1
                        time.sleep(1.5)  # 等待滚动后内容加载
                # 如果最大尝试次数后仍未点击成功，跳出循环
                if not clicked:
                    library_logger.info(
                        f"第 {max_sib + 1} 个视频容器，经过 {max_attempts} 次尝试仍无法点击第 {max_sib + 1} 个视频，终止处理")
                    max_sib += 1
                    continue

                # 点击成功后的处理（关闭标签页等）
                try:
                    previous_sibling, next_sibling = self.WeChat_Auto_utils.find_sibling_tabs(self.SEARCH_KEYWORD + "_搜索")
                    self.WeChat_Auto_utils.find_and_filter_children(next_sibling,target_name="关闭",is_click_back=self.back_click_model)
                    library_logger.info(f"第 {max_sib + 1} 个视频容器已关闭标签页")
                except Exception as close_error:
                    library_logger.warning(f"第 {max_sib + 1} 个视频容器 关闭操作失败: {str(close_error)}")
                max_sib += 1
            except Exception as e:
                library_logger.warning(f"在处理第 {max_sib + 1} 个操作时发生错误: {str(e)}")
                time.sleep(1)
                max_sib += 1
                continue
            finally:
                if max_sib > 666:
                    break
        return video_data
    def scroll_video_top(self):
        """
        搜索关键字页-快速滚动到最顶部
        :return:
        """
        try:
            parent_group = self.TEXT_CONTROL.GetParentControl()
            # # 2. 获取该父控件的下一个兄弟节点（我们推测它就是视频容器）
            target_video_group = parent_group.GetNextSiblingControl()
            if target_video_group.Exists(maxSearchSeconds=3):
                library_logger.info("成功找到视频容器组")
            else:
                library_logger.warning("未找到视频容器组")
            # 我们将从第一个视频容器开始处理，temp初始化为target_video_group
            temp = target_video_group
            temp_parent = temp.GetParentControl()

            while True:
                all_child_controls = temp_parent.GetChildren()
                account_text=all_child_controls[0].GetChildren()[0]
                if account_text.Name == "账号" and (not account_text.IsOffscreen):
                    library_logger.info(f"没有更多了,循环结束")
                    break
                self.scroll_video_container(self.SEARCH_KEYWORD,model="up")
                time.sleep(0.1)
        except Exception as e:
            library_logger.warning(f"滚动操作失败: {str(e)}")
    def scroll_video_bottom(self):
        """
        搜索关键字页-滚动到最底部
        :return:
        """
        try:
            parent_group = self.TEXT_CONTROL.GetParentControl()
            # # 2. 获取该父控件的下一个兄弟节点（我们推测它就是视频容器）
            target_video_group = parent_group.GetNextSiblingControl()
            if target_video_group.Exists(maxSearchSeconds=3):
                library_logger.info("成功找到视频容器组")
            else:
                library_logger.warning("未找到视频容器组")
            # 我们将从第一个视频容器开始处理，temp初始化为target_video_group
            temp = target_video_group
            temp_parent=temp.GetParentControl()

            while True:
                all_child_controls = temp_parent.GetChildren()
                if all_child_controls[-1].Name=="没有更多了" and (not all_child_controls[-1].IsOffscreen):
                    library_logger.info(f"没有更多了,循环结束")
                    break
                self.scroll_video_container(self.SEARCH_KEYWORD)
                time.sleep(0.1)
        except Exception as e:
            library_logger.warning(f"滚动操作失败: {str(e)}")
    def scroll_video_container(self,search_keyword: str,model: str = "down"):
        """
        尝试滚动视频容器
        返回布尔值表示是否滚动成功
        """
        try:
            scroll_container = auto.DocumentControl(searchDepth=8, Name=search_keyword + '_搜索')  # 根据你的查找条件调整
            if scroll_container.Exists():
                rect = scroll_container.BoundingRectangle
                if rect.width() > 0 and rect.height() > 0:
                    # 计算文档控件的中心坐标
                    center_x = (rect.left + rect.right) // 2
                    center_y = (rect.top + rect.bottom) // 2

                    # 将鼠标移动到该中心点（确保操作焦点在目标区域）
                    auto.MoveTo(center_x, center_y)
                    time.sleep(0.2)  # 稍作停顿
                    if model=="down":
                        # 模拟鼠标滚轮向下滚动
                        auto.WheelDown(waitTime=0.1)  # waitTime控制滚动间隔[1](@ref)
                    elif model=="up":
                        # 模拟鼠标滚轮向上滚动
                        auto.WheelUp(waitTime=0.1)
                    library_logger.info("模拟鼠标滚轮向下滚动成功")
                else:
                    library_logger.info("文档控件边界矩形无效")
            else:
                library_logger.info("未找到指定的文档控件")
            library_logger.info("未找到可滚动容器")
            return True
        except Exception as e:
            library_logger.warning(f"滚动操作失败: {e}")
            return False
    def comment_func(self,wechat_pane)->dict:
        """
        获取单个视频详情的数据
        :return:
        """
        library_logger.info("开始获取单个视频的标题名，作者名，发布时间，分享数，转发数，喜欢数，评论数。。。。")

        # 定义需要获取的数据字段
        required_data = {
            "author_name": None,  # 作者名称
            "video_title": None,  # 视频标题
            "create_time":None, #发布时间
            "like_count": None,  # 喜欢数
            "share_count": None,  # 分享数
            "favorite_count": None,  # 点赞数
            "comment_count": None  # 评论数
        }
        # 设置超时时间（根据评论数动态调整，初始设为5分钟）

        close_zhu_button_control = auto.ButtonControl(searchFromControl=wechat_pane, Name="+关注")
        author_name_control=None
        if close_zhu_button_control.Exists():
            library_logger.info("找到了+关注按钮")
            like_control = auto.ButtonControl(searchFromControl=wechat_pane, SubName='喜欢')
            if like_control.Exists():
                library_logger.info(f"在已关注的节点中找到了包含“喜欢”的按钮: {like_control.Name}")
                required_data["like_count"] = self.like_count_func(like_control)
                required_data["share_count"] = self.share_count_func(like_control)
                required_data["favorite_count"] = self.favorite_count_func(like_control)
                required_data["comment_count"] = self.comment_count_func(like_control)
                required_data["author_name"], author_name_control = self.author_name_func(close_zhu_button_control)
        else:
            library_logger.info("未找到+关注按钮")
            like_control=auto.ButtonControl(searchFromControl=wechat_pane, SubName='喜欢')
            if like_control.Exists():
                library_logger.info(f"在未关注的节点中找到了包含“喜欢”的按钮: {like_control.Name}")
                guanzhu_control=self.yes_guanzhu_control(like_control)
                required_data["like_count"] = self.like_count_func(like_control)
                required_data["share_count"]=self.share_count_func(like_control)
                required_data["favorite_count"]=self.favorite_count_func(like_control)
                required_data["comment_count"] = self.comment_count_func(like_control)
                required_data["author_name"],author_name_control=self.author_name_func(guanzhu_control)

        video_item_title_temp=self.video_item_title_time(author_name_control)
        required_data["video_title"]=video_item_title_temp["video_title"]
        create_time = self.WeChat_VideoData_utils.format_time(video_item_title_temp["create_time"])
        required_data["create_time"]=create_time
        library_logger.info(f"结束获取单个视频的标题名，作者名，发布时间，分享数，转发数，喜欢数，评论数。。。。required_data：{required_data}")
       # time.sleep(10)
        return required_data
    def yes_guanzhu_control(self,like_control):
        """
        已关注的控件位置
        :param like_control:
        :return:
        """
        temp = like_control
        guanzhu_control=None
        found = False
        for i in range(1, 10):
            if found:
                break
            temp = temp.GetPreviousSiblingControl()
            if temp.Exists():
                #library_logger.info(f"已检查 {i} 个兄弟节点，已找到已关注的节点: {temp.Name}")
                for j in temp.GetChildren():
                    """
                    Name:	"已关注"
                    ControlType:	UIA_TextControlTypeId (0xC364)
                    LocalizedControlType:	"文本"
                    """
                    if j.Name == "已关注" and j.ControlTypeName == "TextControl":
                        library_logger.info(f"已找到已关注的节点: {j.Name}")
                        found = True
                        guanzhu_control=temp
                        break
            else:
                continue
        return guanzhu_control
    def like_count_func(self,like_control):
        """
        喜欢的数量
        :param like_control:
        :return:
        """
        favorite_count = ""
        favorite_button_sibling = like_control
        if favorite_button_sibling.Exists():
            if "喜欢" in favorite_button_sibling.Name:
                favorite_count = self.WeChat_VideoData_utils.extract_number_from_string(favorite_button_sibling.Name)
        return favorite_count
    def author_name_func(self,close_zhu_button_control):
        """
        作者名称
        :return:
        """
        temp_author_name=""
        author_name_control=None
        max_siblings_to_check = 10
        current_sibling_prev = close_zhu_button_control
        # 从“+关注”按钮或者"已关注"按钮开始，连续查找最多10个前续兄弟节点
        current_sibling_prev_status = False
        for i in range(max_siblings_to_check):
            if current_sibling_prev_status:
                library_logger.info(f"已经找到了，不需要再继续往前找前续节点了")
                break
            current_sibling_prev = current_sibling_prev.GetPreviousSiblingControl()
            if not current_sibling_prev.Exists():
                library_logger.info(f"已检查 {i + 1} 个兄弟节点，前续无更多兄弟节点")
                break
           # library_logger.info(f"正在检查第 {i + 1} 个兄弟节点: {current_sibling_prev.Name} (ControlType: {current_sibling_prev.ControlTypeName})")
            """
            作者
            1.从+关注这里往上找兄弟节点,
            -如果上个兄弟节点的孩子里面有图像UIA_ImageControlTypeId (0xC356)，则跳过这个兄弟节点，说明这是带v的官方账号,
            然后从+关注这里找上上个兄弟节点，如果上上个兄弟节点的孩子里面有UIA_TextControlTypeId (0xC364)，则就是这个兄弟节点的孩子节点的名称Name
            -如果上个兄弟节点的孩子里面有UIA_TextControlTypeId (0xC364)，则就是这个兄弟节点的孩子节点的名称Name,说明这个是普通账号
            """
            all_children = current_sibling_prev.GetChildren()
            for child_control in all_children:
                if child_control.ControlTypeName == "TextControl":  # 或者使用 child_control.ControlType == auto.ControlType.Text
                    author_name = child_control.Name
                    author_name_control = child_control
                    temp_author_name= author_name
                    #library_logger.info()(f"找到普通账号文本控件作者名称: {author_name}")
                    current_sibling_prev_status = True
                    break
                elif child_control.ControlTypeName == "ImageControl":  # 或者使用 child_control.ControlType == auto.ControlType.Image
                    library_logger.info("检测到官方账号的图像标识，继续查找...")
                    #library_logger.info()("检测到官方账号的图像标识，继续查找...")

        return temp_author_name,author_name_control
    def share_count_func(self,like_control):
        """
        分享数量
        :return:
        """
        share_count=""
        share_button_sibling = like_control.GetNextSiblingControl()
        if share_button_sibling.Exists():
            # 2. 在该兄弟节点内部查找“分享”按钮 (使用模糊匹配)
            share_button = auto.ButtonControl(searchFromControl=share_button_sibling, SubName='分享')
            if share_button.Exists(maxSearchSeconds=1):
                # 获取分享按钮的所有子控件
                all_children = share_button.GetChildren()
                # 遍历子控件，统计类型为TextControl的控件
                found_text_control = False  # 初始化一个标志变量，表示是否找到文本控件
                for child_control in all_children:
                    if child_control.ControlTypeName == "TextControl":  # 或者使用 child_control.ControlType == auto.ControlType.Text
                        library_logger.info(f"分享按钮内找到文本控件: {child_control.Name}")
                        """
                        分享
                        """
                        share_count = self.WeChat_VideoData_utils.extract_number_from_string(child_control.Name)
                        found_text_control = True
                        break
                # 如果遍历完所有子控件后仍未找到文本控件，则设置为0
                if not found_text_control:
                    library_logger.info("[DEBUG] 在分享按钮内没找到文本控件: share_count设置为0")
                    share_count= "0"
        return share_count
    def favorite_count_func(self,like_control):
        """
        点赞数量
        :return:
        """
        favorite_count=""
        favorite_button_sibling=like_control.GetNextSiblingControl().GetNextSiblingControl()
        if favorite_button_sibling.Exists():
            if "点赞" in favorite_button_sibling.Name:
                favorite_count=self.WeChat_VideoData_utils.extract_number_from_string(favorite_button_sibling.Name)
        return favorite_count
    def comment_count_func(self,like_control):
        """
        评论数量
        :return:
        """
        comment_count=""
        comment_button_sibling=like_control.GetNextSiblingControl().GetNextSiblingControl().GetNextSiblingControl()
        if comment_button_sibling.Exists():
            if "评论" in comment_button_sibling.Name:
                comment_count = self.WeChat_VideoData_utils.extract_number_from_string(comment_button_sibling.Name)
        return comment_count
    def video_item_title_time(self,author_name_control):
        """
        单个视频标题
        :return:
        """
        data={
            "video_title":"",
            "create_time":""
        }
        library_logger.info(f"开始获取视频标题和时间")
        try:
            prev_control=author_name_control.GetParentControl().GetPreviousSiblingControl().GetPreviousSiblingControl()
            #library_logger.info(f"正在检查前一个兄弟节点: {prev_control.Name} (ControlType: {prev_control.ControlTypeName})")
            if prev_control.Exists():
                all_children = prev_control.GetChildren()
                if all_children:
                    # 获取第一个子节点,通常是视频标题
                    first_child = all_children[0]
                   # library_logger.info(f"第一个子节点的名称: {first_child}")
                    first_child_children=first_child.GetChildren()
                   # library_logger.info(f"第一个子节点的子节点名称: {first_child_children}")
                    #
                    video_title=""
                    for child in first_child_children:
                        video_title+=child.Name
                    data["video_title"]=video_title
                    #情况1:里面有\n的看要不要去除，
                    #############################################################
                    second_child = all_children[-1]
                    first_child_children=second_child.GetChildren()
                    for child in first_child_children:
                        if child.ControlTypeName=="TextControl":
                            library_logger.info("视频发布时间",child.Name)
                            data["create_time"] = child.Name
        except Exception as e:
            library_logger.warning("单个视频标题报错",e)
        library_logger.info(f"结束获取视频标题和时间data:{data}")
        return data
    """
    单个视频评论
    """

    def is_reply_count_text_control(self,control):
        """
        判断给定的控件是否是显示'X条回复'的文本控件。
        根据你的实际观察，可能还需要检查其他属性，如ClassName或AutomationId，以提高准确性。
        """
        if control.ControlTypeName == "TextControl":  # 确保是文本控件
            if control.Name:  # 确保Name属性不为空
                # 使用正则表达式匹配数字+“条回复”的模式
                match = re.search(r'(\d+)\s*条回复', control.Name)
                if match:
                    library_logger.info(f"找到回复数量控件: {control.Name}, 共有 {match.group(1)} 条回复")
                    return True
        return False

    def unfold_comments(self, control):
        """展开折叠评论"""
        pass

    def _has_folded_comment(self, control):
        """检查是否有折叠评论"""
        # 实现你的折叠评论检测逻辑
        # 返回True如果发现折叠评论，否则返回False
        pass

    def _need_scroll(self, control):
        """检查是否需要滚动"""
        # 实现你的滚动检测逻辑
        # 返回True如果需要滚动，否则返回False
        pass

    def _scroll_comments(self):
        """执行滚动操作"""
        # 实现你的滚动逻辑
        pass

    def compare_control_tree(self,before, after):
        """
        比较操作前后的控件树信息
        返回一个布尔值表示是否发生变化，以及变化的描述（可选）
        """
        if len(before) != len(after):
            return True, f"子控件数量变化: 操作前 {len(before)}个, 操作后 {len(after)}个"

        for i, (before_item, after_item) in enumerate(zip(before, after)):
            if before_item != after_item:
                return True, f"第{i}个子控件属性发生变化: {before_item} -> {after_item}"

        return False, "控件树未检测到变化"
    def get_children_info(self,control,current_depth=0, max_depth=10):
        """
        递归获取一个控件的所有层级子控件关键信息，以嵌套JSON格式返回
        :param control: 要检查的父控件
        :param current_depth: 当前递归深度（内部使用）
        :param max_depth: 最大搜索深度，防止无限递归
        :return: 嵌套的控件信息字典
        """
        # 深度控制，防止无限递归
        if current_depth >= max_depth:
            return None

        try:
            children = control.GetChildren()
        except Exception as e:
            library_logger.error(f"获取子控件时发生错误: {e}")
            return None

        # 获取当前控件的基本信息
        control_info = {
            'ControlType': control.ControlTypeName if hasattr(control, 'ControlTypeName') else 'Unknown',
            'Name': control.Name if hasattr(control, 'Name') else '',
            'AutomationId': control.AutomationId if hasattr(control, 'AutomationId') else '',
            'ClassName': control.ClassName if hasattr(control, 'ClassName') else '',
            'Depth': current_depth,
            'Children': []  # 用于存储子控件信息
        }

        # 递归获取子控件的子控件
        for child in children:
            child_info = self.get_children_info(child, current_depth + 1, max_depth)
            if child_info:
                control_info['Children'].append(child_info)

        return control_info

    def print_control_tree(self, control_info, indent=0):
        """
        以树形结构打印控件信息
        :param control_info: 控件信息字典
        :param indent: 缩进级别（内部使用）
        """
        if not control_info:
            return

        # 打印当前控件信息
        indent_str = "  " * indent

        # 递归打印子控件
        for child in control_info['Children']:
            self.print_control_tree(child, indent + 1)

    def is_control_visible(self, temp_control):
        """
        检查控件是否在屏幕可见区域内
        :param temp_control: 要检查的控件
        :return: 是否可见
        """
        try:
            temp_control_rect = temp_control.BoundingRectangle
            if (temp_control_rect.left == 0 and temp_control_rect.top == 0 and temp_control_rect.right == 0 and temp_control_rect.bottom == 0) or temp_control.IsOffscreen:
                return False
            else:
                return True
        except:
            return False
    def comment_content_key(self,data)->bool:
        """
        判断评论内容是否有相关的
        True就是有
        False就是没有
        :return:
        """
        try:
            keyword_list=self.COMMENT_KEY

            # 2. 构建正则表达式模式（自动转义特殊字符）
            pattern = '|'.join(map(re.escape, keyword_list))

            # 3. 检查评论内容是否匹配任何关键词
            comment_content = data["comment_content"]
            if not re.search(pattern, comment_content):
                return False
            return True
        except Exception as e:
            return False

    def check_and_wait(self, reply_counter:int)->None:
        """
        检查回复数量，如果达到新的阈值倍数则等待指定时间
        :param reply_counter: 当前回复数量
        """
        try:
            threshold = self.VIDEO_LIST_DATA_CONFIG["Interval_count"]
            wait_time = self.VIDEO_LIST_DATA_CONFIG["Interval_seconds"]

            # 添加一个实例变量来记录上次等待时的倍数
            if not hasattr(self, 'LAST_WAITED_MULTIPLE'):
                self.LAST_WAITED_MULTIPLE = -1  # 初始化为-1，确保第一次能触发

            # 计算当前倍数
            current_multiple = reply_counter // threshold

            # 只有当达到新的倍数时才等待
            if reply_counter % threshold == 0 and reply_counter != 0 and current_multiple > self.LAST_WAITED_MULTIPLE:
                library_logger.success(f"开始等待，当前回复数量为: {reply_counter}")
                time.sleep(wait_time * 60)
                # 更新上次等待的倍数
                self.LAST_WAITED_MULTIPLE = current_multiple
            else:
                library_logger.debug(f"当前回复数量为: {reply_counter},无需等待")
        except Exception as e:
            library_logger.warning(f"等待时间发生错误: {e}")

    def filter_required_comment_data(self,required_comment_data)->bool:
        """
        过滤7天内的数据，31天内的数据
        :param required_comment_data:当前数据
        :return:True就是可以，False就是不可以
        """

        # 检查评论创建时间是否存在
        comment_create_time = required_comment_data.get("comment_create_time")
        if comment_create_time is None:
            return False
        try:
            # 处理时间格式：如果comment_create_time是字符串，转换为datetime对象
            if isinstance(comment_create_time, str):
                # 常见的时间字符串格式，可根据实际情况调整格式字符串
                comment_create_time = datetime.strptime(
                    comment_create_time,
                    '%Y-%m-%d %H:%M:%S'  # 例如 "2023-09-25 14:30:00"
                )

            # 确保comment_create_time是datetime对象
            if not isinstance(comment_create_time, datetime):
                return False
            #self.VIDEO_LIST_DATA_CONFIG["comment_datetime"] = datetime.now()
            # 如果要用固定时间，应该这样写：

            # 获取参考时间（当前时间）和时间间隔
            now_date_time = datetime.strptime(self.VIDEO_LIST_DATA_CONFIG["comment_datetime"], "%Y-%m-%d %H:%M:%S")
            time_space = int(self.VIDEO_LIST_DATA_CONFIG["comment_day"])  # 将字符串间隔转换为整数

            # 计算时间边界：参考时间减去时间间隔（天数）
            time_boundary = now_date_time - timedelta(days=time_space)

            # 核心判断：评论时间是否在边界时间之后（即 within the last `time_space` days）
            # 直接返回布尔表达式，避免冗余的if-else结构[1,3](@ref)
            return comment_create_time >= time_boundary
        except Exception as e:
            # 时间格式解析错误或类型错误
            print(f"时间解析错误: {e}")
            return False

    def continue_srcoll_contorl(self):
        """
        跳过滚动的控件
        :return:
        """
        try:
            if not self.CONTINUE_SRCOLL_CONTORL:
                return True
            else:
                return False
        except Exception as e:
            library_logger.warning(f"跳过滚动控件发生错误: {e}")

    def cat_author_name(self,control):
        """
        查看评论作者的名字
        :param control:
        :return:
        """
        try:
            now_control_name=""
            now_comment_author_name = control.GetPreviousSiblingControl().GetChildren()
            for child in now_comment_author_name:
                if child.ControlTypeName == "TextControl":
                    now_control_name += child.Name
            return now_control_name
        except Exception as e:
            library_logger.warning(f"获取作者名字发生错误: {e}")

    def control_srcoll(self,temp_control,temp_next_control,temp_next_next_control,sum_comment_count):
        """
        控制滚动
        :return:
        """
        # 检查控件是否在屏幕内
        if (not self.is_control_visible(temp_control)) and self.continue_srcoll_contorl():
            library_logger.debug(f"第{sum_comment_count + 1}条评论，控件是否在屏幕内{self.is_control_visible(temp_control)}',temp_control:'{temp_control}")
            try:
                temp_count=0
                while True:
                    if temp_count>15:
                        break
                    if self.is_control_visible(temp_control):
                        break
                    else:
                        self.scroll_video_comment(self.NEXT_SIBLING)
                    temp_count+=1
                    time.sleep(0.1)
            except Exception as e:
                library_logger.warning(f"滚动发生错误: {e}")
            library_logger.success(f"第{sum_comment_count + 1}条评论，控件是否在屏幕内{self.is_control_visible(temp_control)}',temp_control:'{temp_control}")
        elif not self.continue_srcoll_contorl():
            library_logger.debug(f"当前编辑过，等会轮到这个元素出来，再滚动temp_control{temp_control}")
            library_logger.debug(f"self.CONTINUE_SRCOLL_CONTORL['name']:{self.CONTINUE_SRCOLL_CONTORL['name']}")
            library_logger.debug(f"self.CONTINUE_SRCOLL_CONTORL['from']:{self.CONTINUE_SRCOLL_CONTORL['from']}")
            library_logger.debug(f"self.CONTINUE_SRCOLL_CONTORL['date']:{self.CONTINUE_SRCOLL_CONTORL['date']}")

            if self.CONTINUE_SRCOLL_CONTORL["mode"] == "1" and temp_control.Name == "作者":
                library_logger.debug(f"处理作者评论,滚动的问题开始")
                now_control_name = self.cat_author_name(temp_control)
                now_control_from = temp_next_control.Name
                now_control_date = temp_next_next_control.Name
                continue_control_name = self.CONTINUE_SRCOLL_CONTORL["name"]
                continue_control_from = self.CONTINUE_SRCOLL_CONTORL["from"]
                continue_control_date = self.CONTINUE_SRCOLL_CONTORL["date"]
                if now_control_from == continue_control_from and \
                        now_control_date == continue_control_date and \
                        now_control_name == continue_control_name:
                    self.CONTINUE_SRCOLL_CONTORL = {}
                    library_logger.debug(f"处理作者评论,滚动的问题,{self.CONTINUE_SRCOLL_CONTORL}")
            elif self.CONTINUE_SRCOLL_CONTORL["mode"] == "2" and temp_next_control.Name != "":
                library_logger.debug(f"处理其他用户评论,滚动的问题开始")
                now_control_name = self.cat_author_name(temp_control)
                now_control_from = temp_next_control.Name
                now_control_date = temp_next_next_control.Name
                continue_control_name = self.CONTINUE_SRCOLL_CONTORL["name"]
                continue_control_from = self.CONTINUE_SRCOLL_CONTORL["from"]
                continue_control_date = self.CONTINUE_SRCOLL_CONTORL["date"]
                if now_control_name == continue_control_name and \
                        now_control_from == continue_control_from and \
                        now_control_date == continue_control_date:
                    self.CONTINUE_SRCOLL_CONTORL = {}
                    library_logger.debug(f" 处理其他用户评论,滚动的问题,{self.CONTINUE_SRCOLL_CONTORL}")
            elif self.CONTINUE_SRCOLL_CONTORL["mode"] == "3" and temp_next_control.Name == "" and temp_next_next_control.Name == "":
                library_logger.debug(f"处理自己评论,滚动的问题开始")
                now_control_name = self.cat_author_name(temp_control)
                now_control_date = temp_control.Name
                continue_control_name = self.CONTINUE_SRCOLL_CONTORL["name"]
                continue_control_date = self.CONTINUE_SRCOLL_CONTORL["date"]
                if now_control_name == continue_control_name and now_control_date == continue_control_date:
                    self.CONTINUE_SRCOLL_CONTORL = {}
                    library_logger.debug(f"处理自己评论,滚动的问题,{self.CONTINUE_SRCOLL_CONTORL}")
            else:
                pass
                # library_logger.debug(f"其他问题滚动开始")
                # library_logger.debug(f"now_control_name{now_control_name}")
                # library_logger.debug(f"now_control_date{now_control_date}")
                # try:
                #     library_logger.debug(f"continue_control_from{continue_control_from}")
                # except Exception as e:
                #     library_logger.warning(f"continue_control_from:{e}")


    def video_item_comment(self,next_sibling,video_data,comment_list:list=None,comment_key:list=None):
        """
        获取视频评论数据，每获取一条评论就通过回调函数处理
        :param next_sibling:标签页
        :param video_data: 对应的视频数据，用于回调时关联评论和视频
        :return:
        """
        # 滚动视频评论
        self.NEXT_SIBLING=next_sibling


        #comment_data_list=[]
        search_pinglun_text_control = self.search_pinglun_text_control_func()
        temp_control=search_pinglun_text_control
        sum_comment_count=0 #第几条评论
        # 初始化存储姓名的集合
        author_names_set = set()

        current_state = OperationState.IDLE # 使用枚举状态替代多个布尔标志
        contorl_count=0 #第几个控件
        self.CONTINUE_SRCOLL_CONTORL = {}
        while True:
            try:
                self.check_and_wait(self.REPLAY_COUNT)
                """
                流程
                1.我先检查非空控件是否可见
                2.然后不可见就滚动
                3.检查空控件
                """
                if temp_control is None:
                    library_logger.debug(f"没有更多评论了")
                    break  # 没有更多控件，退出循环

                #滚动屏幕

                # 只有在空闲状态时才获取新控件
                # if current_state == OperationState.IDLE:
                #     pass
                #     #library_logger.debug(f"空闲时才滚动屏幕")s
                #
                # # # 非空闲状态，跳过处理继续循环
                # if current_state != OperationState.IDLE:
                #     # 非空闲状态，跳过处理继续循环
                #     library_logger.info(f"当前状态 {current_state.name}，暂停处理新控件")
                #     if temp_control.Name != "" and (not self.is_control_visible(temp_control)):
                #         self.scroll_video_comment(self.NEXT_SIBLING)
                #     continue

                #library_logger.debug(f"第{contorl_count+1}个控件: {temp_control}")
                if temp_control.Name != "":
                    temp_next_control = self.get_next_control_safe(temp_control)
                    temp_next_next_control = self.get_next_control_safe(temp_next_control)
                    self.control_srcoll(temp_control,temp_next_control,temp_next_next_control,sum_comment_count)#控制屏幕滚动的函数

                    if temp_control.Name == "作者" and temp_next_control.Name != "" and temp_next_next_control.Name != "":
                        # 处理作者评论
                        required_comment_data = self.item_comment_func(temp_control)
                        library_logger.debug(f"author_names_set{author_names_set},第{sum_comment_count + 1}条评论，作者评论: {required_comment_data},是否包含关键字{self.COMMENT_KEY},{self.comment_content_key(required_comment_data)}")

                        if (required_comment_data['comment_author_name'] not in author_names_set) and (self.comment_content_key(required_comment_data)) and self.filter_required_comment_data(required_comment_data):
                            library_logger.success(f"第{sum_comment_count + 1}条评论，作者评论: {required_comment_data}可以回复，符合条件{self.filter_required_comment_data(required_comment_data)},当前评论{self.REPLAY_COUNT+1}个")
                            # 标记状态为回复中
                            current_state = OperationState.REPLYING

                            # 回复消息
                            self.replay_comment_func(temp_next_control)

                            # 标记状态为关注中
                            current_state = OperationState.FOLLOWING
                            time.sleep(1)
                            # 关注用户
                            self.guanzhu_func(temp_control)

                            # 添加到已处理集合
                            author_names_set.add(required_comment_data['comment_author_name'])
                            # 恢复空闲状态

                            current_state = OperationState.IDLE
                            # 通过回调函数处理单条评论数据
                            if self.comment_callback:
                                try:
                                    self.comment_callback(required_comment_data, video_data)
                                except Exception as e:
                                    library_logger.warning(f"评论回调函数执行失败: {e}")
                            # 回复数量+1
                            self.REPLAY_COUNT += 1

                        temp_control = self.get_next_control_safe(temp_next_next_control)
                    elif temp_next_control.Name != "":
                        # 处理其他用户评论
                        required_comment_data = self.item_comment_func(temp_control)

                        if not (required_comment_data["comment_from"] == "四川" and any(comment in required_comment_data["comment_content"] for comment in self.COMMENT_LIST)):
                            library_logger.debug(f"author_names_set{author_names_set},第{sum_comment_count + 1}条评论，他人评论: {required_comment_data}:是否包含关键字{self.COMMENT_KEY},{self.comment_content_key(required_comment_data)},是否符合7天内{self.filter_required_comment_data(required_comment_data)}")

                            if (required_comment_data['comment_author_name'] not in author_names_set) and (self.comment_content_key(required_comment_data)) and self.filter_required_comment_data(required_comment_data):
                                library_logger.success(f"第{sum_comment_count + 1}条评论，作者评论: {required_comment_data}可以回复，符合条件{self.filter_required_comment_data(required_comment_data)},当前评论{self.REPLAY_COUNT+1}个")

                                # 标记状态为回复中
                                current_state = OperationState.REPLYING


                                # 回复消息
                                self.replay_comment_func(temp_control)
                                # 标记状态为关注中
                                current_state = OperationState.FOLLOWING
                                # 关注用户
                                self.guanzhu_func(temp_control)

                                # 添加到已处理集合
                                author_names_set.add(required_comment_data['comment_author_name'])
                                # 恢复空闲状态
                                current_state = OperationState.IDLE

                                # 通过回调函数处理单条评论数据
                                if self.comment_callback:
                                    try:
                                        self.comment_callback(required_comment_data, video_data)
                                    except Exception as e:
                                        library_logger.warning(f"评论回调函数执行失败: {e}")
                                # 回复数量+1
                                self.REPLAY_COUNT += 1
                        #temp_control = temp_next_control
                        temp_control=self.get_next_control_safe(temp_next_control)
                    elif temp_next_control.Name == "" and temp_next_next_control.Name == "":
                        # 处理自己评论
                        required_comment_data = self.item_comment_func(temp_control, model="2")
                        library_logger.debug(f"第{sum_comment_count + 1}条评论，自己评论: {required_comment_data}")
                        temp_control = self.get_next_control_safe(temp_control)
                    else:
                        # 未知类型评论，跳过
                        temp_control = self.get_next_control_safe(temp_control)
                        continue
                    # 恢复空闲状态
                    #current_state = OperationState.IDLE
                    sum_comment_count += 1
                else:
                    # 处理空名称控件
                    has_expanded = self.find_and_click_reply_text(temp_control)
                    if has_expanded:
                        # 等待评论加载
                        self.CONTINUE_SRCOLL_CONTORL = {}
                        time.sleep(1)
                    temp_control = self.get_next_control_safe(temp_control)

                contorl_count+=1

            except Exception as e:
                library_logger.warning(f"第{sum_comment_count+1}个视频获取评论内容失败：{e}")
                # 确保在出现异常时重置状态
                current_state = OperationState.IDLE
                # 出错时尝试跳过当前控件
                temp_control = self.get_next_control_safe(temp_control)

            time.sleep(0.5)

    def get_next_control_safe(self,current_control):
        """
        安全地获取下一个兄弟控件，避免在最后一个控件时报错
        """
        try:
           # library_logger.debug(f"当前控件: {current_control}，查看是")
            next_control = current_control.GetNextSiblingControl()
            if next_control and next_control.Exists():
                return next_control
            else:
                if current_control.ControlTypeName == "GroupControl":
                    #说明还没滚动到底
                    library_logger.debug(f"还没滚动到底")
                    temp_count=0
                    while True:
                        if temp_count>15:
                            break
                        self.scroll_video_comment(self.NEXT_SIBLING)
                        next_control = current_control.GetNextSiblingControl()
                        if next_control and next_control.Exists():
                            library_logger.success(f"找到下一个兄弟控件: {next_control}")
                            return next_control
                        temp_count+=1
                        time.sleep(0.1)
                elif current_control.ControlTypeName == "TextControl":
                    #滚动到最底部了
                    library_logger.debug(f"滚动到最底部了")
                library_logger.warning(f"当前控件: {current_control}，没有下一个兄弟控件")
            return None
        except Exception as e:
            library_logger.warning(f"get_next_control_safe获取下一个控件时出错: {e}")
            return None
    def find_and_click_reply_text(self,parent_control, max_depth=10):
        """
        递归地从父控件开始查找所有层级的子控件，寻找并点击'X条回复'文本。
        :param parent_control: 开始查找的父控件（例如一个评论项）。
        :param max_depth: 最大搜索深度，防止无限递归。
        """
        if max_depth <= 0:
            return

        clicked = False
        # 获取当前父控件的所有直接子控件
        children = parent_control.GetChildren()

        for child in children:
            # 检查当前子控件是否是我们要找的“条回复”文本控件
            if self.is_reply_count_text_control(child):
                try:
                    library_logger.info(f"尝试点击回复控件: {child.Name}")
                    # **尝试点击该文本控件本身**
                    if self.back_click_model:
                        self.WeChat_Auto_utils.backstage_click(child)
                    else:
                        child.Click(simulateMove=True)  # simulateMove 模拟鼠标移动更真实
                    time.sleep(1.5)  # **重要：点击后等待回复加载，时间可根据实际情况调整**
                    # 点击后，你可以选择跳出循环（如果确定只有一个这样的控件）
                    # break
                    clicked = True
                    # 点击后跳出循环，只处理一个可折叠评论
                    break
                except Exception as e:
                    library_logger.warning(f"点击回复控件时出错: {e}")
                    # 如果直接点击文本控件无效，可以尝试查找其父控件或兄弟控件中的按钮
                    # 例如，有时“条回复”文本旁边可能有一个实际的按钮用于点击
                    parent_of_text = child.GetParentControl()
                    # 尝试在父控件中查找按钮（ButtonControl）
                    possible_button = parent_of_text.ButtonControl(searchDepth=1)
                    if possible_button.Exists():
                        try:
                            library_logger.info("尝试通过父控件中的按钮点击")
                            possible_button.Click(simulateMove=True)
                            time.sleep(1.5)
                            clicked = True
                            break
                        except Exception as btn_e:
                            library_logger.warning(f"点击按钮时出错: {btn_e}")
            else:
                # 如果当前控件不是，则递归深入其子控件继续查找
                if self.find_and_click_reply_text(child, max_depth - 1):
                    clicked = True
                    break
                # 如果当前控件不是，则递归深入其子控件继续查找
                #self.find_and_click_reply_text(child, max_depth - 1)
        return clicked
    def user_tab_func(self):
        """
        查看个人主页是否打开
        :return:
        """
        try:

            previous_sibling, next_sibling = self.WeChat_Auto_utils.find_sibling_tabs(self.SEARCH_KEYWORD + "_搜索")
            # 获取父节点
            parentControl = next_sibling.GetParentControl().GetChildren()
            #library_logger.debug(f"tabs标签页父节点长度: {len(parentControl)}")
            return parentControl
        except Exception as e:
            library_logger.info(f"查找节点时出错: {e}")
            return None

    def profile_function(self, func, *args, **kwargs):
        """
        使用 cProfile 分析函数性能，并通过 loguru 输出结果
        :param func: 要分析的函数
        :param args: 函数的位置参数
        :param kwargs: 函数的关键字参数
        :return: 函数的返回值
        """
        # 创建 Profile 对象
        profiler = cProfile.Profile()
        profiler.enable()  # 开始性能分析

        try:
            # 运行要分析的函数
            result = func(*args, **kwargs)
        except Exception as e:
            # 如果函数执行出错，记录错误信息
            library_logger.error(f"分析函数执行出错: {e}")
            result = None
        finally:
            profiler.disable()  # 停止性能分析

        # 将分析结果输出到字符串流
        result_stream = StringIO()
        sortby = 'cumulative'  # 按累计时间排序，这能帮你找到最耗时的函数
        stats = pstats.Stats(profiler, stream=result_stream).sort_stats(sortby)
        stats.print_stats()  # 打印统计信息

        # 使用 loguru 输出分析结果
        analysis_result = result_stream.getvalue()
        library_logger.info("cProfile Performance Analysis Result:\n{}", analysis_result)

        return result
    def guanzhu_func(self,temp_control):
        """
        关注功能
        :return:
        """
        #1.关注作者，判断是否已关注
        #2.点击头像进去不了个人主页,可以通过判断标签页是否有增加
        #3.点击头像可以进入主页，判断是否已关注
        #4.关闭标签页

        library_logger.debug(f"开始关注功能{temp_control.Name}")
        #self.profile_function(AvatarClickHandler.handle_avatar_click,avatar_control=temp_control,tab_control_name=self.SEARCH_KEYWORD + "_搜索")# 运行你想要分析的函数
        AvatarClickHandler.handle_avatar_click(avatar_control=temp_control,tab_control_name=self.SEARCH_KEYWORD + "_搜索")
        library_logger.debug(f"结束关注功能{temp_control.Name}")
        time.sleep(1)
    def replay_comment_func(self,temp_control):
        """
        回复功能
        :param temp_control:
        :return:
        """
        library_logger.debug(f"开始回复功能{temp_control}")
        replay_control = temp_control.GetNextSiblingControl().GetNextSiblingControl().GetNextSiblingControl().GetNextSiblingControl()
        for replay_control_item in replay_control.GetChildren():
            if replay_control_item.Name == "回复":
                if self.back_click_model:
                    self.WeChat_Auto_utils.backstage_click(replay_control_item)
                else:
                    self.WeChat_Auto_utils.default_click(replay_control_item)
                break

        replay_random_text = self.random_select()
        auto.SendKeys(replay_random_text)

        library_logger.debug(f"回复话术内容:{replay_random_text}")
        self.replay_click(replay_control)
        time.sleep(2)
        library_logger.debug(f"结束回复功能{temp_control}")



    ##########################################################
    def find_parent_and_siblings(self,control, max_parent_levels=10, max_siblings=6):
        """
        查找控件的父节点及其前后兄弟节点
        :param control: 目标控件
        :param max_parent_levels: 最大向上查找的父节点层数
        :param max_siblings: 前后兄弟节点的最大数量
        :return: 包含父节点和兄弟节点信息的字典
        """
        result = {
            'target_control': control,
            'parent_hierarchy': [],
            'siblings_info': []
        }

        # 向上查找父节点层级
        current_parent = control.GetParentControl()
        level = 1

        while current_parent and level <= max_parent_levels:
            parent_info = {
                'level': level,
                'parent_control': current_parent,
                'parent_name': current_parent.Name if current_parent else 'Unknown',
                'parent_class': current_parent.ClassName if current_parent else 'Unknown',
                'parent_automation_id': current_parent.AutomationId if current_parent else 'Unknown',
                'previous_siblings': [],
                'next_siblings': []
            }

            # 查找前兄弟节点（最多max_siblings个）
            prev_sibling = current_parent.GetPreviousSiblingControl()
            prev_count = 0
            while prev_sibling and prev_count < max_siblings:
                parent_info['previous_siblings'].append({
                    'sibling_control': prev_sibling,
                    'name': prev_sibling.Name if prev_sibling else 'Unknown',
                    'class_name': prev_sibling.ClassName if prev_sibling else 'Unknown',
                    'automation_id': prev_sibling.AutomationId if prev_sibling else 'Unknown'
                })
                prev_sibling = prev_sibling.GetPreviousSiblingControl()
                prev_count += 1

            # 查找后兄弟节点（最多max_siblings个）
            next_sibling = current_parent.GetNextSiblingControl()
            next_count = 0
            while next_sibling and next_count < max_siblings:
                parent_info['next_siblings'].append({
                    'sibling_control': next_sibling,
                    'name': next_sibling.Name if next_sibling else 'Unknown',
                    'class_name': next_sibling.ClassName if next_sibling else 'Unknown',
                    'automation_id': next_sibling.AutomationId if next_sibling else 'Unknown'
                })
                next_sibling = next_sibling.GetNextSiblingControl()
                next_count += 1

            result['parent_hierarchy'].append(parent_info)

            # 继续向上查找父节点
            current_parent = current_parent.GetParentControl()
            level += 1

        return result

    def print_parent_siblings_info(self,control_info):
        """打印父节点和兄弟节点信息"""
        print("=" * 60)
        print("控件父节点及兄弟节点分析结果")
        print("=" * 60)

        target = control_info['target_control']
        print(f"目标控件: {target.Name} (Class: {target.ClassName}, ID: {target.AutomationId})")
        print()

        for parent_info in control_info['parent_hierarchy']:
            print(f"第 {parent_info['level']} 层父节点:")
            print(f"  - 名称: {parent_info['parent_name']}")
            print(f"  - 类名: {parent_info['parent_class']}")
            print(f"  - AutomationId: {parent_info['parent_automation_id']}")

            # 打印前兄弟节点
            if parent_info['previous_siblings']:
                print(f"  - 前 {len(parent_info['previous_siblings'])} 个兄弟节点:")
                for i, sibling in enumerate(parent_info['previous_siblings'], 1):
                    print(
                        f"    {i}. {sibling['name']} (Class: {sibling['class_name']}, ID: {sibling['automation_id']})")
            else:
                print("  - 前兄弟节点: 无")

            # 打印后兄弟节点
            if parent_info['next_siblings']:
                print(f"  - 后 {len(parent_info['next_siblings'])} 个兄弟节点:")
                for i, sibling in enumerate(parent_info['next_siblings'], 1):
                    print(
                        f"    {i}. {sibling['name']} (Class: {sibling['class_name']}, ID: {sibling['automation_id']})")
            else:
                print("  - 后兄弟节点: 无")

            print("-" * 40)

    # 简化版本：只获取特定层级的父节点信息
    def get_specific_parent_level(self,control, target_level=1):
        """
        获取特定层级的父节点信息

        :param control: 目标控件
        :param target_level: 目标层级（1=直接父节点，2=祖父节点，以此类推）
        :return: 指定层级的父节点信息，如果不存在返回None
        """
        current_parent = control
        current_level = 0

        while current_parent and current_level < target_level:
            current_parent = current_parent.GetParentControl()
            current_level += 1

        if current_parent and current_level == target_level:
            return {
                'level': target_level,
                'parent_control': current_parent,
                'name': current_parent.Name,
                'class_name': current_parent.ClassName,
                'automation_id': current_parent.AutomationId
            }

        return None

    # 示例1：获取评论控件的父节点和兄弟节点信息
    def analyze_comment_control(self,edit_control):
        """分析评论控件的层级结构"""
        # 原有的分析
        control_info = self.find_parent_and_siblings(edit_control)
        self.print_parent_siblings_info(control_info)

        # 新增：分析第2层父节点的兄弟节点
        second_level_siblings = self.analyze_second_level_parent_siblings(edit_control)
        self.print_second_level_siblings_info(second_level_siblings)

        # 获取第一个非空前兄弟节点（如果需要）
        first_prev_sibling = self.get_first_non_empty_sibling(edit_control, 'previous', 0)
        first_next_sibling = self.get_first_non_empty_sibling(edit_control, 'next', 0)

        if first_prev_sibling:
            print(f"第一个非空前兄弟节点: {first_prev_sibling.Name}")
        if first_next_sibling:
            print(f"第一个非空后兄弟节点: {first_next_sibling.Name}")

        # 返回合并的结果
        return {
            'full_hierarchy': control_info,
            'second_level_siblings': second_level_siblings,
            'first_previous_sibling': first_prev_sibling,
            'first_next_sibling': first_next_sibling
        }

    def analyze_second_level_parent_siblings(self, control, max_siblings=6):
        """
        分析控件的第2层父节点的前后兄弟节点

        :param control: 目标控件
        :param max_siblings: 前后兄弟节点的最大数量，默认为6
        :return: 包含第2层父节点前后兄弟节点信息的字典
        """
        # 获取第2层父节点
        second_level_parent = self.get_specific_parent_level(control, target_level=2)

        if not second_level_parent:
            print("未找到第2层父节点")
            return {
                'target_control': control,
                'second_level_parent': None,
                'previous_siblings': [],
                'next_siblings': []
            }

        result = {
            'target_control': control,
            'second_level_parent': second_level_parent,
            'previous_siblings': [],
            'next_siblings': []
        }

        parent_control = second_level_parent['parent_control']

        # 查找前兄弟节点（最多max_siblings个非空节点）
        prev_sibling = parent_control.GetPreviousSiblingControl()
        prev_count = 0

        while prev_sibling and prev_count < max_siblings:
            # 检查节点是否非空（根据名称、类名或AutomationId判断）
            if (prev_sibling.Name or prev_sibling.ClassName or prev_sibling.AutomationId):
                sibling_info = {
                    'sibling_control': prev_sibling,
                    'name': prev_sibling.Name if prev_sibling else 'Unknown',
                    'class_name': prev_sibling.ClassName if prev_sibling else 'Unknown',
                    'automation_id': prev_sibling.AutomationId if prev_sibling else 'Unknown'
                }
                result['previous_siblings'].append(sibling_info)
                prev_count += 1

            prev_sibling = prev_sibling.GetPreviousSiblingControl()

        # 查找后兄弟节点（最多max_siblings个非空节点）
        next_sibling = parent_control.GetNextSiblingControl()
        next_count = 0

        while next_sibling and next_count < max_siblings:
            # 检查节点是否非空
            if (next_sibling.Name or next_sibling.ClassName or next_sibling.AutomationId):
                sibling_info = {
                    'sibling_control': next_sibling,
                    'name': next_sibling.Name if next_sibling else 'Unknown',
                    'class_name': next_sibling.ClassName if next_sibling else 'Unknown',
                    'automation_id': next_sibling.AutomationId if next_sibling else 'Unknown'
                }
                result['next_siblings'].append(sibling_info)
                next_count += 1

            next_sibling = next_sibling.GetNextSiblingControl()

        return result

    def get_first_non_empty_sibling(self, control, direction='previous', sibling_index=0):
        """
        获取指定方向的第一个非空兄弟节点

        :param control: 目标控件
        :param direction: 方向，'previous'表示前兄弟节点，'next'表示后兄弟节点
        :param sibling_index: 兄弟节点索引，0表示第一个
        :return: 兄弟节点控件，如果不存在返回None
        """
        siblings_info = self.analyze_second_level_parent_siblings(control)

        if direction == 'previous':
            siblings_list = siblings_info['previous_siblings']
        else:
            siblings_list = siblings_info['next_siblings']

        if sibling_index < len(siblings_list):
            return siblings_list[sibling_index]['sibling_control']

        return None

    def print_second_level_siblings_info(self, siblings_info):
        """打印第2层父节点的兄弟节点信息"""
        print("=" * 60)
        print("第2层父节点兄弟节点分析结果")
        print("=" * 60)

        target = siblings_info['target_control']
        print(f"目标控件: {target.Name} (Class: {target.ClassName}, ID: {target.AutomationId})")
        print()

        second_parent = siblings_info['second_level_parent']
        if second_parent:
            print(f"第2层父节点:")
            print(f"  - 名称: {second_parent['name']}")
            print(f"  - 类名: {second_parent['class_name']}")
            print(f"  - AutomationId: {second_parent['automation_id']}")
            print()

            # 打印前兄弟节点
            if siblings_info['previous_siblings']:
                print(f"前 {len(siblings_info['previous_siblings'])} 个非空兄弟节点:")
                for i, sibling in enumerate(siblings_info['previous_siblings'], 1):
                    print(f"  {i}. {sibling['name']} (Class: {sibling['class_name']}, ID: {sibling['automation_id']})")
            else:
                print("前兄弟节点: 无")

            print()

            # 打印后兄弟节点
            if siblings_info['next_siblings']:
                print(f"后 {len(siblings_info['next_siblings'])} 个非空兄弟节点:")
                for i, sibling in enumerate(siblings_info['next_siblings'], 1):
                    print(f"  {i}. {sibling['name']} (Class: {sibling['class_name']}, ID: {sibling['automation_id']})")
            else:
                print("后兄弟节点: 无")
        else:
            print("未找到第2层父节点")

        print("=" * 60)
    """
    1.查找编辑的兄弟节点的下一个节点，并记录存下来，然后遍历到这个节点的时候，再进行判断是否可见，并进行滚动
    2.判断是否为空，如果为空，
    """
    ##########################################################


    def continue_control_config(self,first_next):
        """
        需要跳过滚动控件配置
        :return:
        """
        self.CONTINUE_SRCOLL_CONTORL.clear()
        continue_control = first_next
        continue_control_next = self.get_next_control_safe(continue_control)
        continue_control_next_next = self.get_next_control_safe(continue_control_next)
        self.CONTINUE_SRCOLL_CONTORL["continue_control"] = continue_control
        self.CONTINUE_SRCOLL_CONTORL["continue_control_next"] = continue_control_next
        self.CONTINUE_SRCOLL_CONTORL["continue_control_next_next"] = continue_control_next_next
        if continue_control.Name == "作者" and continue_control_next.Name != "" and continue_control_next_next.Name == "":
            self.CONTINUE_SRCOLL_CONTORL["name"] = self.cat_author_name(continue_control)
            self.CONTINUE_SRCOLL_CONTORL["from"] = continue_control_next.Name
            self.CONTINUE_SRCOLL_CONTORL["date"] = continue_control_next_next.Name
            self.CONTINUE_SRCOLL_CONTORL["mode"] = "1"
        elif continue_control_next.Name != "":
            self.CONTINUE_SRCOLL_CONTORL["name"] = self.cat_author_name(continue_control)
            self.CONTINUE_SRCOLL_CONTORL["from"] = continue_control.Name
            self.CONTINUE_SRCOLL_CONTORL["date"] = continue_control_next.Name
            self.CONTINUE_SRCOLL_CONTORL["mode"] = "2"
        elif continue_control_next.Name == "" and continue_control_next_next.Name == "":
            self.CONTINUE_SRCOLL_CONTORL["name"] = self.cat_author_name(continue_control)
            self.CONTINUE_SRCOLL_CONTORL["date"] = continue_control.Name
            self.CONTINUE_SRCOLL_CONTORL["from"] = ""
            self.CONTINUE_SRCOLL_CONTORL["mode"] = "3"


    def replay_click(self,control):
        """
        点击回复按钮
        :param control:
        :return:
        """
        # 使用复杂条件查找并执行操作
        edit_control=self.find_and_perform_action(control)
        library_logger.debug(f"edit_control:{edit_control}")
        # self.analyze_comment_control(edit_control)
        # siblings_info = self.analyze_second_level_parent_siblings(edit_control)
        #library_logger.debug(f"siblings_info:{siblings_info}")
        try:
            first_next = self.get_first_non_empty_sibling(edit_control, 'next', 0)
            library_logger.debug(f"first_next:{first_next}")
            if first_next is None:
                library_logger.warning(f"没有找到第一个非空兄弟节点{first_next}")
            else:
                self.continue_control_config(first_next)
        except Exception as e:
            library_logger.error(f"查找编辑框下边的一个控件出现错误: {e}")
        time.sleep(0.5)
        if edit_control:
            huifu_button=auto.TextControl(searchFromControl=edit_control.GetParentControl(),
                                          Name="回复",
                                          searchDepth=10)
            if self.back_click_model:
                self.WeChat_Auto_utils.backstage_click(huifu_button)
            else:
                self.WeChat_Auto_utils.default_click(huifu_button)
        else:
            library_logger.debug("没有找到编辑控件")


    def click_reply_text_near_edit(self,edit_control, **kwargs):
        """
        找到编辑控件附近的回复文本并点击

        :param edit_control: 匹配到的编辑控件
        :return: 是否成功点击
        """
        # 获取编辑控件的父控件（包含所有兄弟节点）
        parent = edit_control.GetParentControl()
        if not parent:
            library_logger.warning("编辑控件没有父控件")
            return False

        # 获取所有兄弟节点
        siblings = parent.GetChildren()

        # 在兄弟节点中查找包含回复文本的控件
        for sibling in siblings:
            if sibling == edit_control:
                continue  # 跳过自己

            # 在兄弟节点中递归查找回复文本控件
            reply_text = self.find_descendant_matching(sibling, self.is_reply_text_control, max_depth=10)

            if reply_text:
                try:
                    library_logger.info(f"找到并点击回复文本控件: {reply_text.Name}")
                    if kwargs.get('back_click_model', False):
                        self.WeChat_Auto_utils.backstage_click(reply_text)
                    else:
                        reply_text.Click(simulateMove=kwargs.get('simulateMove', True))

                    time.sleep(kwargs.get('wait_time', 1.5))
                    return True
                except Exception as e:
                    library_logger.warning(f"点击回复文本时出错: {e}")
                    return False

        library_logger.warning("未找到回复文本控件")
        return False

    def find_descendant_matching(self,control, condition, max_depth=10):
        """
        在控件的后代中递归查找满足条件的控件

        :param control: 要搜索的控件
        :param condition: 匹配条件
        :param max_depth: 最大搜索深度
        :return: 找到的控件或None
        """
        if max_depth <= 0:
            return None

        children = control.GetChildren()
        for child in children:
            if condition(child):
                return child

            found = self.find_descendant_matching(child, condition, max_depth - 1)
            if found:
                return found

        return None
    def is_edit_control(self,control, **kwargs):
        """检查是否是编辑控件"""
        try:
            return (control.LocalizedControlType == "编辑" and
                    control.ControlType == 0xC354)  # UIA_EditControlTypeId
        except Exception:
            return False

    def is_reply_text_control(self,control):
        """检查是否是回复文本控件"""
        try:
            if control.Name == "回复" and control.LocalizedControlType == "文本":
                return True
        except Exception:
            return False
    def is_edit_text_control(self,control):
        """
        判断给定的控件是否是编辑控件。
        根据你的实际观察，可能还需要检查其他属性，如ClassName或AutomationId，以提高准确性。
        :param child:
        :return:
        """
        try:
            if control.LocalizedControlType == "编辑":
                return True
        except Exception:
            return False

    def find_and_perform_action(self, parent_control,condition_func=None, max_depth=10,search_depth=50):
        """
        递归地从父控件开始查找所有层级的子控件，根据匹配条件执行相应操作。
        :param parent_control: 开始查找的父控件（例如一个评论项）
        """

        edit_contorl=auto.EditControl(searchFromControl=parent_control.GetParentControl(),searchDepth=50)
        library_logger.debug(f"edit_contorl:{edit_contorl}")
        if edit_contorl.Exists(maxSearchSeconds=3):
            return edit_contorl
        else:
            return None

    def check_match_conditions(self,control, match_conditions, **kwargs):
        """
        检查控件是否匹配条件
        :param control: 要检查的控件
        :param match_conditions: 匹配条件，可以是：
            - 单个条件函数
            - 条件函数列表（与关系）
            - 条件函数字典（支持复杂组合）
        :return: 是否匹配
        """
        if match_conditions is None:
            # 默认匹配条件：回复计数文本控件
            return False

        # 单个条件函数
        if callable(match_conditions):
            return match_conditions(control, **kwargs)

        # 条件列表（所有条件都必须满足）
        if isinstance(match_conditions, list):
            return all(cond(control, **kwargs) for cond in match_conditions)

        # 条件字典（支持复杂组合匹配）
        if isinstance(match_conditions, dict):
            return self.check_complex_conditions(control, match_conditions, **kwargs)

        return False

    def check_complex_conditions(self, control, conditions, **kwargs):
        """
        检查复杂组合条件
        :param control: 要检查的控件
        :param conditions: 条件字典，支持多种组合方式：
            - "self": 对当前控件的条件
            - "children": 对子控件的条件列表
            - "siblings": 对兄弟控件的条件列表
            - "parent": 对父控件的条件
            - "and": 多个条件的与组合
            - "or": 多个条件的或组合
        :return: 是否匹配所有条件
        """
        for key, value in conditions.items():
            if key == "self":
                if not self.check_match_conditions(control, value, **kwargs):
                    return False

            elif key == "children":
                children = control.GetChildren()
                for child_condition in value:
                    child_match = any(
                        self.check_match_conditions(child, child_condition, **kwargs)
                        for child in children
                    )
                    if not child_match:
                        return False

            elif key == "descendants":
                # 递归搜索所有后代控件
                for descendant_condition in value:
                    if not self.has_descendant_matching(control, descendant_condition, **kwargs):
                        return False

            elif key == "siblings":
                parent = control.GetParentControl()
                if parent:
                    siblings = parent.GetChildren()
                    for sibling_condition in value:
                        sibling_match = any(
                            self.check_match_conditions(sibling, sibling_condition, **kwargs)
                            for sibling in siblings if sibling != control
                        )
                        if not sibling_match:
                            return False
                else:
                    return False

            elif key == "parent":
                parent = control.GetParentControl()
                if not parent or not self.check_match_conditions(parent, value, **kwargs):
                    return False

            elif key == "and":
                for condition in value:
                    if not self.check_match_conditions(control, condition, **kwargs):
                        return False

            elif key == "or":
                or_match = any(
                    self.check_match_conditions(control, condition, **kwargs)
                    for condition in value
                )
                if not or_match:
                    return False

        return True

    def has_descendant_matching(self, control, condition, max_depth=10, **kwargs):
        """
        检查控件是否有后代满足条件
        """
        if max_depth <= 0:
            return False

        children = control.GetChildren()
        for child in children:
            if self.check_match_conditions(child, condition, **kwargs):
                return True

            if self.has_descendant_matching(child, condition, max_depth - 1, **kwargs):
                return True

        return False
    def default_click_action(self, control, **kwargs):
        """默认点击操作"""
        library_logger.info(f"尝试点击控件: {control.Name}")
        if self.back_click_model:
            self.WeChat_Auto_utils.backstage_click(control)
        else:
            control.Click(simulateMove=kwargs.get('simulateMove', True))

        time.sleep(kwargs.get('wait_time', 1.5))
        return True
    def random_select(self):
        """
        从列表中随机抽取一个元素（不改变原列表）

        参数:
            items (list): 待抽取的列表

        返回:
            随机选中的元素
        """
        #return random.choice(items)  # 核心调用 random.choice()
        return self.FairSelector_class.select()

    def item_comment_func(self,temp_control,model="1"):
        """
        关注的情况
        1.点击头像和名字直接进入主页了，分析是否已关注，已关注直接关闭
        2.点击名字无效，点击头像出现资料卡，然后再点击视频号进入主页，分析是否已关注，已关注直接关闭
        3.点击名字无效，点击头像也无效，不跳转个人主页
        有个情况要注意一下，就是他评论的时候名字是"如来💯如顺",但是点击个人头像的时候,显示资料卡是"大吉大钰",主页名字也是"大吉大钰"
        尽量点击头像
        """
        """
        回复的情况
        1.点击要回复的用户,自动焦点锁定在输入框，
        """
        """
        ""组
            -"老林主任"文本      #评论作者名
        "广东"文本              #评论地区
        "6天前"文本             #评论日期
        ""组                   #评论内容
            -"有靠谱的路子"文本
            -"墙"未加标签的图片
        ""组                   *评论的点赞数
            -""图像
        ""组
            -"回复"文本         *点击回复
        :param temp_control:
        :return:
        """
        required_comment_data = {
            "comment_author_name": None,  # 评论作者名称
            "comment_create_time": None,  # 评论日期
            "comment_from": None,  # 评论地区
            "comment_content": None,  # 评论内容
        }
        try:
            if model=="2":
                #自己刚评论的，只有名字，时间，内容
                required_comment_data["comment_create_time"] = self.WeChat_VideoData_utils.format_time(temp_control.Name)
                comment_author_name_str =self.cat_author_name(temp_control)
                required_comment_data["comment_author_name"] = comment_author_name_str
                content = temp_control.GetNextSiblingControl().GetChildren()
                content_str = ""
                for child in content:
                    if child.ControlTypeName == "TextControl":
                        content_str += child.Name
                required_comment_data["comment_content"] = content_str
            else:
                #别人评论的，包括作者评论的
                comment_author_name_str =self.cat_author_name(temp_control)
                content = temp_control.GetNextSiblingControl().GetNextSiblingControl().GetChildren()
                content_str = ""
                for child in content:
                    #library_logger.debug(f"child: {child}的控件类型是: {child.ControlTypeName}")
                    if child.ControlTypeName == "TextControl":
                        content_str += child.Name
                    elif child.ControlTypeName=="HyperlinkControl":
                        content_str += child.Name
                required_comment_data["comment_from"]=temp_control.Name
                required_comment_data["comment_create_time"] = self.WeChat_VideoData_utils.format_time(temp_control.GetNextSiblingControl().Name)
                required_comment_data["comment_author_name"] =comment_author_name_str
                required_comment_data["comment_content"] = content_str
        except Exception as e:
            library_logger.warning(f"item_comment_func出错: {e}")
        return required_comment_data
    def search_pinglun_text_control_func(self):
        """
        查找评论关键字，通过这个关键字来获取评论，返回其父节点，然后通过父节点往下找获取评论
        :return:
        """
        search_pinglun_text_control = auto.TextControl(searchFromControl=self.WECHAT_PANE, Name="评论")
        if search_pinglun_text_control.Exists():
            search_pinglun_text_control = search_pinglun_text_control.GetParentControl()
            return search_pinglun_text_control


    @staticmethod
    def log_caller(func):
        import functools
        import traceback
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            stack = traceback.extract_stack()
            caller = stack[-2]
            #print(f"{func.__name__} called by: {caller.filename} at line {caller.lineno}")
            return func(*args, **kwargs)

        return wrapper

    @log_caller
    def scroll_video_comment(self,next_sibling,model: str = "down"):
        library_logger.debug(f"滚动屏幕")
        try:
            scroll_container = auto.DocumentControl(searchDepth=8, Name=next_sibling.Name)  # 根据你的查找条件调整
            if scroll_container.Exists():
                rect = scroll_container.BoundingRectangle
                if rect.width() > 0 and rect.height() > 0:
                    # 计算文档控件的中心坐标
                    center_x = (rect.left + rect.right) // 2
                    center_y = (rect.top + rect.bottom) // 2

                    # 将鼠标移动到该中心点（确保操作焦点在目标区域）
                    auto.MoveTo(center_x, center_y)
                    time.sleep(0.2)  # 稍作停顿
                    if model=="down":
                        auto.WheelDown(waitTime=self.scroll_video_comment_time)
                    elif model=="up":
                        auto.WheelUp(waitTime=self.scroll_video_comment_time)
                    # 模拟鼠标滚轮向下滚动
                    #auto.WheelDown(waitTime=self.scroll_video_comment_time)  # waitTime控制滚动间隔[1](@ref)
                    #library_logger.info("单个视频获取评论-模拟鼠标滚轮向下滚动成功")
                else:
                    pass
                    #library_logger.info("单个视频获取评论-文档控件边界矩形无效")
            else:
                pass
                #library_logger.info("单个视频获取评论-未找到指定的文档控件")
            #library_logger.info("单个视频获取评论-未找到可滚动容器")
            return True

        except Exception as e:
            library_logger.warning(f"单个视频获取评论-滚动操作失败: {e}")
            return False
    def scroll_top(self):
        pass
    def set_comment_callback(self, callback_func):
        """
        设置评论数据回调函数

        Args:
            callback_func: 回调函数，接收单条评论数据和对应的视频数据作为参数
        """
        self.comment_callback = callback_func

class WeChatVideoCrawler:
    """
    微信视频号数据爬取管理器（ facade模式/门面模式 ）
    封装了从启动微信到获取视频数据的完整流程，简化调用。
    """

    def __init__(self):
        """初始化爬虫管理器"""
        self.automator = None  # 微信自动化器实例
        self.comment_callback = None  # 评论回调函数

    def initialize(self,wechat_path:str=r"C:\Program Files\Tencent\Weixin\Weixin.exe",scroll_video_comment_time: float=1.0,back_click_model:bool=False):
        """
        初始化微信自动化环境。
        完成所有必要的准备工作。
        """
        self.automator = WeChatAutomator(scroll_video_comment_time,back_click_model)
        # 1. 打开微信，并激活
        self.automator.start_webchat(wechat_path)
        # 2. 查找微信窗口
        self.automator.search_wechat()
        # 3. 点击打开视频号
        self.automator.open_video_channel()
        # 4. 查找视频号窗口
        self.automator.find_video_channel()
        library_logger.info("WeChatVideoCrawler 初始化完成。")

    def set_comment_callback(self, callback_func):
        """
        设置用于处理评论数据的回调函数。

        Args:
            callback_func (function): 一个接受 comment_data 和 video_data 为参数的函数。
        """
        self.comment_callback = callback_func
        # 将回调设置给底层的 automator
        if self.automator:
            self.automator.set_comment_callback(callback_func)
        library_logger.info("评论回调函数设置成功。")

    def crawl(self,
              search_keyword:str,
              comment_datetime: str,
              comment_key:list[str]=None,
              skip_comment:bool=False,
              comment_list:list[str]=None,
              comment_day: str = "7",
              Interval_count: int = 1,
              Interval_minutes: int = 5):
        """
        执行视频号数据爬取的主要方法。

        Args:
            search_keyword (str): 要在视频号中搜索的关键字。
            skip_comment (bool): 是否跳过评论获取。默认为 False。False就是跳过评论，不抓取评论，True就是要评论，不跳过
            comment_key (list): 评论中带这些关键字
            comment_list (list): 回复的内容,随机或者按顺序
            comment_day (str): 离当前日期的天数
            comment_datetime (str): 默认为当前日期,可修改为其他日期，格式为2025-9-26 15:15:15
            Interval_count(int):间隔条数
            Interval_minutes(int):间隔分钟数 ,里面有个代码*60变成秒的单位

        Returns:
            list: 视频数据列表。
        """
        if not self.automator:
            raise RuntimeError("爬虫器未初始化，请先调用 initialize() 方法。")

        # 5. 通过视频号窗口-输入关键字并搜索
        self.automator.input_keyword_search(search_keyword)
        # 6. 等待视频列表加载完成
        status = self.automator.video_channel_lodding()

        if not status:
            library_logger.warning("视频列表加载失败。")
            return []

        # 7. 循环并自动滚动获取每个视频的数据
        library_logger.info(f"开始爬取关键词 '{search_keyword}' 的视频数据...")
        list_data = self.automator.video_list_data(skip_comment=skip_comment,
                                                   comment_key=comment_key,
                                                   comment_list=comment_list,
                                                   comment_day=comment_day,
                                                   comment_datetime=comment_datetime,
                                                   Interval_count=Interval_count,
                                                   Interval_seconds=Interval_minutes)

        library_logger.info(f"爬取完成！共获取到 {len(list_data)} 个视频的数据。")
        return list_data


def handle_single_comment(comment_data, video_data):
    """
    处理单条评论数据的回调函数示例
    """
    print(f"视频 '{video_data.get('video_title', '未知')}' 收到一条评论:")
    print(f"  作者: {comment_data.get('comment_author_name', '未知')}")
    print(f"  内容: {comment_data.get('comment_content', '无内容')}")
    print(f"  时间: {comment_data.get('comment_create_time', '未知')}")
