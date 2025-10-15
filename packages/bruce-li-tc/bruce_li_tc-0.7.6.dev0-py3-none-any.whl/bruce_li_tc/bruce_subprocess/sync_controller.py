import subprocess
import sys
import threading
from typing import List, Optional, Tuple, Union, Callable


class SubprocessController:
    """
    高级subprocess控制器，支持：
    - 多线程安全执行
    - 窗口隐藏（Windows）
    - 自动资源释放
    - 编码处理
    - 实时输出捕获
    """

    def __init__(self, encoding: str = 'utf-8', hide_window: bool = True):
        """
        :param encoding: 子进程输入/输出流的编码
        :param hide_window: 是否隐藏控制台窗口（仅Windows有效）
        """
        self.encoding = encoding
        self.hide_window = hide_window
        self._lock = threading.Lock()  # 多线程安全锁

        # Windows隐藏窗口配置
        self._startupinfo = None
        if hide_window and sys.platform == 'win32':
            self._startupinfo = subprocess.STARTUPINFO()
            self._startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self._startupinfo.wShowWindow = subprocess.SW_HIDE

    def run_command(
            self,
            cmd: Union[str, List[str]],
            timeout: Optional[float] = None,
            input_data: Optional[str] = None,
            output_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[int, str, str]:
        """
        执行命令并返回结果（线程安全）

        :param cmd: 命令字符串或参数列表
        :param timeout: 超时时间（秒）
        :param input_data: 输入到stdin的数据
        :param output_callback: 实时输出回调函数
        :return: (返回码, stdout输出, stderr输出)
        """
        # 确保在多线程环境下的安全执行
        with self._lock:
            try:
                with subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE if input_data else None,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,  # 启用文本模式自动解码
                        encoding=self.encoding,
                        startupinfo=self._startupinfo,
                        bufsize=1,  # 行缓冲，用于实时输出
                        errors='replace'  # 编码错误处理策略
                ) as proc:
                    stdout_lines = []
                    stderr_lines = []

                    # 实时输出处理
                    def process_stream(stream, lines, is_stdout=True):
                        for line in stream:
                            decoded_line = line
                            lines.append(decoded_line)
                            if output_callback:
                                output_callback(decoded_line)

                    # 启动输出处理线程
                    stdout_thread = threading.Thread(
                        target=process_stream,
                        args=(proc.stdout, stdout_lines),
                        daemon=True
                    )
                    stderr_thread = threading.Thread(
                        target=process_stream,
                        args=(proc.stderr, stderr_lines, False),
                        daemon=True
                    )
                    stdout_thread.start()
                    stderr_thread.start()

                    # 输入处理
                    if input_data:
                        proc.stdin.write(input_data)
                        proc.stdin.flush()
                        proc.stdin.close()

                    # 等待进程结束
                    try:
                        proc.wait(timeout=timeout)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        stdout_thread.join(timeout=1.0)
                        stderr_thread.join(timeout=1.0)
                        raise TimeoutError(f"命令执行超时: {timeout}秒")

                    # 等待输出线程完成
                    stdout_thread.join(timeout=2.0)
                    stderr_thread.join(timeout=2.0)

                    stdout_str = ''.join(stdout_lines)
                    stderr_str = ''.join(stderr_lines)

                    return proc.returncode, stdout_str, stderr_str

            except Exception as e:
                raise RuntimeError(f"子进程执行失败: {str(e)}")

    @staticmethod
    def get_system_encoding() -> str:
        """
        获取系统推荐编码（用于subprocess）
        """
        if sys.platform == 'win32':
            return 'gbk'  # Windows中文系统常用编码
        return 'utf-8'  # Linux/macOS推荐编码


# # 使用示例
# if __name__ == "__main__":
#     # 创建控制器实例（自动选择系统编码）
#     controller = SubprocessController(
#         encoding=SubprocessController.get_system_encoding(),
#         hide_window=True
#     )
#
#
#     # 实时输出回调函数
#     def realtime_output(line: str):
#         print(f"[实时输出] {line.strip()}")
#
#
#     # 在多个线程中执行命令
#     def thread_task(cmd: str):
#         try:
#             returncode, stdout, stderr = controller.run_command(
#                 cmd=cmd,
#                 output_callback=realtime_output
#             )
#             print(f"命令 '{cmd}' 执行完成, 返回码: {returncode}")
#         except Exception as e:
#             print(f"命令 '{cmd}' 执行失败: {str(e)}")
#
#
#     # 创建多个线程执行不同命令
#     commands = [
#         ["python", "-c", "import time; print('任务1开始'); time.sleep(2); print('任务1结束')"],
#         ["python", "-c", "print('任务2输出'); import sys; sys.stderr.write('任务2错误')"],
#         ["python", "-c", "print('中文测试')"]  # 测试中文输出
#     ]
#
#     threads = []
#     for cmd in commands:
#         t = threading.Thread(target=thread_task, args=(cmd,))
#         t.start()
#         threads.append(t)
#
#     # 等待所有线程完成
#     for t in threads:
#         t.join()