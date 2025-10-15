"""
B_ThreadTool.py - Python threading 库高级封装工具
提供线程创建、同步原语、线程池等常用功能
"""

import threading
import time
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed


class ThreadTool:
    """
    线程工具类，封装常用 threading 功能
    示例代码直接嵌入在 create_thread() 方法中
    """

    def __init__(self):
        """
        初始化线程工具
        """
        self.threads = {}  # 存储管理的线程 {name: thread}
        self.sync_objects = {}  # 存储同步对象 {type: {name: object}}
        self.sync_objects['lock'] = {}
        self.sync_objects['rlock'] = {}
        self.sync_objects['condition'] = {}
        self.sync_objects['semaphore'] = {}
        self.sync_objects['queue'] = {}
        self.event = threading.Event()  # 全局事件

    def create_thread(self, target, name=None, args=(), kwargs={}, daemon=False):
        """
        创建并启动一个新线程，包含使用示例

        功能: 创建并启动一个新线程，自动管理线程资源
        参数:
            target: 线程目标函数 (callable)
            name: 线程名称 (str, 可选)
            args: 目标函数位置参数 (tuple, 默认())
            kwargs: 目标函数关键字参数 (dict, 默认{})
            daemon: 是否设置为守护线程 (bool, 默认False)
        返回: 创建的线程对象 (threading.Thread)

        示例:
            # 创建线程工具实例
            tool = ThreadTool()

            # 定义线程函数
            def worker(thread_id, sleep_time):
                print(f"线程 {thread_id} 开始, 将休眠 {sleep_time} 秒")
                time.sleep(sleep_time)
                print(f"线程 {thread_id} 结束")
                return f"线程 {thread_id} 结果"

            # 创建并启动线程
            thread = tool.create_thread(
                target=worker,
                name="示例线程",
                args=(1, 2),
                daemon=False
            )

            # 等待线程结束
            tool.join_threads()
        """
        thread_name = name or f"Thread-{threading.get_ident()}-{time.time()}"
        thread = threading.Thread(
            target=target,
            name=thread_name,
            args=args,
            kwargs=kwargs,
            daemon=daemon
        )
        self.threads[thread_name] = thread
        thread.start()
        print(f"[ThreadTool] 创建并启动线程: {thread_name}")
        return thread

    def join_threads(self, names=None, timeout=None):
        """
        等待线程结束

        功能: 等待指定线程或所有线程结束
        参数:
            names: 要等待的线程名称列表 (list, None表示所有线程)
            timeout: 超时时间(秒) (float, 默认None)
        返回: 未结束的线程列表 (list)
        """
        threads_to_join = []
        if names is None:
            threads_to_join = list(self.threads.values())
        else:
            threads_to_join = [self.threads[name] for name in names if name in self.threads]

        end_time = time.time() + timeout if timeout else None
        remaining = []

        for thread in threads_to_join:
            try:
                remaining_time = end_time - time.time() if end_time else None
                if remaining_time and remaining_time <= 0:
                    remaining.append(thread)
                    continue

                thread.join(remaining_time)
                if thread.is_alive():
                    remaining.append(thread)
                    print(f"[ThreadTool] 警告: 线程 {thread.name} 超时未结束")
                else:
                    print(f"[ThreadTool] 线程 {thread.name} 已结束")
                    # 从管理列表中移除已结束的线程
                    if thread.name in self.threads:
                        del self.threads[thread.name]
            except RuntimeError as e:
                print(f"[ThreadTool] 错误: 等待线程 {thread.name} 时出错: {str(e)}")

        return remaining

    def get_thread_count(self):
        """
        获取当前管理的线程数量

        返回: 线程数量 (int)
        """
        return len(self.threads)

    def get_active_threads(self):
        """
        获取所有活动的线程

        返回: 活动线程列表 (list)
        """
        return [t for t in self.threads.values() if t.is_alive()]

    def create_lock(self, name):
        """
        创建一个命名的锁

        参数:
            name: 锁的名称 (str)
        返回: Lock 对象
        """
        return self._create_sync_object('lock', name, threading.Lock)

    def create_rlock(self, name):
        """
        创建一个命名的可重入锁

        参数:
            name: 锁的名称 (str)
        返回: RLock 对象
        """
        return self._create_sync_object('rlock', name, threading.RLock)

    def create_condition(self, name, lock=None):
        """
        创建一个命名的条件变量

        参数:
            name: 条件变量名称 (str)
            lock: 关联的锁对象 (Lock/RLock, 默认None)
        返回: Condition 对象
        """

        def condition_creator():
            return threading.Condition(lock=lock)

        return self._create_sync_object('condition', name, condition_creator)

    def create_semaphore(self, name, value=1):
        """
        创建一个命名的信号量

        参数:
            name: 信号量名称 (str)
            value: 信号量初始值 (int, 默认1)
        返回: Semaphore 对象
        """

        def semaphore_creator():
            return threading.Semaphore(value)

        return self._create_sync_object('semaphore', name, semaphore_creator)

    def create_queue(self, name, maxsize=0):
        """
        创建一个命名的队列

        参数:
            name: 队列名称 (str)
            maxsize: 队列最大容量 (int, 0=无限)
        返回: Queue 对象
        """

        def queue_creator():
            return queue.Queue(maxsize)

        return self._create_sync_object('queue', name, queue_creator)

    def _create_sync_object(self, obj_type, name, creator_func):
        """
        内部方法：创建同步对象

        参数:
            obj_type: 对象类型 ('lock', 'rlock', 'condition', 'semaphore', 'queue')
            name: 对象名称 (str)
            creator_func: 创建对象的函数
        返回: 同步对象
        """
        obj_store = self.sync_objects.get(obj_type)
        if not obj_store:
            raise ValueError(f"无效的对象类型: {obj_type}")

        if name in obj_store:
            print(f"[ThreadTool] 警告: {obj_type} '{name}' 已存在，返回现有对象")
            return obj_store[name]

        obj = creator_func()
        obj_store[name] = obj
        print(f"[ThreadTool] 创建{obj_type}: {name}")
        return obj

    def set_global_event(self):
        """
        设置全局事件标志
        """
        self.event.set()
        print("[ThreadTool] 全局事件已设置")

    def clear_global_event(self):
        """
        清除全局事件标志
        """
        self.event.clear()
        print("[ThreadTool] 全局事件已清除")

    def wait_global_event(self, timeout=None):
        """
        等待全局事件标志被设置

        参数:
            timeout: 超时时间(秒) (float, 默认None)
        返回: 是否在超时前等到事件 (bool)
        """
        result = self.event.wait(timeout)
        status = "等到事件" if result else "超时"
        print(f"[ThreadTool] 等待全局事件: {status}")
        return result

    def execute_in_pool(self, tasks, max_workers=None):
        """
        使用线程池执行任务

        功能: 使用线程池并发执行多个任务
        参数:
            tasks: 任务列表 [(func, args, kwargs)]
            max_workers: 最大工作线程数 (int, None=自动)
        返回: 任务结果列表

        示例:
            # 定义任务函数
            def calculate_square(number):
                time.sleep(0.5)
                return number * number

            # 准备任务
            tasks = [
                (calculate_square, (1,), {}),
                (calculate_square, (2,), {}),
                (calculate_square, (3,), {}),
            ]

            # 使用线程池执行
            results = tool.execute_in_pool(tasks, max_workers=2)
            print("计算结果:", results)
        """
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for task in tasks:
                func = task[0]
                args = task[1] if len(task) > 1 else ()
                kwargs = task[2] if len(task) > 2 else {}
                future = executor.submit(func, *args, **kwargs)
                futures[future] = task

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    task_str = str(futures[future])[:50]
                    print(f"[ThreadPool] 任务完成: {task_str}...")
                except Exception as e:
                    print(f"[ThreadPool] 错误: 任务失败: {str(e)}")
                    results.append(None)

        return results


# 示例使用
# if __name__ == "__main__":
#     # 创建线程工具实例
#     tool = ThreadTool()
#
#
#     # 使用 create_thread() 方法中的示例
#     # 定义线程函数
#     def worker(thread_id, sleep_time):
#         print(f"线程 {thread_id} 开始, 将休眠 {sleep_time} 秒")
#         time.sleep(sleep_time)
#         print(f"线程 {thread_id} 结束")
#         return f"线程 {thread_id} 结果"
#
#
#     # 创建并启动线程
#     print("\n=== create_thread() 方法示例 ===")
#     thread1 = tool.create_thread(
#         target=worker,
#         name="示例线程1",
#         args=(1, 2),
#         daemon=False
#     )
#
#     thread2 = tool.create_thread(
#         target=worker,
#         name="示例线程2",
#         args=(2, 1)
#     )
#
#     # 等待线程结束
#     tool.join_threads()
#
#     # 线程池使用示例
#     print("\n=== execute_in_pool() 方法示例 ===")
#
#
#     # 定义任务函数
#     def calculate_square(number):
#         print(f"计算平方: {number}")
#         time.sleep(0.5)
#         return number * number
#
#
#     # 准备任务
#     tasks = [
#         (calculate_square, (1,), {}),
#         (calculate_square, (2,), {}),
#         (calculate_square, (3,), {}),
#         (calculate_square, (4,), {}),
#     ]
#
#     # 使用线程池执行
#     results = tool.execute_in_pool(tasks, max_workers=2)
#     print("计算结果:", results)
#
#     # 锁和队列使用示例
#     print("\n=== 锁和队列使用示例 ===")
#
#     # 创建共享资源
#     shared_counter = 0
#     counter_lock = tool.create_lock("counter_lock")
#     task_queue = tool.create_queue("task_queue", maxsize=5)
#
#
#     # 生产者线程函数
#     def producer(thread_id, items):
#         for i in range(items):
#             task = f"任务-{thread_id}-{i}"
#             task_queue.put(task)
#             print(f"生产者 {thread_id} 添加: {task}")
#             time.sleep(0.1)
#         print(f"生产者 {thread_id} 完成")
#
#
#     # 消费者线程函数
#     def consumer(thread_id):
#         nonlocal shared_counter
#         while True:
#             try:
#                 task = task_queue.get(timeout=1)
#                 print(f"消费者 {thread_id} 处理: {task}")
#
#                 # 使用锁保护共享资源
#                 with counter_lock:
#                     shared_counter += 1
#                     print(f"消费者 {thread_id} 更新计数器: {shared_counter}")
#
#                 task_queue.task_done()
#                 time.sleep(0.2)
#             except queue.Empty:
#                 print(f"消费者 {thread_id} 结束")
#                 break
#
#
#     # 创建生产者和消费者
#     tool.create_thread(target=producer, name="Producer-1", args=(1, 5))
#     tool.create_thread(target=producer, name="Producer-2", args=(2, 3))
#     tool.create_thread(target=consumer, name="Consumer-A")
#     tool.create_thread(target=consumer, name="Consumer-B")
#
#     # 等待所有生产者完成
#     tool.join_threads(names=["Producer-1", "Producer-2"])
#
#     # 等待队列清空
#     task_queue.join()
#
#     # 通知消费者结束
#     for _ in range(2):
#         task_queue.put(None)
#
#     # 等待所有线程结束
#     tool.join_threads()
#     print(f"最终计数器值: {shared_counter}")