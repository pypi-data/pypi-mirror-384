import os
import re
import socket
import subprocess
import platform
import threading
import ipaddress
from typing import List, Dict, Tuple, Union, Optional
from multiprocessing import Pool, cpu_count


class B_NetworkUtils:
    """
    高级网络工具集 - 提供线程安全的网络操作功能

    主要功能：
      - 获取本地IP地址（IPv4/IPv6）
      - 检测空闲端口
      - Ping主机（跨平台支持）
      - 获取网络接口信息
      - 端口扫描
      - 网络连接诊断

    多线程注意事项：
      1. 所有公共方法都使用线程锁保证安全
      2. 避免在多个线程中同时调用资源密集型方法（如全端口扫描）
      3. 长时间阻塞操作（如Ping）会占用线程锁

    多进程注意事项：
      1. 每个进程有独立的GIL，适合CPU密集型操作
      2. 使用multiprocessing.Pool进行并行端口扫描
      3. 避免在子进程中修改共享状态
      4. 使用进程间通信（IPC）传递结果

    示例用法：
        from bruce_network import B_NetworkUtils

        utils = B_NetworkUtils()
        print("本地IPv4地址:", utils.get_local_ip())
        print("空闲端口:", utils.find_free_port(8000, 9000))
        print("Ping结果:", utils.ping("google.com"))
    """

    def __init__(self, thread_safe: bool = True):
        """
        初始化网络工具
        :param thread_safe: 是否启用线程安全锁（默认启用）
        """
        self._lock = threading.RLock() if thread_safe else None

    def get_local_ip(self, ipv6: bool = False, interface: str = None) -> List[str]:
        """
        获取本地IP地址列表

        :param ipv6: 是否获取IPv6地址（默认False，获取IPv4）
        :param interface: 指定网络接口名称（如'eth0'），None表示所有接口
        :return: IP地址列表，按数值排序

        示例:
            # 获取所有IPv4地址
            ipv4_list = utils.get_local_ip()

            # 获取指定接口的IPv6地址
            ipv6_list = utils.get_local_ip(ipv6=True, interface="eth0")
        """
        with self._get_lock():
            family = socket.AF_INET6 if ipv6 else socket.AF_INET
            hostname = socket.gethostname()

            try:
                addrs = socket.getaddrinfo(hostname, None, family, socket.SOCK_STREAM)
                ips = [addr[4][0] for addr in addrs]
            except socket.gaierror:
                ips = []

            # 过滤指定接口
            if interface:
                iface_ips = self._get_interface_ips(ipv6)
                ips = [ip for ip in ips if ip in iface_ips.get(interface, [])]

            # 去重并排序
            return sorted(set(ips), key=lambda ip: ipaddress.ip_address(ip))

    def get_interface_info(self) -> Dict[str, List[Dict[str, str]]]:
        """
        获取网络接口详细信息

        :return: 字典 {接口名: [{"ip": IP地址, "netmask": 子网掩码}, ...]}

        示例:
            interfaces = utils.get_interface_info()
            for iface, ips in interfaces.items():
                print(f"接口 {iface}:")
                for ip_info in ips:
                    print(f"  IP: {ip_info['ip']}, 子网掩码: {ip_info['netmask']}")
        """
        with self._get_lock():
            if platform.system() == "Windows":
                return self._get_windows_interface_info()
            else:
                return self._get_unix_interface_info()

    def find_free_port(self, start: int = 1024, end: int = 65535,
                       host: str = '0.0.0.0') -> int:
        """
        查找指定范围内的空闲端口

        :param start: 起始端口号（默认1024）
        :param end: 结束端口号（默认65535）
        :param host: 绑定主机地址（默认所有接口）
        :return: 找到的空闲端口号，找不到则返回-1

        示例:
            port = utils.find_free_port(8000, 8100)
            if port != -1:
                print(f"找到空闲端口: {port}")
        """
        with self._get_lock():
            for port in range(start, end + 1):
                if self._is_port_free(port, host):
                    return port
            return -1

    def ping(self, host: str, count: int = 4, timeout: int = 2) -> Dict[str, Union[bool, float, str]]:
        """
        Ping目标主机并返回详细结果

        :param host: 目标主机名或IP地址
        :param count: 发送的Ping包数量（默认4）
        :param timeout: 超时时间（秒，默认2）
        :return: 结果字典 {
            "success": 是否成功,
            "avg_rtt": 平均往返时间(ms),
            "packet_loss": 丢包率(%),
            "details": 原始输出
        }

        示例:
            result = utils.ping("google.com")
            if result["success"]:
                print(f"平均延迟: {result['avg_rtt']}ms")
        """
        with self._get_lock():
            if platform.system() == "Windows":
                return self._ping_windows(host, count, timeout)
            else:
                return self._ping_unix(host, count, timeout)

    def scan_ports(self, host: str, ports: Union[List[int], range],
                   timeout: float = 0.5, max_workers: int = None) -> Dict[int, str]:
        """
        扫描目标主机的端口状态（多进程并行）

        :param host: 目标主机名或IP地址
        :param ports: 要扫描的端口列表或范围
        :param timeout: 连接超时时间（秒）
        :param max_workers: 最大工作进程数（默认CPU核心数）
        :return: 字典 {端口: "open" 或 "closed"}

        多进程注意事项:
          1. 使用多进程池并行扫描提高速度
          2. 避免在子进程中修改共享状态
          3. 大量端口扫描会消耗较多资源

        示例:
            # 扫描80-100端口
            results = utils.scan_ports("localhost", range(80, 101))
            for port, status in results.items():
                print(f"端口 {port}: {status}")
        """
        with self._get_lock():
            # 将range转换为list
            if isinstance(ports, range):
                ports = list(ports)

            # 设置工作进程数
            if max_workers is None:
                max_workers = cpu_count() * 2
            max_workers = min(max_workers, len(ports))

            # 使用进程池并行扫描
            with Pool(processes=max_workers) as pool:
                tasks = [(host, port, timeout) for port in ports]
                results = pool.starmap(self._check_port_mp, tasks)

            return {port: "open" if status else "closed" for port, status in zip(ports, results)}

    def diagnose_connection(self, host: str, port: int = None) -> Dict[str, str]:
        """
        诊断到目标主机的网络连接问题

        :param host: 目标主机名或IP地址
        :param port: 目标端口（可选）
        :return: 诊断结果字典 {步骤: 结果描述}

        示例:
            report = utils.diagnose_connection("google.com", 80)
            for step, result in report.items():
                print(f"{step}: {result}")
        """
        with self._get_lock():
            report = {}

            # 步骤1: 检查DNS解析
            try:
                ip = socket.gethostbyname(host)
                report["DNS解析"] = f"成功: {host} -> {ip}"
            except socket.gaierror:
                report["DNS解析"] = "失败: 无法解析主机名"
                return report

            # 步骤2: Ping测试
            ping_result = self.ping(host, count=2, timeout=1)
            if ping_result["success"]:
                report["Ping测试"] = f"成功: 平均延迟 {ping_result['avg_rtt']}ms"
            else:
                report["Ping测试"] = "失败: 主机不可达"

            # 步骤3: 端口检查（如果指定了端口）
            if port is not None:
                if self._check_port(host, port, 1):
                    report[f"端口{port}"] = "开放"
                else:
                    report[f"端口{port}"] = "关闭或过滤"

            return report

    def _get_lock(self):
        """获取线程锁上下文管理器"""
        return self._lock if self._lock else _DummyLock()

    def _is_port_free(self, port: int, host: str) -> bool:
        """检查端口是否空闲"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                s.bind((host, port))
                return True
        except (OSError, socket.error):
            return False

    def _check_port(self, host: str, port: int, timeout: float) -> bool:
        """检查端口是否开放（单线程版本）"""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    @staticmethod
    def _check_port_mp(host: str, port: int, timeout: float) -> bool:
        """检查端口是否开放（多进程兼容版本）"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                s.connect((host, port))
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def _get_interface_ips(self, ipv6: bool) -> Dict[str, List[str]]:
        """获取各接口的IP地址"""
        interfaces = self.get_interface_info()
        result = {}
        for iface, ip_list in interfaces.items():
            result[iface] = []
            for ip_info in ip_list:
                ip = ip_info["ip"]
                try:
                    # 过滤IPv4/IPv6
                    if (ipv6 and ":" in ip) or (not ipv6 and "." in ip):
                        result[iface].append(ip)
                except ValueError:
                    continue
        return result

    def _ping_windows(self, host: str, count: int, timeout: int) -> Dict[str, Union[bool, float, str]]:
        """Windows平台Ping实现"""
        try:
            # 执行Ping命令
            result = subprocess.run(
                ["ping", "-n", str(count), "-w", str(timeout * 1000), host],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                check=False
            )
            output = result.stdout

            # 检查是否超时
            if "请求超时" in output or "timed out" in output:
                return {
                    "success": False,
                    "avg_rtt": 0.0,
                    "packet_loss": 100.0,
                    "details": output
                }

            # 解析结果
            packet_loss = 0.0
            rtts = []

            # 匹配丢包率
            loss_match = re.search(r'\((\d+)%', output)
            if loss_match:
                packet_loss = float(loss_match.group(1))

            # 匹配往返时间
            rtt_matches = re.findall(r'=(\d+)ms', output)
            if rtt_matches:
                rtts = [int(ms) for ms in rtt_matches]

            avg_rtt = sum(rtts) / len(rtts) if rtts else 0.0
            success = packet_loss < 100.0

            return {
                "success": success,
                "avg_rtt": avg_rtt,
                "packet_loss": packet_loss,
                "details": output
            }
        except Exception as e:
            return {
                "success": False,
                "avg_rtt": 0.0,
                "packet_loss": 100.0,
                "details": f"Ping执行失败: {str(e)}"
            }

    def _ping_unix(self, host: str, count: int, timeout: int) -> Dict[str, Union[bool, float, str]]:
        """Unix平台Ping实现（Linux/Mac）"""
        try:
            # 执行Ping命令
            result = subprocess.run(
                ["ping", "-c", str(count), "-W", str(timeout), host],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                check=False
            )
            output = result.stdout

            # 检查是否超时
            if "100.0% packet loss" in output:
                return {
                    "success": False,
                    "avg_rtt": 0.0,
                    "packet_loss": 100.0,
                    "details": output
                }

            # 解析结果
            packet_loss = 0.0
            rtts = []

            # 匹配丢包率
            loss_match = re.search(r'(\d+)% packet loss', output)
            if loss_match:
                packet_loss = float(loss_match.group(1))

            # 匹配往返时间
            rtt_line = re.search(r'rtt min/avg/max/mdev = [\d.]+/([\d.]+)/', output)
            if rtt_line:
                avg_rtt = float(rtt_line.group(1))
            else:
                # 备选方案：匹配每行的时间
                rtt_matches = re.findall(r'time=([\d.]+) ms', output)
                if rtt_matches:
                    rtts = [float(ms) for ms in rtt_matches]
                    avg_rtt = sum(rtts) / len(rtts) if rtts else 0.0
                else:
                    avg_rtt = 0.0

            success = packet_loss < 100.0

            return {
                "success": success,
                "avg_rtt": avg_rtt,
                "packet_loss": packet_loss,
                "details": output
            }
        except Exception as e:
            return {
                "success": False,
                "avg_rtt": 0.0,
                "packet_loss": 100.0,
                "details": f"Ping执行失败: {str(e)}"
            }

    def _get_windows_interface_info(self) -> Dict[str, List[Dict[str, str]]]:
        """Windows平台获取接口信息"""
        try:
            result = subprocess.run(
                ["ipconfig", "/all"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                check=True
            )
            output = result.stdout

            interfaces = {}
            current_iface = None

            for line in output.splitlines():
                # 检测接口开始
                iface_match = re.match(r'^([\w\s]+):$', line.strip())
                if iface_match:
                    current_iface = iface_match.group(1).strip()
                    interfaces[current_iface] = []
                    continue

                if current_iface:
                    # 匹配IPv4地址
                    ipv4_match = re.match(r'^\s*IPv4 Address[^:]*: ([0-9.]+)', line, re.IGNORECASE)
                    if ipv4_match:
                        ip = ipv4_match.group(1)
                        interfaces[current_iface].append({"ip": ip, "netmask": "255.255.255.0"})

                    # 匹配IPv6地址
                    ipv6_match = re.match(r'^\s*IPv6 Address[^:]*: ([0-9a-fA-F:]+)', line, re.IGNORECASE)
                    if ipv6_match:
                        ip = ipv6_match.group(1).split('%')[0]  # 移除接口后缀
                        interfaces[current_iface].append({"ip": ip, "netmask": "64"})

            return interfaces
        except Exception:
            return {}

    def _get_unix_interface_info(self) -> Dict[str, List[Dict[str, str]]]:
        """Unix平台获取接口信息（Linux/Mac）"""
        try:
            if platform.system() == "Darwin":  # macOS
                cmd = ["ifconfig"]
            else:  # Linux
                cmd = ["ip", "-o", "-4", "addr", "show"]
                # 获取IPv6信息需要额外命令
                ipv6_info = subprocess.run(
                    ["ip", "-o", "-6", "addr", "show"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                ).stdout

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                check=True
            )
            output = result.stdout

            if platform.system() != "Darwin":
                output += "\n" + ipv6_info

            interfaces = {}

            # macOS解析
            if platform.system() == "Darwin":
                current_iface = None
                for line in output.splitlines():
                    # 检测接口
                    iface_match = re.match(r'^(\w+):', line)
                    if iface_match:
                        current_iface = iface_match.group(1)
                        interfaces[current_iface] = []
                        continue

                    if current_iface:
                        # 匹配IPv4地址
                        ipv4_match = re.match(r'^\s+inet (\d+\.\d+\.\d+\.\d+)\s+netmask (\w+)\s', line)
                        if ipv4_match:
                            ip = ipv4_match.group(1)
                            netmask_hex = ipv4_match.group(2)
                            netmask = self._hex_netmask_to_dotted(netmask_hex)
                            interfaces[current_iface].append({"ip": ip, "netmask": netmask})

                        # 匹配IPv6地址
                        ipv6_match = re.match(r'^\s+inet6 ([0-9a-fA-F:]+)%\w*\s+prefixlen (\d+)', line)
                        if ipv6_match:
                            ip = ipv6_match.group(1)
                            netmask = ipv6_match.group(2)
                            interfaces[current_iface].append({"ip": ip, "netmask": netmask})

            # Linux解析
            else:
                for line in output.splitlines():
                    # 示例: 2: eth0    inet 192.168.1.100/24 brd 192.168.1.255 scope global eth0
                    parts = line.split()
                    if len(parts) >= 4:
                        iface = parts[1]
                        if iface not in interfaces:
                            interfaces[iface] = []

                        if "inet" in parts:
                            ip_info = parts[3]
                            if '/' in ip_info:
                                ip, prefix = ip_info.split('/')
                                if '.' in ip:  # IPv4
                                    netmask = self._prefix_to_netmask(int(prefix))
                                else:  # IPv6
                                    netmask = prefix
                                interfaces[iface].append({"ip": ip, "netmask": netmask})

            return interfaces
        except Exception:
            return {}

    def _hex_netmask_to_dotted(self, hex_str: str) -> str:
        """将十六进制子网掩码转换为点分十进制"""
        try:
            # 移除0x前缀
            hex_str = hex_str.lower().replace('0x', '')
            # 转换为32位整数
            mask_int = int(hex_str, 16)
            # 转换为点分十进制
            return socket.inet_ntoa(mask_int.to_bytes(4, 'big'))
        except Exception:
            return "255.255.255.0"  # 默认值

    def _prefix_to_netmask(self, prefix: int) -> str:
        """将CIDR前缀转换为点分十进制子网掩码"""
        mask = (0xffffffff << (32 - prefix)) & 0xffffffff
        return socket.inet_ntoa(mask.to_bytes(4, 'big'))


class _DummyLock:
    """用于非线程安全模式的虚拟锁"""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# ==================== 使用示例 ====================
# if __name__ == "__main__":
#     utils = B_NetworkUtils()
#
#     print("=" * 50)
#     print("本地IP地址测试:")
#     print("IPv4地址:", utils.get_local_ip())
#     print("IPv6地址:", utils.get_local_ip(ipv6=True))
#
#     print("\n" + "=" * 50)
#     print("网络接口信息:")
#     interfaces = utils.get_interface_info()
#     for iface, ips in interfaces.items():
#         print(f"接口 {iface}:")
#         for ip_info in ips:
#             print(f"  IP: {ip_info['ip']}, 子网掩码: {ip_info['netmask']}")
#
#     print("\n" + "=" * 50)
#     print("空闲端口检测:")
#     free_port = utils.find_free_port(8000, 8100)
#     print(f"找到空闲端口: {free_port}")
#
#     print("\n" + "=" * 50)
#     print("Ping测试:")
#     ping_result = utils.ping("google.com")
#     print("Ping结果:", ping_result)
#
#     print("\n" + "=" * 50)
#     print("端口扫描:")
#     # 使用小范围端口作为示例
#     scan_result = utils.scan_ports("localhost", range(80, 85))
#     for port, status in scan_result.items():
#         print(f"端口 {port}: {status}")
#
#     print("\n" + "=" * 50)
#     print("连接诊断:")
#     diag_result = utils.diagnose_connection("google.com", 80)
#     for step, result in diag_result.items():
#         print(f"{step}: {result}")
#
#     # 多进程端口扫描性能测试
#     print("\n" + "=" * 50)
#     print("多进程端口扫描性能测试:")
#     import time
#
#     ports = list(range(8000, 8100))
#
#     # 单线程扫描
#     start = time.time()
#     utils.scan_ports("localhost", ports, max_workers=1)
#     single_time = time.time() - start
#
#     # 多进程扫描
#     start = time.time()
#     utils.scan_ports("localhost", ports, max_workers=8)
#     multi_time = time.time() - start
#
#     print(f"单线程扫描时间: {single_time:.2f}秒")
#     print(f"多进程扫描时间: {multi_time:.2f}秒")
#     print(f"性能提升: {single_time / multi_time:.1f}倍")