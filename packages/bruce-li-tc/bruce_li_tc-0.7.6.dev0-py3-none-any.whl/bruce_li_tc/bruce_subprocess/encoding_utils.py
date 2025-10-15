# 专注于subprocess编码处理的工具
import sys


class SubprocessEncoding:
    """ subprocess专用编码处理 """

    @staticmethod
    def get_system_default() -> str:
        """ 获取系统推荐编码 """
        if sys.platform == 'win32':
            return 'gbk'
        return 'utf-8'

    @staticmethod
    def detect_output_encoding(output: bytes) -> str:
        """ 自动检测子进程输出编码（简化版） """
        try:
            output.decode('utf-8')
            return 'utf-8'
        except UnicodeDecodeError:
            pass

        try:
            output.decode('gbk')
            return 'gbk'
        except UnicodeDecodeError:
            pass

        return SubprocessEncoding.get_system_default()