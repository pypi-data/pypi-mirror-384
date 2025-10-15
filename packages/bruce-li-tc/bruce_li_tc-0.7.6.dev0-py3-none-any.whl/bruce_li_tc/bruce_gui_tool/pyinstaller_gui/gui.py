import os
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QFileDialog, QCheckBox, QMessageBox,
    QGroupBox, QProgressBar, QRadioButton, QButtonGroup, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont

from .core import Packager
from .worker import VersionCheckThread, BuildThread
from .utils import format_path, get_default_icon, create_config


class PyInstallerGUI(QMainWindow):
    """PyInstaller打包工具的主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyInstaller 打包工具")
        self.setGeometry(100, 100, 900, 700)
        self.setWindowIcon(QIcon(get_default_icon()))
        self.setup_ui()
        self.setup_connections()

        # 初始化变量
        self.venv_path = ""
        self.project_dir = ""
        self.base_name = "app"
        self.config = {}

        self.log_message("请选择虚拟环境目录开始")

    def setup_ui(self):
        """设置UI界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 环境设置组
        env_group = QGroupBox("环境设置")
        self.setup_env_group(env_group)
        main_layout.addWidget(env_group)

        # 打包选项组
        options_group = QGroupBox("打包选项")
        self.setup_options_group(options_group)
        main_layout.addWidget(options_group)

        # 高级设置组
        self.advanced_group = QGroupBox("高级设置")
        self.setup_advanced_group(self.advanced_group)
        self.advanced_group.setVisible(False)
        main_layout.addWidget(self.advanced_group)

        # 高级设置按钮
        self.advanced_btn = QPushButton("显示高级设置")
        self.advanced_btn.setStyleSheet("background-color: #8e44ad;")
        main_layout.addWidget(self.advanced_btn, alignment=Qt.AlignmentFlag.AlignRight)

        # 日志输出
        log_group = QGroupBox("打包日志")
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.build_btn = QPushButton("开始打包")
        self.build_btn.setStyleSheet("background-color: #27ae60;")
        btn_layout.addWidget(self.build_btn)

        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.setStyleSheet("background-color: #e67e22;")
        btn_layout.addWidget(self.clear_log_btn)

        self.exit_btn = QPushButton("退出")
        self.exit_btn.setStyleSheet("background-color: #e74c3c;")
        btn_layout.addWidget(self.exit_btn)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # 状态栏
        self.statusBar().showMessage("就绪")

    def setup_env_group(self, group):
        """设置环境组UI"""
        layout = QGridLayout(group)
        layout.setVerticalSpacing(10)
        layout.setHorizontalSpacing(15)

        # 虚拟环境路径
        layout.addWidget(QLabel("虚拟环境路径:"), 0, 0)
        venv_layout = QHBoxLayout()
        self.venv_edit = QLineEdit()
        self.venv_edit.setPlaceholderText("请选择虚拟环境目录")
        venv_layout.addWidget(self.venv_edit)
        self.browse_venv_btn = QPushButton("浏览...")
        venv_layout.addWidget(self.browse_venv_btn)
        layout.addLayout(venv_layout, 0, 1)

        # 版本信息
        layout.addWidget(QLabel("Python 版本:"), 1, 0)
        self.py_version_label = QLabel("未知")
        layout.addWidget(self.py_version_label, 1, 1)

        layout.addWidget(QLabel("PyInstaller 版本:"), 2, 0)
        self.pi_version_label = QLabel("未知")
        layout.addWidget(self.pi_version_label, 2, 1)

        layout.addWidget(QLabel("最新 PyInstaller:"), 3, 0)
        self.latest_pi_label = QLabel("正在检查...")
        layout.addWidget(self.latest_pi_label, 3, 1)

        # 升级按钮
        self.update_pi_btn = QPushButton("升级 PyInstaller")
        layout.addWidget(self.update_pi_btn, 4, 1)

    def setup_options_group(self, group):
        """设置选项组UI"""
        layout = QGridLayout(group)
        layout.setVerticalSpacing(10)
        layout.setHorizontalSpacing(15)

        # 入口文件
        layout.addWidget(QLabel("入口文件:"), 0, 0)
        entry_layout = QHBoxLayout()
        self.entry_path_edit = QLineEdit()
        self.entry_path_edit.setPlaceholderText("请选择入口文件")
        entry_layout.addWidget(self.entry_path_edit)
        self.browse_entry_btn = QPushButton("浏览...")
        entry_layout.addWidget(self.browse_entry_btn)
        layout.addLayout(entry_layout, 0, 1)

        # 基础名称
        layout.addWidget(QLabel("基础名称:"), 1, 0)
        self.base_name_edit = QLineEdit("app")
        self.base_name_edit.setPlaceholderText("用于生成输出文件名")
        layout.addWidget(self.base_name_edit, 1, 1)

        # 版本选择
        layout.addWidget(QLabel("版本选择:"), 2, 0)
        version_layout = QHBoxLayout()
        self.auto_version_radio = QRadioButton("自动版本")
        self.auto_version_radio.setChecked(True)
        self.manual_version_radio = QRadioButton("手动版本")
        version_layout.addWidget(self.auto_version_radio)
        version_layout.addWidget(self.manual_version_radio)
        layout.addLayout(version_layout, 2, 1)

        # 输出文件
        layout.addWidget(QLabel("输出文件:"), 3, 0)
        output_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("输出文件路径")
        output_layout.addWidget(self.output_path_edit)
        self.browse_output_btn = QPushButton("浏览...")
        output_layout.addWidget(self.browse_output_btn)
        layout.addLayout(output_layout, 3, 1)

        # 图标文件
        layout.addWidget(QLabel("图标文件:"), 4, 0)
        icon_layout = QHBoxLayout()
        self.icon_file_edit = QLineEdit()
        self.icon_file_edit.setPlaceholderText("例如: icon.ico")
        icon_layout.addWidget(self.icon_file_edit)
        self.browse_icon_btn = QPushButton("浏览...")
        icon_layout.addWidget(self.browse_icon_btn)
        self.validate_icon_btn = QPushButton("验证")
        icon_layout.addWidget(self.validate_icon_btn)
        layout.addLayout(icon_layout, 4, 1)

        # 打包选项
        layout.addWidget(QLabel("打包选项:"), 5, 0)
        options_layout = QVBoxLayout()
        self.onefile_check = QCheckBox("打包为单个文件 (--onefile)")
        self.onefile_check.setChecked(True)
        options_layout.addWidget(self.onefile_check)
        self.noconsole_check = QCheckBox("无控制台窗口 (--noconsole)")
        options_layout.addWidget(self.noconsole_check)
        self.clean_check = QCheckBox("清理构建 (--clean)")
        self.clean_check.setChecked(True)
        options_layout.addWidget(self.clean_check)
        layout.addLayout(options_layout, 5, 1)

    def setup_advanced_group(self, group):
        """设置高级组UI"""
        layout = QGridLayout(group)
        layout.setVerticalSpacing(10)
        layout.setHorizontalSpacing(15)

        # 附加数据
        layout.addWidget(QLabel("附加数据:"), 0, 0)
        self.data_edit = QLineEdit()
        self.data_edit.setPlaceholderText("格式: src;dest 或 static;static")
        layout.addWidget(self.data_edit, 0, 1)

        # 隐藏导入
        layout.addWidget(QLabel("隐藏导入:"), 1, 0)
        self.hidden_edit = QLineEdit()
        self.hidden_edit.setPlaceholderText("格式: module1,module2")
        layout.addWidget(self.hidden_edit, 1, 1)

        # 排除模块
        layout.addWidget(QLabel("排除模块:"), 2, 0)
        self.exclude_edit = QLineEdit()
        self.exclude_edit.setPlaceholderText("格式: module1,module2")
        layout.addWidget(self.exclude_edit, 2, 1)

    def setup_connections(self):
        """设置信号连接"""
        self.browse_venv_btn.clicked.connect(self.browse_venv)
        self.browse_entry_btn.clicked.connect(self.browse_entry_file)
        self.browse_output_btn.clicked.connect(self.browse_output_file)
        self.browse_icon_btn.clicked.connect(self.browse_icon_file)
        self.validate_icon_btn.clicked.connect(self.validate_icon)
        self.update_pi_btn.clicked.connect(self.update_pyinstaller)
        self.advanced_btn.clicked.connect(self.toggle_advanced)
        self.build_btn.clicked.connect(self.start_build)
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.exit_btn.clicked.connect(self.close)
        self.base_name_edit.textChanged.connect(self.update_base_name)
        self.auto_version_radio.toggled.connect(self.generate_output_filename)

    def log_message(self, message):
        """记录消息到日志"""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()

    def browse_venv(self):
        """浏览虚拟环境目录"""
        path = QFileDialog.getExistingDirectory(self, "选择虚拟环境目录")
        if path:
            self.venv_path = path
            self.venv_edit.setText(format_path(path))
            self.project_dir = os.path.dirname(path)

            # 设置默认入口文件
            self.entry_file_path = os.path.join(self.project_dir, "main.py")
            self.entry_path_edit.setText(format_path(self.entry_file_path))

            # 更新配置
            self.config = create_config(
                venv_path=path,
                entry_file=self.entry_file_path,
                output_name="",
                project_dir=self.project_dir
            )

            # 显示版本信息
            self.py_version_label.setText(self.get_python_version())
            self.pi_version_label.setText(self.get_pyinstaller_version())

            # 检查最新版本
            self.check_latest_version()

            # 生成输出文件名
            self.generate_output_filename()

    def get_python_version(self):
        """获取Python版本"""
        packager = Packager(self.config)
        return packager.get_python_version()

    def get_pyinstaller_version(self):
        """获取PyInstaller版本"""
        packager = Packager(self.config)
        return packager.get_pyinstaller_version()

    def check_latest_version(self):
        """检查最新版本"""
        self.latest_pi_label.setText("正在检查...")
        self.thread = VersionCheckThread(self.config)
        self.thread.finished.connect(self.update_latest_version)
        self.thread.error.connect(self.handle_version_error)
        self.thread.start()

    def update_latest_version(self, version):
        """更新最新版本显示"""
        self.latest_pi_label.setText(version)
        self.log_message(f"最新 PyInstaller 版本: {version}")

    def handle_version_error(self, error):
        """处理版本检查错误"""
        self.latest_pi_label.setText("未知")
        self.log_message(f"获取最新版本失败: {error}")

    def update_base_name(self, name):
        """更新基础名称"""
        self.base_name = name.strip() or "app"
        self.generate_output_filename()

    def browse_entry_file(self):
        """浏览入口文件"""
        if not self.project_dir:
            QMessageBox.warning(self, "错误", "请先选择虚拟环境目录")
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "选择入口文件", self.project_dir, "Python Files (*.py)"
        )
        if path:
            self.entry_file_path = path
            self.entry_path_edit.setText(format_path(path))

            # 更新基础名称
            if self.base_name in ["", "app"]:
                base = os.path.splitext(os.path.basename(path))[0]
                self.base_name_edit.setText(base)

            self.generate_output_filename()

    def browse_output_file(self):
        """浏览输出文件"""
        if not self.project_dir:
            QMessageBox.warning(self, "错误", "请先选择虚拟环境目录")
            return

        # 创建dist目录
        dist_dir = os.path.join(self.project_dir, "dist")
        os.makedirs(dist_dir, exist_ok=True)

        path, _ = QFileDialog.getSaveFileName(
            self, "选择输出文件", dist_dir, "Executable Files (*.exe)"
        )
        if path:
            if not path.lower().endswith('.exe'):
                path += '.exe'
            self.output_file_path = path
            self.output_path_edit.setText(format_path(path))

    def generate_output_filename(self):
        """生成输出文件名"""
        if not self.project_dir:
            return

        if self.auto_version_radio.isChecked():
            packager = Packager(self.config)
            next_version, new_base = packager.get_next_version(self.base_name)

            # 更新基础名称
            if new_base != self.base_name:
                self.base_name = new_base
                self.base_name_edit.setText(new_base)

            # 设置输出路径
            dist_dir = os.path.join(self.project_dir, "dist")
            self.output_file_path = os.path.join(dist_dir, next_version)
            self.output_path_edit.setText(format_path(self.output_file_path))

    def browse_icon_file(self):
        """浏览图标文件"""
        if not self.project_dir:
            QMessageBox.warning(self, "错误", "请先选择虚拟环境目录")
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "选择图标文件", self.project_dir, "Icon Files (*.ico)"
        )
        if path:
            self.icon_file_edit.setText(format_path(path))

    def validate_icon(self):
        """验证图标文件"""
        icon_path = self.icon_file_edit.text()
        packager = Packager(self.config)
        valid, msg = packager.validate_icon(icon_path)
        self.log_message(msg)
        return valid

    def update_pyinstaller(self):
        """升级PyInstaller"""
        packager = Packager(self.config)
        packager.update_pyinstaller()

        # 刷新版本显示
        self.pi_version_label.setText(self.get_pyinstaller_version())

    def toggle_advanced(self):
        """切换高级设置可见性"""
        visible = not self.advanced_group.isVisible()
        self.advanced_group.setVisible(visible)
        self.advanced_btn.setText("隐藏高级设置" if visible else "显示高级设置")

    def start_build(self):
        """开始打包"""
        # 准备配置
        config = {
            'venv_path': self.venv_path,
            'entry_file': self.entry_path_edit.text(),
            'output_name': os.path.splitext(os.path.basename(self.output_file_path))[0],
            'project_dir': self.project_dir,
            'onefile': self.onefile_check.isChecked(),
            'noconsole': self.noconsole_check.isChecked(),
            'clean': self.clean_check.isChecked(),
            'icon': self.icon_file_edit.text(),
            'data': self.data_edit.text().split(',') if self.data_edit.text() else [],
            'hidden_imports': self.hidden_edit.text().split(',') if self.hidden_edit.text() else [],
            'exclude_modules': self.exclude_edit.text().split(',') if self.exclude_edit.text() else []
        }

        # 验证输入
        if not config['venv_path']:
            QMessageBox.warning(self, "错误", "请选择虚拟环境目录")
            return
        if not config['entry_file'] or not os.path.exists(config['entry_file']):
            QMessageBox.warning(self, "错误", "入口文件不存在")
            return

        # 创建打包线程
        self.build_thread = BuildThread(config)
        self.build_thread.log_signal.connect(self.log_message)
        self.build_thread.progress_signal.connect(self.update_progress)
        self.build_thread.finished_signal.connect(self.build_finished)

        # 更新UI状态
        self.build_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 启动线程
        self.build_thread.start()

    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)

    def build_finished(self, success):
        """打包完成处理"""
        self.build_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            QMessageBox.information(self, "成功", "打包完成！")
            # 生成新版本号
            self.generate_output_filename()
        else:
            QMessageBox.warning(self, "错误", "打包过程中出错，请查看日志")


def run():
    """启动PyInstaller GUI应用"""
    app = QApplication(sys.argv)
    window = PyInstallerGUI()
    window.show()
    sys.exit(app.exec())


