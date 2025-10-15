#!python3
# -*- coding:utf-8 -*-
import sys
import time
import uiautomation as auto

class UIControlEnumerator:
    """UI控件枚举器，用于查看和记录UI控件树结构"""

    def __init__(self, delay_seconds=3, show_all_name=False, show_pid=False):
        """
        初始化枚举器
        :param delay_seconds: 开始枚举前的延迟时间（秒）
        :param show_all_name: 是否显示控件全名
        :param show_pid: 是否显示进程ID
        """
        self.delay_seconds = delay_seconds
        self.show_all_name = show_all_name
        self.show_pid = show_pid
        auto.Logger.Write('UIAutomation {} (Python {}.{}.{}, {} bit)\n'.format(
            auto.VERSION, sys.version_info.major, sys.version_info.minor,
            sys.version_info.micro, 64 if sys.maxsize > 0xFFFFFFFF else 32))

    def _wait_and_log_start(self):
        """等待延迟并记录开始信息"""
        if self.delay_seconds > 0:
            auto.Logger.Write('please wait for {0} seconds\n\n'.format(self.delay_seconds), writeToFile=False)
            time.sleep(self.delay_seconds)
        auto.Logger.ColorfullyLog('Starts, Current Cursor Position: <Color=Cyan>{}</Color>'.format(auto.GetCursorPos()))

    def enumerate_from_root(self, depth=0xFFFFFFFF):
        """从根控件（桌面）开始枚举控件树"""
        self._wait_and_log_start()
        control = auto.GetRootControl()
        auto.EnumAndLogControl(control, depth, self.show_all_name, self.show_pid)
        auto.Logger.Log('Ends\n')

    def enumerate_from_focus(self, depth=0xFFFFFFFF):
        """从焦点控件开始枚举控件树"""
        self._wait_and_log_start()
        control = auto.GetFocusedControl()
        if control:
            control_list = []
            while control:
                control_list.insert(0, control)
                control = control.GetParentControl()
            if len(control_list) == 1:
                control = control_list[0]
            else:
                control = control_list[1]
                auto.LogControl(control_list[0], 0, self.show_all_name, self.show_pid)
            auto.EnumAndLogControl(control, depth, self.show_all_name, self.show_pid, startDepth=1)
        else:
            auto.Logger.Write('No focused control found\n', auto.ConsoleColor.Yellow)
        auto.Logger.Log('Ends\n')

    def enumerate_from_cursor(self, depth=0xFFFFFFFF, enumerate_ancestors=False):
        """
        从光标下控件开始枚举
        :param depth: 枚举深度
        :param enumerate_ancestors: 是否枚举祖先控件
        """
        self._wait_and_log_start()
        control = auto.ControlFromCursor()

        if not control:
            auto.Logger.Write('No control found under cursor\n', auto.ConsoleColor.Yellow)
            return

        if enumerate_ancestors:
            auto.EnumAndLogControlAncestors(control, self.show_all_name, self.show_pid)
        else:
            if depth < 0:
                while depth < 0 and control:
                    control = control.GetParentControl()
                    depth += 1
                depth = 0xFFFFFFFF
            auto.EnumAndLogControl(control, depth, self.show_all_name, self.show_pid)

        auto.Logger.Log('Ends\n')

    def enumerate_ancestors_from_cursor(self):
        """枚举光标下控件的祖先控件"""
        self.enumerate_from_cursor(enumerate_ancestors=True)


# 使用示例
# if __name__ == '__main__':
#     # 创建枚举器实例
#     enumerator = UIControlEnumerator(delay_seconds=3, show_all_name=True, show_pid=True)
#
#     # 示例1: 从根控件开始枚举
#     # enumerator.enumerate_from_root(depth=2)
#
#     # 示例2: 从焦点控件开始枚举
#     # enumerator.enumerate_from_focus()
#
#     # 示例3: 从光标下控件开始枚举
#     enumerator.enumerate_from_cursor()
#
#     # 示例4: 枚举光标下控件的祖先
#     # enumerator.enumerate_ancestors_from_cursor()