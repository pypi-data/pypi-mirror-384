"""
bruce_c - C语言交互工具包

包含功能：
- ctypes高级封装
- DLL动态加载
- 结构体/共用体处理
"""

from .B_CTypesHelper import B_CTypesHelper

__all__ = [
    'B_CTypesHelper'
]

# 简化导入：用户可以直接从 bruce_li_tc 导入 B_CTypesHelper
# 例如: from bruce_li_tc import B_CTypesHelper