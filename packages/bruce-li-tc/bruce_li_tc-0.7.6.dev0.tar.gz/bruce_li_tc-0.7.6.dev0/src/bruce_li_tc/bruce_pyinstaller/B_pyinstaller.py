import os
import sys
import glob
import time
from pathlib import Path
from typing import List, Optional, Tuple, Union


class PyInstallerSpecBuilder:
    """
    PyInstaller Spec 文件生成器

    简化创建复杂的 PyInstaller spec 文件，支持添加各种资源文件和环境依赖。

    资源类型提示:
    - 目录: 使用 add_directory() - 适用于 Python 模块目录、静态资源目录等
    - 单个文件: 使用 add_file() - 适用于配置文件、数据文件等
    - 二进制文件: 使用 add_binary() - 适用于 .exe, .dll, .so, .zip, .jar 等
    - Python 模块: 使用 add_module() - 适用于需要显式导入的模块

    使用示例:
    >>> builder = PyInstallerSpecBuilder(
    ...     main_script="src/main.py",
    ...     output_name="my_app",
    ...     console=False
    ... )
    >>> # 添加目录 (Python 模块)
    >>> builder.add_directory("core", "core")
    >>> # 添加二进制文件 (.exe)
    >>> builder.add_binary("bin/tool.exe", '.')
    >>> # 添加 Python 模块
    >>> builder.add_module("pandas")
    >>> # 生成 spec 文件
    >>> builder.generate_spec("my_app.spec")
    """

    def __init__(self,
                 main_script: Optional[str] = None,
                 output_name: str = "app",
                 console: bool = True,
                 project_root: Optional[str] = None):
        """
        初始化 PyInstaller Spec 构建器

        :param main_script: 主应用程序入口脚本 (默认为项目根目录下的 main.py)
        :param output_name: 输出文件名（不含扩展名）
        :param console: 是否显示控制台窗口
        :param project_root: 项目根目录（可选，默认为当前工作目录）
        """
        # 设置项目根目录（默认为当前工作目录）
        self.project_root = Path(project_root or os.getcwd()).resolve()

        # 设置主脚本（默认为项目根目录下的 main.py）
        self.main_script = self._resolve_path(main_script or "main.py")

        # 基本配置
        self.output_name = output_name
        self.console = console

        # 初始化资源列表
        self.datas = []  # 数据文件/目录
        self.binaries = []  # 二进制文件
        self.hiddenimports = [  # 需要显式导入的Python模块
            'encodings.utf_8',
            'encodings.ascii',
            'encodings.latin_1',
            'encodings.cp1252'
        ]

        # 高级配置
        self.hookspath = []
        self.excludes = []
        self.upx = True
        self.upx_exclude = []
        self.additional_pathex = [str(self.project_root)]
        self.runtime_hooks = []
        self.win_no_prefer_redirects = False
        self.win_private_assemblies = False

        # 自动添加平台特定依赖
        if sys.platform == 'win32':
            self.add_module('psutil')
            self.add_module('psutil._psutil_windows')
            self.add_module('ctypes')
            self.add_module('ctypes.wintypes')

    def add_directory(self, source: str, target: str) -> Tuple[bool, str]:
        """
        添加整个目录到打包资源中

        适用于:
        - Python 模块目录 (包含 __init__.py 的目录)
        - 静态资源目录 (如 static, templates)
        - 配置文件目录

        :param source: 源目录路径（相对或绝对）
        :param target: 目标路径（在打包后的位置）
        :return: (是否成功, 消息)
        """
        source_path = self._resolve_path(source)

        if not source_path.exists():
            return False, f"目录 '{source_path}' 不存在"

        if not source_path.is_dir():
            return False, f"'{source_path}' 不是目录，请使用 add_file() 或 add_binary()"

        self.datas.append((str(source_path), target))
        return True, f"成功添加目录: {source} -> {target}"

    def add_file(self, source: str, target: str) -> Tuple[bool, str]:
        """
        添加单个文件到打包资源中

        适用于:
        - 配置文件 (.ini, .json, .yaml)
        - 数据文件 (.csv, .db, .txt)
        - Python 脚本 (.py)

        :param source: 源文件路径（相对或绝对）
        :param target: 目标路径（在打包后的位置）
        :return: (是否成功, 消息)
        """
        source_path = self._resolve_path(source)

        if not source_path.exists():
            return False, f"文件 '{source_path}' 不存在"

        if source_path.is_dir():
            return False, f"'{source_path}' 是目录，请使用 add_directory()"

        self.datas.append((str(source_path), target))
        return True, f"成功添加文件: {source} -> {target}"

    def add_binary(self, source: str, target: str) -> Tuple[bool, str]:
        """
        添加二进制文件到打包资源中

        适用于:
        - 可执行文件 (.exe, .bin)
        - 动态链接库 (.dll, .so)
        - 压缩文件 (.zip, .jar)
        - 其他二进制文件 (.dat, .bin, .pyd)

        :param source: 源文件路径（相对或绝对）
        :param target: 目标路径（在打包后的位置）
        :return: (是否成功, 消息)
        """
        source_path = self._resolve_path(source)

        if not source_path.exists():
            return False, f"二进制文件 '{source_path}' 不存在"

        if source_path.is_dir():
            return False, f"'{source_path}' 是目录，请使用 add_directory()"

        self.binaries.append((str(source_path), target))
        return True, f"成功添加二进制文件: {source} -> {target}"

    def add_module(self, module_name: str) -> Tuple[bool, str]:
        """
        添加需要显式导入的Python模块

        适用于:
        - PyInstaller 无法自动检测到的模块
        - 动态导入的模块
        - C扩展模块

        :param module_name: 模块名称（如 "pandas", "numpy.core"）
        :return: (是否成功, 消息)
        """
        if module_name in self.hiddenimports:
            return False, f"模块 '{module_name}' 已存在"

        self.hiddenimports.append(module_name)
        return True, f"成功添加Python模块: {module_name}"

    def add_node_env(self, node_exe_path: str, node_modules_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        添加Node.js环境到打包资源中

        :param node_exe_path: node.exe 或 node 可执行文件路径
        :param node_modules_path: node_modules 目录路径（可选）
        :return: (是否成功, 消息)
        """
        success1, msg1 = self.add_binary(node_exe_path, '.')
        success2 = True
        msg2 = ""

        if node_modules_path:
            success2, msg2 = self.add_directory(node_modules_path, "node_modules")

        if success1 and success2:
            return True, f"成功添加Node.js环境: {node_exe_path} 和 node_modules"
        else:
            return False, f"添加Node.js环境失败: {msg1} {msg2}"

    def add_java_env(self, java_home: str) -> Tuple[bool, str]:
        """
        添加Java环境到打包资源中

        :param java_home: Java主目录路径
        :return: (是否成功, 消息)
        """
        return self.add_directory(java_home, "jre")

    def add_static_files(self, static_path: str, target: str = "static") -> Tuple[bool, str]:
        """
        添加静态文件目录到打包资源中

        适用于:
        - Web资源 (HTML, CSS, JS)
        - 图片、图标
        - 字体文件

        :param static_path: 静态文件目录路径
        :param target: 目标路径
        :return: (是否成功, 消息)
        """
        return self.add_directory(static_path, target)

    def add_windows_fonts(self, font_pattern: str = "C:/Windows/Fonts/segui*.ttf", target: str = "fonts") -> Tuple[
        bool, str]:
        """
        添加Windows字体文件（仅Windows平台）

        :param font_pattern: 字体文件匹配模式
        :param target: 目标路径
        :return: (是否成功, 消息)
        """
        if sys.platform != "win32":
            return False, "字体添加仅支持Windows平台"

        font_files = glob.glob(font_pattern)
        if not font_files:
            return False, f"未找到匹配的字体文件: {font_pattern}"

        for font_file in font_files:
            self.datas.append((font_file, target))

        return True, f"成功添加 {len(font_files)} 个Windows字体文件"

    def set_console(self, show_console: bool) -> None:
        """
        设置是否显示控制台窗口

        :param show_console: 是否显示控制台
        """
        self.console = show_console

    def generate_spec(self, spec_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        生成spec文件

        :param spec_path: spec文件保存路径（可选）
        :return: (是否成功, 生成的spec文件路径或错误消息)
        """
        try:
            if not spec_path:
                spec_path = self.project_root / f"{self.output_name}.spec"
            else:
                spec_path = Path(spec_path)

            spec_content = self._build_spec_content(spec_path)

            # 确保目录存在
            spec_path.parent.mkdir(parents=True, exist_ok=True)

            with open(spec_path, 'w', encoding='utf-8') as f:
                f.write(spec_content)

            return True, str(spec_path)
        except Exception as e:
            return False, f"生成spec文件失败: {str(e)}"

    def _resolve_path(self, path: str) -> Path:
        """解析路径为绝对路径"""
        path_obj = Path(path)
        if not path_obj.is_absolute():
            path_obj = self.project_root / path_obj
        return path_obj.resolve()

    def _build_spec_content(self, spec_path: Path) -> str:
        """构建spec文件内容"""
        # 构建pathex
        pathex = [str(self.project_root)] + self.additional_pathex

        # 构建Analysis参数
        analysis_lines = [
            f"    [{str(self.main_script)!r}],",
            f"    pathex={pathex},",
            f"    binaries={self.binaries},",
            f"    datas={self.datas},",
            f"    hiddenimports={self.hiddenimports},",
            f"    hookspath={self.hookspath},",
            "    hooksconfig={},",
            f"    runtime_hooks={self.runtime_hooks},",
            f"    excludes={self.excludes},",
            f"    win_no_prefer_redirects={self.win_no_prefer_redirects},",
            f"    win_private_assemblies={self.win_private_assemblies},",
            "    cipher=None,",
            "    noarchive=False"
        ]
        analysis_str = ",\n".join(analysis_lines)

        # 构建EXE参数
        exe_lines = [
            "    pyz,",
            "    a.scripts,",
            "    a.binaries,",
            "    a.zipfiles,",
            "    a.datas,",
            f"    name={self.output_name!r},",
            "    debug=False,",
            "    bootloader_ignore_signals=False,",
            "    strip=False,",
            f"    upx={self.upx},",
            f"    upx_exclude={self.upx_exclude},",
            "    runtime_tmpdir=None,",
            f"    console={self.console},",
            "    disable_windowed_traceback=False,",
            "    argv_emulation=False,",
            "    target_arch=None,",
            "    codesign_identity=None,",
            "    entitlements_file=None"
        ]
        exe_str = ",\n".join(exe_lines)

        # 组合完整spec内容
        return f"""# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

# ========================================================
# 自动生成的 PyInstaller spec 文件
# 由 PyInstallerSpecBuilder 生成
# 生成时间: {time.strftime("%Y-%m-%d %H:%M:%S")}
# ========================================================

# 项目根目录
PROJECT_ROOT = Path(r"{self.project_root}").resolve()

# 分析主脚本
a = Analysis(
{analysis_str}
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 创建可执行文件
exe = EXE(
{exe_str}
)

# ========================================================
# 打包说明:
# 1. 运行命令: pyinstaller {spec_path.name}
# 2. 输出目录: dist/{self.output_name}
# 3. 控制台: {'显示' if self.console else '隐藏'}
# 4. 包含资源:
#    - 数据文件: {len(self.datas)} 项
#    - 二进制文件: {len(self.binaries)} 项
#    - 隐藏模块: {len(self.hiddenimports)} 个
# ========================================================
"""


# def create_example_spec() -> Tuple[bool, str]:
#     """
#     创建示例 spec 文件
#     """
#     try:
#         # 创建构建器实例
#         builder = PyInstallerSpecBuilder(
#             main_script="./test1.py",
#             output_name="app",
#             console=False
#         )
#
#         # 添加核心目录 (Python 模块)
#         builder.add_directory("core", "core")
#
#
#         # 添加Node.js环境
#         xhs_crawler_path = "core/Crawler/xhs_crawler"
#         builder.add_node_env(
#             os.path.join(xhs_crawler_path, "node.exe"),
#             os.path.join(xhs_crawler_path, "node_modules")
#         )
#
#         # 添加静态文件目录
#         builder.add_static_files(
#             os.path.join(xhs_crawler_path, "static"),
#             "/xhs_crawler/static"
#         )
#
#         # 添加二进制文件 (.exe)
#         builder.add_binary("test.exe", '.')
#
#         # 添加Windows字体
#         if sys.platform == "win32":
#             builder.add_windows_fonts()
#
#         # 添加额外Python模块
#         builder.add_module("psutil")
#         builder.add_module("win32api")
#         builder.add_module("win32con")
#         builder.add_module("PyQt6.QtWidgets")
#
#         # 生成spec文件
#         return builder.generate_spec("app.spec")
#     except Exception as e:
#         return False, f"创建示例失败: {str(e)}"
#
#
# if __name__ == "__main__":
#     # 示例使用
#     success, result = create_example_spec()
#     if success:
#         print(f"Spec文件生成成功: {result}")
#     else:
#         print(f"错误: {result}")