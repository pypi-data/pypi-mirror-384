import os
import sys
import winreg
import ctypes
import shutil
from pathlib import Path
from typing import Tuple, Optional
"""
注册表/启动文件夹方式
是否需要用户登录	  ✅ 需要
运行时机		      用户登录后
运行账户		      登录用户
运行环境		      用户桌面环境
权限级别		      用户权限
可见性		      在任务栏可见

"""
class B_WindowsAutoStart:
    """
    Windows系统开机自启动管理类
    提供两种方式实现开机自启动：注册表方式和启动文件夹方式
    """

    @staticmethod
    def _is_admin() -> bool:
        """
        检查当前是否以管理员权限运行

        返回:
            bool: True表示有管理员权限，False表示无
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    @staticmethod
    def add_via_registry(app_name: str,
                         executable_path: str,
                         all_users: bool = False) -> Tuple[bool, Optional[str]]:
        """
        通过注册表添加开机自启动项

        参数:
            app_name (str): 应用唯一标识名称
            executable_path (str): 可执行文件的完整路径
            all_users (bool): 是否为所有用户启用(默认False,仅当前用户)

        返回:
            Tuple[bool, Optional[str]]: (是否成功, 错误信息)

        示例:
            success, error = B_WindowsAutoStart.add_via_registry(
                "MyApp",
                r"C:\Program Files\MyApp\app.exe"
            )
        """
        try:
            # 确定注册表路径
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            hive = winreg.HKEY_LOCAL_MACHINE if all_users else winreg.HKEY_CURRENT_USER

            # 检查管理员权限
            if all_users and not B_WindowsAutoStart._is_admin():
                return False, "需要管理员权限为所有用户设置自启动"

            # 打开或创建注册表项
            with winreg.OpenKey(hive, key_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, executable_path)

            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def remove_via_registry(app_name: str,
                            all_users: bool = False) -> Tuple[bool, Optional[str]]:
        """
        从注册表移除开机自启动项

        参数:
            app_name (str): 应用唯一标识名称
            all_users (bool): 是否为所有用户设置(默认False,仅当前用户)

        返回:
            Tuple[bool, Optional[str]]: (是否成功, 错误信息)

        示例:
            success, error = B_WindowsAutoStart.remove_via_registry("MyApp")
        """
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            hive = winreg.HKEY_LOCAL_MACHINE if all_users else winreg.HKEY_CURRENT_USER

            # 检查管理员权限
            if all_users and not B_WindowsAutoStart._is_admin():
                return False, "需要管理员权限移除所有用户的自启动"

            # 打开注册表项并删除
            with winreg.OpenKey(hive, key_path, 0, winreg.KEY_WRITE) as key:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    # 如果注册表项不存在，视为成功
                    return True, None

            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def add_via_startup_folder(app_name: str,
                               executable_path: str,
                               all_users: bool = False) -> Tuple[bool, Optional[str]]:
        """
        通过启动文件夹添加开机自启动项

        参数:
            app_name (str): 应用名称（用于创建快捷方式）
            executable_path (str): 可执行文件的完整路径
            all_users (bool): 是否为所有用户启用(默认False,仅当前用户)

        返回:
            Tuple[bool, Optional[str]]: (是否成功, 错误信息)

        示例:
            success, error = B_WindowsAutoStart.add_via_startup_folder(
                "MyApp",
                r"C:\Program Files\MyApp\app.exe"
            )
        """
        try:
            # 获取启动文件夹路径
            if all_users:
                startup_path = Path(os.environ.get("ProgramData")) / \
                               "Microsoft" / "Windows" / "Start Menu" / "Programs" / "StartUp"
            else:
                startup_path = Path(os.environ.get("APPDATA")) / \
                               "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

            # 确保启动文件夹存在
            startup_path.mkdir(parents=True, exist_ok=True)

            # 创建快捷方式
            shortcut_path = startup_path / f"{app_name}.lnk"

            # 使用Python创建快捷方式
            from win32com.client import Dispatch
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.TargetPath = executable_path
            shortcut.WorkingDirectory = str(Path(executable_path).parent)
            shortcut.save()

            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def remove_via_startup_folder(app_name: str,
                                  all_users: bool = False) -> Tuple[bool, Optional[str]]:
        """
        从启动文件夹移除开机自启动项

        参数:
            app_name (str): 应用名称（快捷方式文件名）
            all_users (bool): 是否为所有用户设置(默认False,仅当前用户)

        返回:
            Tuple[bool, Optional[str]]: (是否成功, 错误信息)

        示例:
            success, error = B_WindowsAutoStart.remove_via_startup_folder("MyApp")
        """
        try:
            # 获取启动文件夹路径
            if all_users:
                startup_path = Path(os.environ.get("ProgramData")) / \
                               "Microsoft" / "Windows" / "Start Menu" / "Programs" / "StartUp"
            else:
                startup_path = Path(os.environ.get("APPDATA")) / \
                               "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

            # 删除快捷方式
            shortcut_path = startup_path / f"{app_name}.lnk"

            if shortcut_path.exists():
                shortcut_path.unlink()

            return True, None
        except Exception as e:
            return False, str(e)

"""

from bruce_autostart.b_autostart import B_WindowsAutoStart

# 当前用户注册表方式添加自启动
success, error = B_WindowsAutoStart.add_via_registry(
    "MyApp",
    r"C:\Program Files\MyApp\app.exe"
)

# 所有用户启动文件夹方式添加自启动
success, error = B_WindowsAutoStart.add_via_startup_folder(
    "MyApp",
    r"C:\Program Files\MyApp\app.exe",
    all_users=True
)

# 移除自启动项
B_WindowsAutoStart.remove_via_registry("MyApp")
B_WindowsAutoStart.remove_via_startup_folder("MyApp", all_users=True)
"""