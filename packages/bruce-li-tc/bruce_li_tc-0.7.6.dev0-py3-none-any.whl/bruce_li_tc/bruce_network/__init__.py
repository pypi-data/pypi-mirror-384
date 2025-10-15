"""
bruce_network - 网络工具包

包含功能：
- IP地址获取
- 空闲端口检测
- Ping操作
- 端口扫描
- 网络诊断
"""

from .B_NetworkUtils import B_NetworkUtils

__all__ = [
    'B_NetworkUtils'
]

# 简化导入：用户可以直接从 bruce_li_tc 导入 B_NetworkUtils
# 例如: from bruce_li_tc import B_NetworkUtils