import ctypes
import os
import threading
import multiprocessing
from ctypes import Structure, Union, POINTER, byref, Array
from typing import Any, Dict, List, Tuple, Type, Optional, Callable, Union as TypeUnion


class B_CTypesHelper:
    """
    ctypes 高级封装助手类，支持多线程/多进程环境
    功能包括：
      - DLL 动态加载与函数调用
      - 结构体/共用体自动封装
      - 类型安全检测与自动转换
      - 返回值解析与错误处理
      - 线程安全锁机制
      - 多进程安全支持
      - 详细的文档和类型提示

    多线程注意事项：
      1. 默认启用线程锁保证线程安全
      2. 使用 with helper.thread_safe(): 管理临界区
      3. 非线程安全的 DLL 函数需要额外同步

    多进程注意事项：
      1. 每个进程需要独立加载 DLL
      2. 共享内存需使用 multiprocessing.Value/Array
      3. 避免在 fork 后初始化 DLL
    """

    def __init__(self, dll_path: str, *, thread_safe: bool = True):
        """
        初始化 CTypes 助手
        :param dll_path: DLL 文件路径
        :param thread_safe: 是否启用线程安全锁（默认启用）
        :example:
            helper = B_CTypesHelper("mydll.dll")
        """
        if not os.path.exists(dll_path):
            raise FileNotFoundError(f"DLL not found: {dll_path}")

        self._dll = ctypes.WinDLL(dll_path)  # Windows
        # Linux/Mac: self._dll = ctypes.CDLL(dll_path)

        self._structs: Dict[str, Type[Structure]] = {}
        self._unions: Dict[str, Type[Union]] = {}
        self._custom_types: Dict[str, Any] = {}
        self._lock = threading.RLock() if thread_safe else None

    def define_struct(self, name: str, **fields: Dict[str, Any]) -> Type[Structure]:
        """
        定义结构体类型
        :param name: 结构体类型名称
        :param fields: 字段定义字典 {字段名: ctypes类型}
        :return: 定义的结构体类
        :example:
            Point = helper.define_struct("Point", x=ctypes.c_int, y=ctypes.c_int)
        """
        cls = type(name, (Structure,), {
            "_fields_": list(fields.items()),
            "_pack_": 1  # 1字节对齐
        })
        self._structs[name] = cls
        return cls

    def define_union(self, name: str, **fields: Dict[str, Any]) -> Type[Union]:
        """
        定义共用体类型
        :param name: 共用体类型名称
        :param fields: 字段定义字典 {字段名: ctypes类型}
        :return: 定义的共用体类
        :example:
            Data = helper.define_union("Data", i=ctypes.c_int, f=ctypes.c_float)
        """
        cls = type(name, (Union,), {"_fields_": list(fields.items())})
        self._unions[name] = cls
        return cls

    def register_custom_type(self, name: str, ctype: Any):
        """
        注册自定义类型别名
        :param name: 类型别名
        :param ctype: ctypes 类型
        :example:
            helper.register_custom_type("HANDLE", ctypes.c_void_p)
        """
        self._custom_types[name] = ctype

    def _resolve_type(self, type_hint: Any) -> Any:
        """解析类型提示为 ctypes 类型"""
        # 直接类型
        if isinstance(type_hint, type) and issubclass(type_hint, (Structure, Union, Array)):
            return type_hint

        # 字符串类型
        if isinstance(type_hint, str):
            if type_hint in self._structs:
                return self._structs[type_hint]
            elif type_hint in self._unions:
                return self._unions[type_hint]
            elif type_hint in self._custom_types:
                return self._custom_types[type_hint]
            elif hasattr(ctypes, type_hint):
                return getattr(ctypes, type_hint)
            elif type_hint.endswith('*'):  # 指针类型
                base_type = self._resolve_type(type_hint[:-1].strip())
                return POINTER(base_type)

        # Python 类型映射
        py_to_ctypes = {
            int: ctypes.c_int,
            float: ctypes.c_float,
            bool: ctypes.c_bool,
            str: ctypes.c_char_p,
            bytes: ctypes.c_char_p,
        }
        if type_hint in py_to_ctypes:
            return py_to_ctypes[type_hint]

        return type_hint

    def function(self, func_name: str,
                 arg_types: Optional[List[Tuple[str, Any]]] = None,
                 return_type: Any = None,
                 *,
                 doc: str = "",
                 param_docs: Optional[Dict[str, str]] = None,
                 returns: str = "",
                 use_lock: bool = True) -> Callable:
        """
        封装 DLL 函数
        :param func_name: DLL 函数名
        :param arg_types: 参数列表 [(参数名, 类型提示), ...]
        :param return_type: 返回类型提示
        :param doc: 函数说明
        :param param_docs: 参数字典说明 {参数名: 说明}
        :param returns: 返回值说明
        :param use_lock: 是否使用线程锁（默认启用）
        :return: 可调用函数
        :example:
            @helper.function("Add",
                [("a", int), ("b", int)],
                int,
                doc="计算两数之和",
                param_docs={"a": "第一个参数", "b": "第二个参数"},
                returns="计算结果")
            def Add(a: int, b: int) -> int: ...
        """
        try:
            dll_func = getattr(self._dll, func_name)
        except AttributeError:
            raise RuntimeError(f"Function not found in DLL: {func_name}") from None

        # 解析参数类型
        resolved_argtypes = []
        if arg_types:
            for _, t in arg_types:
                resolved_type = self._resolve_type(t)
                resolved_argtypes.append(resolved_type)
            dll_func.argtypes = resolved_argtypes

        # 解析返回类型
        if return_type is not None:
            dll_func.restype = self._resolve_type(return_type)

        # 构建文档字符串
        doc_lines = [f"{doc}\n\n" if doc else ""]
        if param_docs:
            doc_lines.append("Parameters:")
            for param, desc in param_docs.items():
                doc_lines.append(f"  {param}: {desc}")
        if returns:
            doc_lines.append(f"\nReturns: {returns}")

        # 包装函数
        def wrapper(*args, **kwargs):
            # 线程锁管理
            lock = self._lock if use_lock else None
            if lock:
                lock.acquire()

            try:
                # 参数类型转换
                converted_args = []
                for i, arg in enumerate(args):
                    expected_type = resolved_argtypes[i] if i < len(resolved_argtypes) else None
                    converted_args.append(self._convert_arg(arg, expected_type))

                # 调用 DLL 函数
                result = dll_func(*converted_args)

                # 返回结果处理
                return self._process_result(result, dll_func.restype)
            except Exception as e:
                raise RuntimeError(f"DLL call failed: {func_name}") from e
            finally:
                if lock:
                    lock.release()

        # 添加类型提示
        annotations = {}
        if return_type is not None:
            annotations['return'] = return_type
        if arg_types:
            for name, type_hint in arg_types:
                annotations[name] = type_hint
        wrapper.__annotations__ = annotations

        # 添加文档
        wrapper.__doc__ = "\n".join(doc_lines)
        wrapper.__name__ = func_name
        return wrapper

    def _convert_arg(self, arg: Any, expected_type: Any) -> Any:
        """转换参数到合适的 ctypes 类型"""
        # 结构体/共用体实例直接使用
        if isinstance(arg, (Structure, Union)):
            return byref(arg) if expected_type and expected_type.__name__.startswith('LP_') else arg

        # 字符串处理
        if isinstance(arg, str) and expected_type == ctypes.c_char_p:
            return arg.encode('utf-8')

        # 数组处理
        if isinstance(arg, list) and expected_type and issubclass(expected_type, Array):
            array_type = expected_type._type_ * len(arg)
            return array_type(*arg)

        # 指针类型处理
        if expected_type and issubclass(expected_type, POINTER) and not isinstance(arg, POINTER):
            # 创建临时变量并返回指针
            base_type = expected_type._type_
            temp_var = base_type(arg)
            return ctypes.byref(temp_var)

        return arg

    def _process_result(self, result: Any, restype: Any) -> Any:
        """处理函数返回结果"""
        # 指针类型处理
        if isinstance(restype, type) and issubclass(restype, POINTER):
            # 自动解引用指针
            if result:
                return result.contents
            return None

        # 结构体/共用体直接返回
        if isinstance(result, (Structure, Union)):
            return result

        # 基本类型直接返回
        return result

    def fill_structure(self, struct_type: TypeUnion[str, Type[Structure]],
                       data: Dict[str, Any]) -> Structure:
        """
        填充结构体数据
        :param struct_type: 结构体类型或类型名
        :param data: 数据字典 {字段名: 值}
        :return: 填充后的结构体实例
        :example:
            point_data = {"x": 10, "y": 20}
            point = helper.fill_structure("Point", point_data)
        """
        if isinstance(struct_type, str):
            struct_type = self._structs[struct_type]

        instance = struct_type()
        for field, value in data.items():
            # 检查字段是否存在
            if not hasattr(instance, field):
                raise AttributeError(f"结构体 {struct_type.__name__} 没有字段 '{field}'")

            # 获取字段类型
            field_type = None
            for fname, ftype in struct_type._fields_:
                if fname == field:
                    field_type = ftype
                    break

            # 特殊处理字符串字段
            if isinstance(field_type, type) and issubclass(field_type, Array) and \
                    field_type._type_ == ctypes.c_char and isinstance(value, str):
                value = value.encode('utf-8')

            setattr(instance, field, value)
        return instance

    def dump_structure(self, struct_instance: Structure) -> Dict[str, Any]:
        """
        导出结构体数据到字典
        :param struct_instance: 结构体实例
        :return: 包含数据的字典
        :example:
            point_dict = helper.dump_structure(point)
        """
        result = {}
        for field, _ in struct_instance._fields_:
            value = getattr(struct_instance, field)

            # 转换字节数组为字符串
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8').rstrip('\x00')
                except UnicodeDecodeError:
                    pass

            result[field] = value
        return result

    def thread_safe(self) -> 'B_CTypesHelper':
        """
        返回线程安全上下文管理器
        :example:
            with helper.thread_safe():
                helper.func1()
                helper.func2()
        """
        return self._LockContext(self)

    class _LockContext:
        """线程安全上下文管理器"""

        def __init__(self, helper: 'B_CTypesHelper'):
            self.helper = helper
            self.lock = helper._lock

        def __enter__(self):
            if self.lock:
                self.lock.acquire()
            return self.helper

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.lock:
                self.lock.release()


# ==================== 使用示例 ====================
# if __name__ == "__main__":
#     # 1. 初始化助手 (启用线程安全)
#     helper = B_CTypesHelper("sample.dll", thread_safe=True)
#
#
#     # 2. 定义结构体
#     class DeviceInfo(Structure):
#         _fields_ = [
#             ("id", ctypes.c_int),
#             ("name", ctypes.c_char * 32),
#             ("status", ctypes.c_byte)
#         ]
#
#
#     helper.register_custom_type("DeviceInfo", DeviceInfo)
#
#     # 3. 定义共用体
#     DataUnion = helper.define_union("DataUnion",
#                                     i=ctypes.c_int,
#                                     f=ctypes.c_float,
#                                     s=ctypes.c_char * 16
#                                     )
#
#
#     # 4. 封装DLL函数
#     @helper.function("GetDeviceCount",
#                      return_type=ctypes.c_int,
#                      doc="获取设备数量",
#                      returns="设备数量（负数表示错误代码）")
#     def GetDeviceCount() -> int:
#         """实际调用由装饰器处理"""
#
#
#     @helper.function("GetDeviceInfo",
#                      arg_types=[("index", int), ("info", "DeviceInfo*")],
#                      return_type=ctypes.c_bool,
#                      doc="获取设备信息",
#                      param_docs={
#                          "index": "设备索引 (0~设备数-1)",
#                          "info": "输出设备信息结构体指针"
#                      },
#                      returns="是否获取成功")
#     def GetDeviceInfo(index: int, info: POINTER(DeviceInfo)) -> bool:
#         """实际调用由装饰器处理"""
#
#
#     @helper.function("ProcessData",
#                      arg_types=[("data", DataUnion), ("mode", "c_byte")],
#                      return_type=ctypes.c_float,
#                      doc="处理数据",
#                      param_docs={
#                          "data": "输入数据共用体",
#                          "mode": "处理模式 (0:整数, 1:浮点, 2:字符串)"
#                      },
#                      returns="处理结果")
#     def ProcessData(data: DataUnion, mode: int) -> float:
#         """实际调用由装饰器处理"""
#
#
#     @helper.function("Calculate",
#                      arg_types=[("values", "c_int*"), ("count", int)],
#                      return_type=ctypes.c_float,
#                      doc="计算平均值",
#                      param_docs={
#                          "values": "整数数组",
#                          "count": "数组长度"
#                      },
#                      returns="平均值")
#     def Calculate(values: Array, count: int) -> float:
#         """实际调用由装饰器处理"""
#
#
#     # 5. 多线程使用示例
#     def worker():
#         with helper.thread_safe():  # 显式加锁
#             count = GetDeviceCount()
#             print(f"Thread {threading.get_ident()}: Device count={count}")
#
#
#     # 启动多个线程
#     threads = []
#     for i in range(3):
#         t = threading.Thread(target=worker)
#         t.start()
#         threads.append(t)
#
#     for t in threads:
#         t.join()
#
#
#     # 6. 多进程使用注意事项
#     def process_task():
#         # 每个进程需要重新初始化DLL助手
#         proc_helper = B_CTypesHelper("sample.dll")
#
#         # 重新注册需要的类型
#         class DeviceInfo(Structure): ...
#
#         proc_helper.register_custom_type("DeviceInfo", DeviceInfo)
#
#         # 重新封装函数
#         @proc_helper.function("GetDeviceCount", ...)
#         def GetDeviceCount(): ...
#
#         count = GetDeviceCount()
#         print(f"Process {os.getpid()}: Device count={count}")
#
#
#     if __name__ == "__main__":  # 多进程保护
#         processes = []
#         for i in range(2):
#             p = multiprocessing.Process(target=process_task)
#             p.start()
#             processes.append(p)
#
#         for p in processes:
#             p.join()
#
#     # 7. 使用示例
#     # 获取设备数量
#     count = GetDeviceCount()
#     print(f"设备数量: {count}")
#
#     # 获取第一个设备信息
#     if count > 0:
#         dev_info = DeviceInfo()
#         if GetDeviceInfo(0, byref(dev_info)):
#             # 导出结构体数据
#             info_dict = helper.dump_structure(dev_info)
#             print(f"设备信息: {info_dict}")
#
#     # 使用共用体处理数据
#     data = DataUnion()
#     data.s = b"hello"  # 设置字符串数据
#     result = ProcessData(data, mode=2)
#     print(f"字符串处理结果: {result}")
#
#     # 结构体填充示例
#     new_device = helper.fill_structure(DeviceInfo, {
#         "id": 99,
#         "name": "NewDevice",
#         "status": 1
#     })
#     print(f"新设备: {helper.dump_structure(new_device)}")
#
#     # 数组计算示例
#     values = [10, 20, 30, 40]
#     avg = Calculate((ctypes.c_int * len(values))(*values), len(values))
#     print(f"平均值: {avg:.2f}")