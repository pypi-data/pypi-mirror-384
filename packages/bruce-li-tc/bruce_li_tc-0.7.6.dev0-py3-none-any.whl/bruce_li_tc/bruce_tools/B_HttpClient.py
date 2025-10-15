"""
B_HttpClient.py - 高级HTTP客户端封装
支持GET/POST请求、代理设置、多线程安全、自动重试
实现 __enter__ 和 __exit__ 方法的主要目的是：
    确保 HTTP 连接资源被可靠释放
    简化资源管理代码
    提供异常安全的保证
    支持 Pythonic 的 with 语句用法
    在多线程环境中安全地管理连接池
"""

import requests
from threading import local
from typing import Dict, Optional, Tuple, Union, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests import Response


class HttpClient:
    """
    线程安全的HTTP客户端，封装requests库
    支持GET/POST方法、代理设置、自动重试

    多线程使用注意事项:
        1. 每个线程使用独立的HttpClient实例
        2. 使用with语句确保资源正确释放
        3. 避免跨线程共享同一个实例
        4. 设置合理的超时时间防止阻塞
        5. 使用重试机制处理临时性网络错误
    """

    def __init__(self,
                 default_headers: Optional[Dict[str, str]] = None,
                 default_timeout: Union[int, float, Tuple[Union[int, float], Union[int, float]]] = 10,
                 max_retries: int = 3):
        """
        初始化HTTP客户端

        :param default_headers: 默认请求头 (字典)
        :param default_timeout: 默认超时时间(秒) (整数/浮点数/(连接超时, 读取超时))
        :param max_retries: 最大重试次数 (整数)

        示例:
            # 创建HttpClient实例
            client = HttpClient(
                default_headers={'User-Agent': 'MyApp/1.0'},
                default_timeout=15,
                max_retries=2
            )
        """
        self._thread_local = local()  # 线程局部存储
        self.default_headers = default_headers or {}
        self.default_timeout = default_timeout
        self.max_retries = max_retries

    def __enter__(self) -> "HttpClient":
        """
        上下文管理器入口

        返回: HttpClient实例

        示例:
            with HttpClient() as client:
                response = client.get('https://api.example.com/data')
                print(response.json())
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        上下文管理器退出时自动关闭Session

        示例:
            # 自动调用__exit__关闭资源
            with HttpClient() as client:
                ...  # 使用client
        """
        self.close()

    def _get_session(self) -> requests.Session:
        """
        获取当前线程的Session对象（线程安全）

        返回: requests.Session对象
        """
        if not hasattr(self._thread_local, "session"):
            session = requests.Session()

            # 设置重试机制
            if self.max_retries > 0:
                retry_strategy = Retry(
                    total=self.max_retries,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["GET", "POST", "PUT", "DELETE"],
                    backoff_factor=0.3,
                    raise_on_status=False
                )
                adapter = HTTPAdapter(max_retries=retry_strategy)
                session.mount("http://", adapter)
                session.mount("https://", adapter)

            self._thread_local.session = session
        return self._thread_local.session

    def _merge_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """
        合并默认请求头和自定义请求头

        :param headers: 自定义请求头 (字典)
        :return: 合并后的请求头字典
        """
        merged = self.default_headers.copy()
        if headers:
            merged.update(headers)
        return merged

    def request(self,
                method: str,
                url: str,
                params: Optional[Dict[str, Any]] = None,
                data: Optional[Union[Dict[str, Any], bytes]] = None,
                json_data: Optional[Dict[str, Any]] = None,
                headers: Optional[Dict[str, str]] = None,
                proxies: Optional[Dict[str, str]] = None,
                timeout: Optional[Union[int, float, Tuple[Union[int, float], Union[int, float]]]] = None,
                **kwargs: Any) -> Response:
        """
        执行HTTP请求

        :param method: HTTP方法 (字符串: GET/POST/PUT/DELETE)
        :param url: 请求URL (字符串)
        :param params: URL查询参数 (字典)
        :param data: 表单数据 (字典/字节)
        :param json_data: JSON数据 (字典)
        :param headers: 请求头 (字典)
        :param proxies: 代理设置 (字典) 格式: {'http': 'http://proxy:port', 'https': 'https://proxy:port'}
        :param timeout: 超时时间(秒) (整数/浮点数/(连接超时, 读取超时))
        :param kwargs: 其他requests参数
        :return: requests.Response对象
        :raises: RuntimeError 当请求失败时

        示例:
            # 使用request方法执行GET请求
            response = client.request(
                method='GET',
                url='https://api.example.com/data',
                params={'page': 1, 'limit': 10},
                headers={'Authorization': 'Bearer token'}
            )

            # 使用request方法执行POST请求
            response = client.request(
                method='POST',
                url='https://api.example.com/users',
                json_data={'name': 'John', 'email': 'john@example.com'},
                headers={'Content-Type': 'application/json'}
            )
        """
        # 合并请求头
        headers = self._merge_headers(headers)
        # 设置超时
        timeout = timeout or self.default_timeout

        session = self._get_session()

        try:
            response = session.request(
                method=method.upper(),
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=headers,
                proxies=proxies,
                timeout=timeout,
                **kwargs
            )
            response.raise_for_status()  # 自动检查HTTP错误
            return response
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request to {url} failed: {str(e)}") from e

    def get(self,
            url: str,
            params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
            proxies: Optional[Dict[str, str]] = None,
            timeout: Optional[Union[int, float, Tuple[Union[int, float], Union[int, float]]]] = None,
            **kwargs: Any) -> Response:
        """
        执行GET请求

        :param url: 请求URL (字符串)
        :param params: URL查询参数 (字典)
        :param headers: 请求头 (字典)
        :param proxies: 代理设置 (字典)
        :param timeout: 超时时间(秒) (整数/浮点数/(连接超时, 读取超时))
        :param kwargs: 其他requests参数
        :return: requests.Response对象

        示例:
            # 执行GET请求
            response = client.get(
                url='https://api.example.com/users',
                params={'id': 123},
                headers={'Accept': 'application/json'}
            )

            # 处理响应
            if response.status_code == 200:
                user_data = response.json()
                print(user_data)
        """
        return self.request('GET', url, params=params, headers=headers,
                            proxies=proxies, timeout=timeout, **kwargs)

    def post(self,
             url: str,
             data: Optional[Union[Dict[str, Any], bytes]] = None,
             json_data: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None,
             proxies: Optional[Dict[str, str]] = None,
             timeout: Optional[Union[int, float, Tuple[Union[int, float], Union[int, float]]]] = None,
             **kwargs: Any) -> Response:
        """
        执行POST请求

        :param url: 请求URL (字符串)
        :param data: 表单数据 (字典/字节)
        :param json_data: JSON数据 (字典)
        :param headers: 请求头 (字典)
        :param proxies: 代理设置 (字典)
        :param timeout: 超时时间(秒) (整数/浮点数/(连接超时, 读取超时))
        :param kwargs: 其他requests参数
        :return: requests.Response对象

        示例:
            # 执行JSON POST请求
            response = client.post(
                url='https://api.example.com/users',
                json_data={'name': 'Alice', 'email': 'alice@example.com'},
                headers={'Content-Type': 'application/json'}
            )

            # 执行表单POST请求
            response = client.post(
                url='https://api.example.com/login',
                data={'username': 'admin', 'password': 'secret'},
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
        """
        return self.request('POST', url, data=data, json_data=json_data, headers=headers,
                            proxies=proxies, timeout=timeout, **kwargs)

    def close(self) -> None:
        """
        关闭所有线程的Session（多线程环境结束时必须调用）

        多线程注意事项:
            1. 在程序退出前调用close()释放资源
            2. 使用with语句自动调用close()
            3. 每个线程结束时自动清理其Session

        示例:
            # 手动关闭资源
            client = HttpClient()
            try:
                response = client.get('https://example.com')
                # 处理响应...
            finally:
                client.close()

            # 使用with语句自动关闭
            with HttpClient() as client:
                response = client.get('https://example.com')
                # 处理响应...
        """
        if hasattr(self._thread_local, "session"):
            try:
                self._thread_local.session.close()
            finally:
                del self._thread_local.session