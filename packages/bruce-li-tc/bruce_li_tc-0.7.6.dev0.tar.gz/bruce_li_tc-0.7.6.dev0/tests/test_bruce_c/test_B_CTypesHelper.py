import pytest
import ctypes
import os
import threading
import multiprocessing
from unittest.mock import MagicMock, patch, call
from ctypes import Structure, Union, POINTER, byref, c_char_p, c_int, c_float, c_bool


# 测试用结构体和共用体定义
class SampleStruct(Structure):
    _fields_ = [("id", c_int), ("name", c_char_p), ("active", c_bool)]


class SampleUnion(Union):
    _fields_ = [("int_val", c_int), ("float_val", c_float)]


# ==================== Fixtures ====================
@pytest.fixture
def mock_dll():
    """模拟 DLL 对象"""
    dll = MagicMock()
    dll_path = "/path/to/mock.dll"
    with patch("ctypes.WinDLL", return_value=dll):
        yield dll


@pytest.fixture
def helper(mock_dll):
    """初始化测试助手"""
    helper = B_CTypesHelper("/path/to/mock.dll", thread_safe=True)

    # 注册自定义类型
    helper.register_custom_type("SampleStruct", SampleStruct)
    helper.register_custom_type("SampleUnion", SampleUnion)

    return helper


# ==================== 核心功能测试 ====================
class TestCoreFunctionality:
    def test_dll_loading_failure(self):
        """测试 DLL 加载失败场景"""
        with pytest.raises(FileNotFoundError):
            B_CTypesHelper("/invalid/path.dll")

    def test_struct_definition(self, helper):
        """测试结构体定义"""
        Point = helper.define_struct("Point", x=c_int, y=c_int)
        assert issubclass(Point, Structure)
        assert [f[0] for f in Point._fields_] == ["x", "y"]
        assert helper._structs["Point"] == Point

    def test_union_definition(self, helper):
        """测试共用体定义"""
        Data = helper.define_union("Data", i=c_int, f=c_float)
        assert issubclass(Data, Union)
        assert [f[0] for f in Data._fields_] == ["i", "f"]
        assert helper._unions["Data"] == Data

    def test_custom_type_registration(self, helper):
        """测试自定义类型注册"""
        helper.register_custom_type("MyHandle", c_char_p)
        assert helper._custom_types["MyHandle"] == c_char_p


# ==================== 函数封装测试 ====================
class TestFunctionWrapping:
    def test_basic_function_wrapping(self, helper, mock_dll):
        """测试基本函数封装"""
        # 配置模拟函数
        mock_dll.Add.argtypes = [c_int, c_int]
        mock_dll.Add.restype = c_int
        mock_dll.Add.return_value = 5

        # 封装函数
        @helper.function("Add", [("a", int), ("b", int)], int)
        def Add(a: int, b: int) -> int: pass

        # 调用并验证
        result = Add(2, 3)
        assert result == 5
        mock_dll.Add.assert_called_once_with(2, 3)

    def test_string_conversion(self, helper, mock_dll):
        """测试字符串参数自动转换"""
        # 配置模拟函数
        mock_dll.Print.argtypes = [c_char_p]
        mock_dll.Print.restype = None

        # 封装函数
        @helper.function("Print", [("text", str)], None)
        def Print(text: str) -> None: pass

        # 调用并验证
        Print("hello")
        mock_dll.Print.assert_called_once_with(b"hello")

    def test_struct_pointer_handling(self, helper, mock_dll):
        """测试结构体指针处理"""
        # 配置模拟函数
        mock_dll.UpdateStruct.argtypes = [POINTER(SampleStruct)]
        mock_dll.UpdateStruct.restype = None

        # 封装函数
        @helper.function("UpdateStruct", [("data", "SampleStruct*")], None)
        def UpdateStruct(data: POINTER(SampleStruct)) -> None: pass

        # 准备测试数据
        struct = SampleStruct(id=1, name=b"test", active=True)
        UpdateStruct(byref(struct))

        # 验证指针传递
        args, _ = mock_dll.UpdateStruct.call_args
        assert isinstance(args[0], POINTER(SampleStruct))

    def test_thread_lock_usage(self, helper, mock_dll):
        """测试线程锁机制"""
        # 配置模拟函数
        mock_dll.ThreadSafeFunc.argtypes = []
        mock_dll.ThreadSafeFunc.restype = None

        # 封装函数（显式禁用锁）
        @helper.function("ThreadSafeFunc", return_type=None, use_lock=False)
        def ThreadSafeFunc() -> None: pass

        # 调用函数
        ThreadSafeFunc()

        # 验证锁未被使用
        assert helper._lock.locked() is False


# ==================== 类型系统测试 ====================
class TestTypeSystem:
    @pytest.mark.parametrize("type_hint, expected", [
        ("c_int", ctypes.c_int),
        (int, ctypes.c_int),
        ("SampleStruct", SampleStruct),
        ("SampleStruct*", POINTER(SampleStruct)),
        (list, None)  # 无效类型
    ])
    def test_type_resolution(self, helper, type_hint, expected):
        """测试类型解析逻辑"""
        if expected is None:
            with pytest.raises(TypeError):
                helper._resolve_type(type_hint)
        else:
            assert helper._resolve_type(type_hint) == expected

    def test_complex_type_resolution(self, helper):
        """测试复杂类型解析"""
        # 定义嵌套类型
        helper.define_struct("Outer", inner="SampleStruct")

        # 解析指针类型
        result = helper._resolve_type("Outer*")
        assert result == POINTER(helper._structs["Outer"])


# ==================== 结构体操作测试 ====================
class TestStructOperations:
    def test_fill_structure(self, helper):
        """测试结构体填充"""
        data = {"id": 10, "name": "test", "active": True}
        struct = helper.fill_structure(SampleStruct, data)

        assert struct.id == 10
        assert struct.name == b"test"
        assert struct.active is True

    def test_fill_structure_invalid_field(self, helper):
        """测试填充无效字段"""
        with pytest.raises(AttributeError):
            helper.fill_structure(SampleStruct, {"invalid_field": 123})

    def test_dump_structure(self, helper):
        """测试结构体导出"""
        struct = SampleStruct(id=20, name=b"dump_test", active=False)
        result = helper.dump_structure(struct)

        assert result == {"id": 20, "name": b"dump_test", "active": False}

    def test_string_decoding_in_dump(self, helper):
        """测试导出时的字符串解码"""

        # 创建带字节数组的结构体
        class StringStruct(Structure):
            _fields_ = [("data", ctypes.c_char * 10)]

        s = StringStruct()
        s.data = b"hello\x00world"  # 带空字符的字节串

        result = helper.dump_structure(s)
        assert result["data"] == "hello"  # 应解码到第一个空字符


# ==================== 多线程安全测试 ====================
class TestThreadSafety:
    def test_thread_lock_context(self, helper):
        """测试线程安全上下文管理器"""
        with helper.thread_safe():
            assert helper._lock.locked() is True
        assert helper._lock.locked() is False

    def test_concurrent_access(self, helper, mock_dll):
        """测试并发访问时的线程安全"""
        # 配置模拟函数
        mock_dll.Counter = MagicMock(side_effect=range(100))
        mock_dll.Counter.argtypes = []
        mock_dll.Counter.restype = c_int

        # 封装函数
        @helper.function("Counter", return_type=int)
        def Counter() -> int:
            pass

        # 并发调用
        results = []

        def worker():
            with helper.thread_safe():
                results.append(Counter())

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()

        # 验证顺序调用
        assert sorted(results) == list(range(10))
        assert mock_dll.Counter.call_count == 10


# ==================== 错误处理测试 ====================
class TestErrorHandling:
    def test_missing_function(self, helper, mock_dll):
        """测试DLL缺少函数"""
        # 配置模拟DLL引发AttributeError
        mock_dll.__getitem__.side_effect = AttributeError("Function not found")

        with pytest.raises(RuntimeError, match="Function not found in DLL: MissingFunc"):
            @helper.function("MissingFunc", return_type=None)
            def MissingFunc(): pass

    def test_argument_conversion_error(self, helper, mock_dll):
        """测试参数转换错误"""

        @helper.function("Process", [("data", "SampleStruct*")], None)
        def Process(data): pass

        # 传递无效参数类型
        with pytest.raises(RuntimeError, match="DLL call failed: Process"):
            Process("invalid_argument")

    def test_dll_exception_propagation(self, helper, mock_dll):
        """测试DLL异常传播"""
        mock_dll.FailFunc.side_effect = ctypes.WinError(5)  # 模拟Windows错误

        @helper.function("FailFunc", return_type=None)
        def FailFunc(): pass

        with pytest.raises(RuntimeError, match="DLL call failed: FailFunc"):
            FailFunc()


# ==================== 多进程兼容性测试 ====================
def test_multiprocess_compatibility():
    """测试多进程环境兼容性"""

    def worker():
        # 每个进程独立实例
        helper = B_CTypesHelper("/path/to/mock.dll")
        helper.register_custom_type("SampleStruct", SampleStruct)

        @helper.function("ProcFunc", return_type=c_int)
        def ProcFunc(): return 42

        assert ProcFunc() == 42

    # 启动多进程测试
    processes = []
    for _ in range(2):
        p = multiprocessing.Process(target=worker)
        p.start()
        processes.append(p)

    for p in processes:
        p.join(timeout=1)
        assert p.exitcode == 0


# ==================== 集成测试 ====================
class TestIntegration:
    def test_complex_workflow(self, helper, mock_dll):
        """测试完整工作流程：定义->注册->封装->调用"""
        # 1. 定义新结构体
        helper.define_struct("Config",
                             id=c_int,
                             name=ctypes.c_char * 32,
                             enabled=c_bool
                             )

        # 2. 注册函数
        mock_dll.GetConfig.argtypes = [c_int, POINTER(helper._structs["Config"])]
        mock_dll.GetConfig.restype = c_bool

        # 模拟返回值
        def mock_get_config(index, config_ptr):
            config = config_ptr.contents
            config.id = 100 + index
            config.name = f"Device{index}".encode()
            config.enabled = True
            return True

        mock_dll.GetConfig.side_effect = mock_get_config

        # 3. 封装函数
        @helper.function("GetConfig",
                         arg_types=[("index", int), ("config", "Config*")],
                         return_type=bool,
                         doc="获取配置"
                         )
        def GetConfig(index: int, config) -> bool: pass

        # 4. 调用函数
        config = helper._structs["Config"]()
        success = GetConfig(1, byref(config))

        # 5. 验证结果
        assert success is True
        assert config.id == 101
        assert config.name.decode().startswith("Device1")
        assert config.enabled is True

        # 6. 导出结构体
        config_dict = helper.dump_structure(config)
        assert config_dict == {
            "id": 101,
            "name": "Device1",
            "enabled": True
        }