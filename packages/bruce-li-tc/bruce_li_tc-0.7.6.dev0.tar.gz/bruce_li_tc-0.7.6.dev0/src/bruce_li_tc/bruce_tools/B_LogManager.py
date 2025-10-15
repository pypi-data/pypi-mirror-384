"""
B_LogManager.py - 高级日志管理工具
基于 loguru 库封装，支持多线程、日志分级、文件轮转和自定义格式化
"""

from loguru import logger
import sys
import os
import threading
import time
from datetime import datetime
from pathlib import Path


class LogManager:
    """
    高级日志管理类，封装 loguru 的常用功能
    支持多线程安全操作、日志分级、文件轮转和自定义格式化
    """

    def __init__(self, log_dir="logs", app_name="Application",
                 max_file_size="10 MB", retention="30 days",
                 log_level="DEBUG", enable_console=True):
        """
        初始化日志管理器

        参数:
            log_dir: 日志目录 (默认"logs")
            app_name: 应用名称 (默认"Application")
            max_file_size: 单个日志文件最大大小 (默认"10 MB")
            retention: 日志保留时间 (默认"30 days")
            log_level: 日志级别 (默认"DEBUG")
            enable_console: 是否启用控制台输出 (默认True)

        示例:
            # 创建日志管理器
            log_manager = LogManager(
                log_dir="app_logs",
                app_name="MyApp",
                max_file_size="20 MB",
                retention="7 days",
                log_level="INFO"
            )

            # 记录日志
            log_manager.info("应用程序启动")
        """
        # 确保日志目录存在
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 配置日志文件路径
        log_file = self.log_dir / f"{app_name}_{datetime.now().strftime('%Y%m%d')}.log"

        # 移除默认配置
        logger.remove()

        # 添加控制台日志
        if enable_console:
            logger.add(
                sys.stderr,
                level=log_level,
                format=self._get_console_format(),
                enqueue=True,  # 多线程安全
                backtrace=True,
                diagnose=True
            )

        # 添加文件日志
        logger.add(
            str(log_file),
            rotation=max_file_size,
            retention=retention,
            compression="zip",
            level=log_level,
            format=self._get_file_format(),
            enqueue=True,  # 多线程安全
            backtrace=True,
            diagnose=True
        )

        print(f"[LogManager] 日志系统初始化完成 | 目录: {log_dir} | 级别: {log_level}")

    def _get_console_format(self):
        """控制台日志格式"""
        return "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{thread.name: <15}</cyan> | <level>{message}</level>"

    def _get_file_format(self):
        """文件日志格式"""
        return "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {thread.name: <15} | {file}:{line} | {message}"

    def debug(self, message, **kwargs):
        """
        记录调试级别日志

        参数:
            message: 日志消息
            kwargs: 额外上下文信息

        示例:
            # 记录调试信息
            log_manager.debug("正在初始化数据库连接", db_host="localhost", db_port=3306)

            # 在函数内部记录
            def complex_calculation(a, b):
                log_manager.debug("开始复杂计算", a=a, b=b)
                # ... 计算逻辑 ...
                log_manager.debug("计算完成", result=result)
                return result
        """
        logger.debug(message, **kwargs)

    def info(self, message, **kwargs):
        """
        记录信息级别日志

        参数:
            message: 日志消息
            kwargs: 额外上下文信息

        示例:
            # 记录应用状态
            log_manager.info("用户登录成功", user_id=123, username="john_doe")

            # 记录处理进度
            for i in range(10):
                log_manager.info(f"处理进度: {i+1}/10", current=i+1, total=10)
                time.sleep(0.1)
        """
        logger.info(message, **kwargs)

    def warning(self, message, **kwargs):
        """
        记录警告级别日志

        参数:
            message: 日志消息
            kwargs: 额外上下文信息

        示例:
            # 记录警告
            log_manager.warning("磁盘空间不足", free_space="5GB", required="10GB")

            # 在配置检查中
            if not config.is_valid():
                log_manager.warning("配置验证失败", invalid_fields=config.get_invalid_fields())
        """
        logger.warning(message, **kwargs)

    def error(self, message, **kwargs):
        """
        记录错误级别日志

        参数:
            message: 日志消息
            kwargs: 额外上下文信息

        示例:
            # 记录错误
            try:
                # 可能失败的操作
                risky_operation()
            except Exception as e:
                log_manager.error("操作失败", error=str(e), operation="risky_operation")

            # 在API请求中
            def handle_request(request):
                try:
                    # 处理请求
                    return process(request)
                except RequestException as e:
                    log_manager.error("请求处理失败", request_id=request.id, error=str(e))
                    return error_response()
        """
        logger.error(message, **kwargs)

    def critical(self, message, **kwargs):
        """
        记录严重错误级别日志

        参数:
            message: 日志消息
            kwargs: 额外上下文信息

        示例:
            # 系统关键错误
            if critical_resource_not_available():
                log_manager.critical("关键资源不可用", resource="database", status="down")
                sys.exit(1)

            # 应用启动失败
            try:
                app.start()
            except FatalError as e:
                log_manager.critical("应用程序启动失败", error=str(e))
                raise
        """
        logger.critical(message, **kwargs)

    def exception(self, message, **kwargs):
        """
        记录异常信息（包括堆栈跟踪）

        参数:
            message: 日志消息
            kwargs: 额外上下文信息

        示例:
            # 捕获并记录异常
            try:
                # 可能抛出异常的操作
                unsafe_operation()
            except Exception as e:
                log_manager.exception("操作发生异常", operation="unsafe_operation")

            # 在任务处理中
            def process_task(task):
                try:
                    task.execute()
                except TaskException as e:
                    log_manager.exception("任务执行失败", task_id=task.id, task_type=task.type)
        """
        logger.exception(message, **kwargs)

    def log_performance(self, func):
        """
        性能日志装饰器

        参数:
            func: 被装饰的函数

        返回: 装饰后的函数

        示例:
            # 装饰函数以记录执行时间
            @log_manager.log_performance
            def complex_operation(data):
                # 复杂操作
                time.sleep(0.5)
                return processed_data

            # 使用
            result = complex_operation(large_dataset)
        """

        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            self.info(
                f"函数 {func.__name__} 执行完成",
                function=func.__name__,
                execution_time=f"{elapsed:.4f}秒",
                args=args,
                kwargs=kwargs
            )
            return result

        return wrapper

    def catch(self, reraise=False):
        """
        异常捕获装饰器

        参数:
            reraise: 是否重新抛出异常 (默认False)

        返回: 装饰器函数

        示例:
            # 使用装饰器捕获异常
            @log_manager.catch(reraise=True)
            def critical_process():
                # 可能失败的关键过程
                if not check_conditions():
                    raise RuntimeError("条件不满足")

            # 在任务调度中使用
            @log_manager.catch()
            def scheduled_task():
                # 定时任务逻辑
                ...
        """

        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.exception(
                        f"函数 {func.__name__} 执行失败",
                        function=func.__name__,
                        error=str(e),
                        args=args,
                        kwargs=kwargs
                    )
                    if reraise:
                        raise

            return wrapper

        return decorator

    def thread_safe_log(self, message, level="INFO", **kwargs):
        """
        线程安全的日志记录方法（显式指定日志级别）

        参数:
            message: 日志消息
            level: 日志级别 (默认"INFO")
            kwargs: 额外上下文信息

        示例:
            # 在多个线程中记录日志
            def worker(thread_id):
                log_manager.thread_safe_log(f"线程 {thread_id} 开始工作", level="DEBUG", thread_id=thread_id)
                # ... 工作逻辑 ...
                log_manager.thread_safe_log(f"线程 {thread_id} 工作完成", level="INFO", thread_id=thread_id)

            # 创建线程
            threads = []
            for i in range(5):
                t = threading.Thread(target=worker, args=(i,))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()
        """
        if level.upper() == "DEBUG":
            self.debug(message, **kwargs)
        elif level.upper() == "INFO":
            self.info(message, **kwargs)
        elif level.upper() == "WARNING":
            self.warning(message, **kwargs)
        elif level.upper() == "ERROR":
            self.error(message, **kwargs)
        elif level.upper() == "CRITICAL":
            self.critical(message, **kwargs)
        else:
            self.info(message, **kwargs)

    def add_file_sink(self, file_path, level="DEBUG", rotation="10 MB", retention="30 days",
                      format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}"):
        """
        添加额外的文件日志输出

        参数:
            file_path: 文件路径
            level: 日志级别 (默认"DEBUG")
            rotation: 文件轮转条件 (默认"10 MB")
            retention: 日志保留时间 (默认"30 days")
            format: 日志格式

        返回: 日志接收器ID

        示例:
            # 添加错误日志专用文件
            error_log_id = log_manager.add_file_sink(
                "logs/errors.log",
                level="ERROR",
                rotation="5 MB",
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {file}:{line} | {message}"
            )

            # 添加审计日志
            audit_log_id = log_manager.add_file_sink(
                "logs/audit.log",
                level="INFO",
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}"
            )
        """
        sink_id = logger.add(
            file_path,
            level=level,
            rotation=rotation,
            retention=retention,
            compression="zip",
            format=format,
            enqueue=True
        )
        print(f"[LogManager] 添加日志输出到: {file_path} | 级别: {level}")
        return sink_id

    def remove_sink(self, sink_id):
        """
        移除日志输出

        参数:
            sink_id: 日志接收器ID

        示例:
            # 移除之前添加的日志输出
            log_manager.remove_sink(error_log_id)
            print("错误日志输出已移除")
        """
        logger.remove(sink_id)
        print(f"[LogManager] 移除日志输出 (ID: {sink_id})")


# 示例使用
# if __name__ == "__main__":
#     # 创建日志管理器
#     log_manager = LogManager(
#         log_dir="example_logs",
#         app_name="DemoApp",
#         max_file_size="1 MB",
#         retention="1 days",
#         log_level="DEBUG"
#     )
#
#     # 1. 基本日志记录示例
#     log_manager.debug("这是一条调试信息", module="example", value=42)
#     log_manager.info("应用程序启动", version="1.0.0", pid=os.getpid())
#     log_manager.warning("磁盘空间低于阈值", free_space="15%", threshold="20%")
#
#     # 2. 错误和异常记录示例
#     try:
#         # 模拟一个错误
#         result = 10 / 0
#     except Exception as e:
#         log_manager.error("计算错误", operation="division", dividend=10, divisor=0)
#         log_manager.exception("发生除零异常")
#
#
#     # 3. 性能日志装饰器示例
#     @log_manager.log_performance
#     def process_data(data_size):
#         log_manager.info("开始处理数据", size=data_size)
#         time.sleep(0.2)  # 模拟数据处理
#         return f"processed_{data_size}"
#
#
#     result = process_data(1000)
#     log_manager.info("数据处理完成", result=result[:15])
#
#
#     # 4. 异常捕获装饰器示例
#     @log_manager.catch(reraise=False)
#     def risky_operation(value):
#         if value < 0:
#             raise ValueError("值不能为负数")
#         return value * 2
#
#
#     risky_operation(5)
#     risky_operation(-3)  # 会记录错误但不会中断程序
#
#
#     # 5. 多线程日志记录示例
#     def worker_thread(thread_id):
#         log_manager.thread_safe_log(f"线程 {thread_id} 开始", level="DEBUG", thread_id=thread_id)
#         time.sleep(0.1)
#         log_manager.thread_safe_log(f"线程 {thread_id} 处理中", level="INFO", thread_id=thread_id)
#         try:
#             if thread_id % 2 == 0:
#                 raise RuntimeError(f"线程 {thread_id} 模拟错误")
#         except Exception as e:
#             log_manager.thread_safe_log(f"线程 {thread_id} 发生错误", level="ERROR", error=str(e))
#         log_manager.thread_safe_log(f"线程 {thread_id} 结束", level="DEBUG", thread_id=thread_id)
#
#
#     log_manager.info("启动多线程测试")
#     threads = []
#     for i in range(3):
#         t = threading.Thread(target=worker_thread, args=(i,), name=f"Worker-{i}")
#         threads.append(t)
#         t.start()
#
#     for t in threads:
#         t.join()
#
#     log_manager.info("多线程测试完成")
#
#     # 6. 添加和移除日志输出示例
#     error_log_id = log_manager.add_file_sink(
#         "example_logs/errors.log",
#         level="ERROR",
#         rotation="500 KB",
#         format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {file}:{line} | {message}"
#     )
#
#     log_manager.error("这是一个测试错误", purpose="测试错误日志输出")
#     log_manager.remove_sink(error_log_id)
#
#     log_manager.info("所有示例执行完成")
#     print("请查看 example_logs 目录中的日志文件")