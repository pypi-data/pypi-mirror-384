# 文件名: b_service_tool.py
import sys
import os
import winreg
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QLabel, QLineEdit, QPushButton, QFileDialog,
                             QMessageBox, QGroupBox, QHBoxLayout, QCheckBox)
from PyQt6.QtCore import Qt
from bruce_autostart import B_ServiceManager  # 我们之前写的服务管理器


class ServiceToolApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("后台服务管理工具")
        self.setGeometry(100, 100, 600, 400)

        self.manager = B_ServiceManager()
        self.service_name = "BruceBackgroundService"

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout()

        # 服务配置区域
        config_group = QGroupBox("服务配置")
        config_layout = QVBoxLayout()

        # 服务名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("服务名称:"))
        self.name_edit = QLineEdit(self.service_name)
        name_layout.addWidget(self.name_edit)
        config_layout.addLayout(name_layout)

        # 文件路径选择
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("程序路径:"))
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择可执行文件或Python脚本")
        path_layout.addWidget(self.path_edit)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_file)
        path_layout.addWidget(browse_btn)
        config_layout.addLayout(path_layout)

        # 所有用户选项
        self.all_users_check = QCheckBox("为所有用户安装")
        config_layout.addWidget(self.all_users_check)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # 操作按钮区域
        btn_layout = QHBoxLayout()
        self.install_btn = QPushButton("安装并启动服务")
        self.install_btn.clicked.connect(self.install_service)
        self.install_btn.setStyleSheet("background-color: #4CAF50; color: white;")

        self.stop_btn = QPushButton("停止服务")
        self.stop_btn.clicked.connect(self.stop_service)
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white;")

        self.uninstall_btn = QPushButton("卸载服务")
        self.uninstall_btn.clicked.connect(self.uninstall_service)

        btn_layout.addWidget(self.install_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.uninstall_btn)
        layout.addLayout(btn_layout)

        # 状态显示区域
        status_group = QGroupBox("服务状态")
        status_layout = QVBoxLayout()

        self.status_label = QLabel("状态: 未检测")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.details_label = QLabel("请先选择程序路径")
        self.details_label.setWordWrap(True)

        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.details_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # 初始状态检查
        self.check_service_status()

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择程序", "", "可执行文件 (*.exe);;Python脚本 (*.py);;所有文件 (*.*)"
        )
        if file_path:
            self.path_edit.setText(file_path)
            self.check_service_status()

    def check_service_status(self):
        service_name = self.name_edit.text().strip() or self.service_name

        if self.manager.is_installed(service_name):
            if self.manager.is_running(service_name):
                self.status_label.setText("状态: 运行中")
                self.status_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
                self.details_label.setText(f"服务 '{service_name}' 正在后台运行")
            else:
                self.status_label.setText("状态: 已安装但未运行")
                self.status_label.setStyleSheet("color: orange; font-weight: bold; font-size: 14px;")
                self.details_label.setText(f"服务 '{service_name}' 已安装但未启动")
        else:
            self.status_label.setText("状态: 未安装")
            self.status_label.setStyleSheet("color: gray; font-weight: bold; font-size: 14px;")
            self.details_label.setText("服务未安装，请选择程序路径并安装服务")

    def install_service(self):
        service_name = self.name_edit.text().strip() or self.service_name
        file_path = self.path_edit.text().strip()

        if not file_path:
            QMessageBox.warning(self, "路径错误", "请先选择程序路径")
            return

        if not os.path.exists(file_path):
            QMessageBox.critical(self, "文件不存在", f"文件不存在: {file_path}")
            return

        try:
            # 安装并启动服务
            display_name = f"{service_name} (开机自启动)"
            if self.manager.install_start(service_name, file_path, display_name):
                QMessageBox.information(self, "成功", "服务安装并启动成功！\n程序将在系统启动时自动运行。")
            else:
                QMessageBox.warning(self, "失败", "服务安装启动失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生错误: {str(e)}")

        self.check_service_status()

    def stop_service(self):
        service_name = self.name_edit.text().strip() or self.service_name

        if not self.manager.is_installed(service_name):
            QMessageBox.warning(self, "未安装", "服务未安装，无法停止")
            return

        if self.manager.stop(service_name):
            QMessageBox.information(self, "成功", "服务已停止")
        else:
            QMessageBox.warning(self, "失败", "停止服务失败")

        self.check_service_status()

    def uninstall_service(self):
        service_name = self.name_edit.text().strip() or self.service_name

        if not self.manager.is_installed(service_name):
            QMessageBox.warning(self, "未安装", "服务未安装，无需卸载")
            return

        reply = QMessageBox.question(
            self, "确认卸载",
            f"确定要完全卸载服务 '{service_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.manager.uninstall(service_name):
                QMessageBox.information(self, "成功", "服务已卸载")
            else:
                QMessageBox.warning(self, "失败", "卸载服务失败")

        self.check_service_status()


# if __name__ == "__main__":
#     # 请求管理员权限
#     if sys.platform == "win32":
#         import ctypes
#
#         if not ctypes.windll.shell32.IsUserAnAdmin():
#             ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
#             sys.exit(0)
#
#     app = QApplication(sys.argv)
#     window = ServiceToolApp()
#     window.show()
#     sys.exit(app.exec())