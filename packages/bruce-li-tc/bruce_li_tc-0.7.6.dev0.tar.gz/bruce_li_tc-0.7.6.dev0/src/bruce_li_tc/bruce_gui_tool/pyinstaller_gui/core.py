import os
import re
import subprocess
import datetime
import sys
import requests


class Packager:
    """核心打包类，包含所有打包逻辑"""

    def __init__(self, config):
        """
        初始化打包器
        :param config: 包含所有配置参数的字典
        """
        self.config = config
        self.log_callback = config.get('log_callback', print)
        self.progress_callback = config.get('progress_callback', lambda x: None)

    def log(self, message):
        """记录日志消息"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        self.log_callback(formatted)

    def get_python_version(self):
        """获取Python版本"""
        try:
            result = subprocess.run(
                [self.config['python_exec'], "--version"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip().replace("Python ", "")
        except Exception as e:
            self.log(f"获取Python版本失败: {str(e)}")
            return "未知"

    def get_pyinstaller_version(self):
        """获取PyInstaller版本"""
        try:
            result = subprocess.run(
                [self.config['python_exec'], "-m", "pip", "show", "pyinstaller"],
                capture_output=True, text=True, check=True
            )
            version_line = [line for line in result.stdout.splitlines()
                            if line.startswith("Version:")]
            return version_line[0].split(":")[1].strip() if version_line else "未安装"
        except Exception as e:
            self.log(f"获取PyInstaller版本失败: {str(e)}")
            return "未安装"

    def get_latest_pyinstaller_version(self):
        """获取PyPI上的最新PyInstaller版本"""
        try:
            response = requests.get("https://pypi.org/pypi/pyinstaller/json", timeout=3)
            if response.status_code == 200:
                return response.json()["info"]["version"]
            return "未知"
        except Exception as e:
            self.log(f"获取最新版本失败: {str(e)}")
            return "未知"

    def get_next_version(self, base_name):
        """
        获取下一个版本号
        :param base_name: 基础名称
        :return: 下一个版本文件名
        """
        dist_dir = self.config.get('dist_dir', 'dist')
        try:
            if not os.path.exists(dist_dir):
                return f"{base_name}_v0.0.1.exe", base_name

            pattern = re.compile(r'^(.*?)_v(\d+)\.(\d+)\.(\d+)\.exe$')
            max_version = (0, 0, 0)
            detected_base = base_name

            for filename in os.listdir(dist_dir):
                if filename.endswith('.exe'):
                    match = pattern.match(filename)
                    if match:
                        try:
                            file_base = match.group(1)
                            version = tuple(map(int, match.groups()[1:4]))
                            if version > max_version:
                                max_version = version
                                detected_base = file_base
                        except ValueError:
                            continue

            next_patch = max_version[2] + 1
            next_version = f"{detected_base}_v{max_version[0]}.{max_version[1]}.{next_patch}.exe"

            # 更新基础名称
            if detected_base != base_name:
                self.log(f"检测到已有版本，自动设置基础名称为: {detected_base}")
                return next_version, detected_base

            return next_version, base_name
        except Exception as e:
            self.log(f"版本检测出错: {str(e)}")
            return f"{base_name}_v0.0.1.exe", base_name

    def validate_icon(self, icon_path):
        """验证图标文件是否存在且有效"""
        if not icon_path:
            return True, "未指定图标"

        if not os.path.exists(icon_path):
            return False, f"图标文件不存在: {icon_path}"

        if not icon_path.lower().endswith('.ico'):
            return False, f"图标文件扩展名不是.ico: {icon_path}"

        return True, "图标验证通过"

    def update_pyinstaller(self):
        """升级PyInstaller"""
        self.log("开始升级PyInstaller...")
        try:
            process = subprocess.Popen(
                [self.config['python_exec'], "-m", "pip", "install", "--upgrade", "pyinstaller"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in process.stdout:
                self.log(line.strip())

            process.wait()

            if process.returncode == 0:
                self.log("PyInstaller升级成功")
                return True
            else:
                self.log(f"PyInstaller升级失败，返回码: {process.returncode}")
                return False
        except Exception as e:
            self.log(f"升级过程中出错: {e}")
            return False

    def build(self):
        """执行打包过程"""
        # 准备参数
        config = self.config
        command = [
            config['python_exec'],
            "-m", "PyInstaller",
            "--name", config['output_name']
        ]

        # 添加选项
        if config.get('onefile', True):
            command.append("--onefile")
        if config.get('noconsole', False):
            command.append("--noconsole")
        if config.get('clean', True):
            command.append("--clean")
        if config.get('icon') and os.path.exists(config['icon']):
            command.extend(["--icon", config['icon']])

        # 添加附加数据
        for item in config.get('data', []):
            if item.strip():
                command.extend(["--add-data", item.strip()])

        # 添加隐藏导入
        for imp in config.get('hidden_imports', []):
            if imp.strip():
                command.extend(["--hidden-import", imp.strip()])

        # 添加排除模块
        for mod in config.get('exclude_modules', []):
            if mod.strip():
                command.extend(["--exclude-module", mod.strip()])

        # 添加入口文件
        command.append(config['entry_file'])

        self.log(f"执行命令: {' '.join(command)}")

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=config['project_dir']
            )

            # 读取输出并更新进度
            progress = 0
            for line in process.stdout:
                self.log(line.strip())

                # 简单的进度模拟
                if "Analyzing" in line:
                    progress = min(progress + 5, 30)
                elif "Processing" in line:
                    progress = min(progress + 2, 70)
                elif "Building" in line:
                    progress = min(progress + 1, 95)

                self.progress_callback(progress)

            process.wait()
            self.progress_callback(100)

            if process.returncode == 0:
                self.log("打包成功完成")
                return True
            else:
                self.log(f"打包失败，返回码: {process.returncode}")
                return False
        except Exception as e:
            self.log(f"打包过程中出错: {str(e)}")
            return False