import asyncio
from typing import List, Tuple, Optional


class AsyncSubprocessController:
    """ 异步subprocess控制器 """

    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding

    async def run_command(
            self,
            cmd: List[str],
            timeout: Optional[float] = None
    ) -> Tuple[int, str, str]:
        """
        异步执行命令

        :param cmd: 命令参数列表
        :param timeout: 超时时间（秒）
        :return: (返回码, stdout, stderr)
        """
        # 创建异步子进程
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # 读取输出（支持超时）
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise TimeoutError(f"命令执行超时: {timeout}秒")

        # 解码输出
        stdout_str = stdout.decode(self.encoding, errors='replace')
        stderr_str = stderr.decode(self.encoding, errors='replace')

        return process.returncode, stdout_str, stderr_str


# 使用示例
# async def main():
#     controller = AsyncSubprocessController(encoding='utf-8')
#
#     # 同时执行多个命令
#     tasks = [
#         controller.run_command(["python", "-c", "print('任务1')"]),
#         controller.run_command(["python", "-c", "print('任务2')"]),
#         controller.run_command(["python", "-c", "print('中文测试')"])
#     ]
#
#     results = await asyncio.gather(*tasks, return_exceptions=True)
#
#     for i, result in enumerate(results):
#         if isinstance(result, Exception):
#             print(f"任务 {i + 1} 失败: {str(result)}")
#         else:
#             returncode, stdout, stderr = result
#             print(f"任务 {i + 1} 完成, 返回码: {returncode}")
#             print(f"输出: {stdout.strip()}")
#
#
# if __name__ == "__main__":
#     asyncio.run(main())