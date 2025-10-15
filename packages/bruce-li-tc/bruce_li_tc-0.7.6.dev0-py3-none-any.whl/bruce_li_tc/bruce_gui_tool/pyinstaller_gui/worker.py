from PyQt6.QtCore import QThread, pyqtSignal
from .core import Packager


class VersionCheckThread(QThread):
    """检查PyInstaller最新版本的线程"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        try:
            packager = Packager(self.config)
            version = packager.get_latest_pyinstaller_version()
            self.finished.emit(version)
        except Exception as e:
            self.error.emit(f"检查版本失败: {str(e)}")


class BuildThread(QThread):
    """执行打包的线程"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)

    def __init__(self, config):
        super().__init__()
        self.config = config
        # 添加回调
        config['log_callback'] = self.log_signal.emit
        config['progress_callback'] = self.progress_signal.emit

    def run(self):
        packager = Packager(self.config)
        success = packager.build()
        self.finished_signal.emit(success)