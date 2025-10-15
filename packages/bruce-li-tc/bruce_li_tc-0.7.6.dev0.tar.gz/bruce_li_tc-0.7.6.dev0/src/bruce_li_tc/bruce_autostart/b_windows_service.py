# 文件名: b_service_manager.py

import win32serviceutil
import win32service
import win32event
import subprocess
import sys
import os
import time
import winreg
"""
Windows 服务方式
是否需要用户登录	❌ 不需要
运行时机	        系统启动时	
运行账户	        SYSTEM	
运行环境	        后台无界面	
权限级别	        最高权限	
可见性	        完全隐藏	
- 无论用户是否登录，服务都会运行
- 用户锁定屏幕（Win+L）后服务继续运行
- 切换用户账户不影响服务运行
"""

class B_ServiceManager:
    """
    Windows服务管理器 - 提供简单的API直接管理服务

    特性:
    - 安装服务: 只需提供exe或py文件路径
    - 启动服务: 服务将在系统启动时自动运行，无需用户登录
    - 停止服务: 停止运行中的服务
    - 卸载服务: 完全移除服务配置

    使用方法:
    manager = B_ServiceManager()

    # 安装并启动服务
    manager.install_start("MyService", "C:\\path\\to\\test1.exe")

    # 停止服务
    manager.stop("MyService")

    # 卸载服务
    manager.uninstall("MyService")
    """

    def __init__(self):
        self.service_class_cache = {}

    def install_start(self, service_name: str, file_path: str, display_name: str = None):
        """
        安装并立即启动服务

        参数:
            service_name (str): 服务唯一标识名
            file_path (str): 要运行的可执行文件或Python脚本路径
            display_name (str): 服务显示名称(可选)

        返回:
            bool: 是否成功
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 创建动态服务类
        service_class = self._create_service_class(service_name, file_path, display_name)

        # 安装服务
        try:
            win32serviceutil.InstallService(
                None,
                service_name,
                display_name or service_name,
                startType=win32service.SERVICE_AUTO_START
            )
            print(f"服务 '{service_name}' 安装成功")
        except Exception as e:
            print(f"服务安装失败: {str(e)}")
            return False

        # 启动服务
        try:
            win32serviceutil.StartService(service_name)
            print(f"服务 '{service_name}' 启动成功")
            return True
        except Exception as e:
            print(f"服务启动失败: {str(e)}")
            # 安装失败时尝试卸载
            self.uninstall(service_name)
            return False

    def start(self, service_name: str):
        """
        启动已安装的服务

        参数:
            service_name (str): 服务唯一标识名

        返回:
            bool: 是否成功
        """
        try:
            win32serviceutil.StartService(service_name)
            print(f"服务 '{service_name}' 启动成功")
            return True
        except Exception as e:
            print(f"服务启动失败: {str(e)}")
            return False

    def stop(self, service_name: str):
        """
        停止正在运行的服务

        参数:
            service_name (str): 服务唯一标识名

        返回:
            bool: 是否成功
        """
        try:
            win32serviceutil.StopService(service_name)
            print(f"服务 '{service_name}' 停止成功")
            return True
        except Exception as e:
            print(f"服务停止失败: {str(e)}")
            return False

    def uninstall(self, service_name: str):
        """
        卸载服务

        参数:
            service_name (str): 服务唯一标识名

        返回:
            bool: 是否成功
        """
        # 先尝试停止服务
        try:
            self.stop(service_name)
        except:
            pass

        # 卸载服务
        try:
            win32serviceutil.RemoveService(service_name)
            print(f"服务 '{service_name}' 卸载成功")
            return True
        except Exception as e:
            print(f"服务卸载失败: {str(e)}")
            return False

    def is_installed(self, service_name: str) -> bool:
        """
        检查服务是否已安装

        参数:
            service_name (str): 服务唯一标识名

        返回:
            bool: 是否已安装
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                f"SYSTEM\\CurrentControlSet\\Services\\{service_name}"
            )
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def is_running(self, service_name: str) -> bool:
        """
        检查服务是否正在运行

        参数:
            service_name (str): 服务唯一标识名

        返回:
            bool: 是否正在运行
        """
        try:
            status = win32serviceutil.QueryServiceStatus(service_name)
            # 状态码1表示运行中
            return status[1] == win32service.SERVICE_RUNNING
        except:
            return False

    def _create_service_class(self, service_name: str, file_path: str, display_name: str = None):
        """
        创建动态服务类
        """
        if service_name in self.service_class_cache:
            return self.service_class_cache[service_name]

        # 动态创建服务类
        class DynamicService(win32serviceutil.ServiceFramework):
            _svc_name_ = service_name
            _svc_display_name_ = display_name or service_name

            def __init__(self, args):
                super().__init__(args)
                self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
                self.process = None

            def SvcStop(self):
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                win32event.SetEvent(self.hWaitStop)
                if self.process:
                    self.process.terminate()

            def SvcDoRun(self):
                self.ReportServiceStatus(win32service.SERVICE_RUNNING)
                # 启动目标程序
                try:
                    if file_path.endswith('.py'):
                        # Python脚本
                        self.process = subprocess.Popen([sys.executable, file_path])
                    else:
                        # 可执行文件
                        self.process = subprocess.Popen(file_path)

                    # 等待停止事件或进程结束
                    while True:
                        if win32event.WaitForSingleObject(self.hWaitStop, 1000) == win32event.WAIT_OBJECT_0:
                            break
                        if self.process.poll() is not None:
                            break
                finally:
                    if self.process:
                        self.process.terminate()

        # 缓存类避免重复创建
        self.service_class_cache[service_name] = DynamicService
        return DynamicService


#from b_service_manager import B_ServiceManager

# def setup_background_service():
#     manager = B_ServiceManager()
#     service_name = "BruceDataSync"
#     py_script = r"C:\apps\data_sync.py"
#
#     # 检查是否已安装
#     if not manager.is_installed(service_name):
#         # 安装并启动服务
#         if manager.install_start(service_name, py_script, "Bruce数据同步服务"):
#             print("后台服务安装成功")
#     else:
#         # 确保服务正在运行
#         if not manager.is_running(service_name):
#             manager.start(service_name)
#
#
# def remove_service():
#     manager = B_ServiceManager()
#     service_name = "BruceDataSync"
#
#     if manager.is_installed(service_name):
#         # 停止并卸载服务
#         manager.stop(service_name)
#         manager.uninstall(service_name)
#         print("服务已移除")