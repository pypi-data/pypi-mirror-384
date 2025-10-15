"""
1.python -m build
2.在Windows命令提示符中：
set PYTHONUTF8=1
twine upload dist/*

或者在PowerShell中：
$env:PYTHONUTF8=1
twine upload dist/*

# 创建并推送第一个标签来测试自动化发布
git tag v0.7.5
git push origin v0.7.5


1.django和fastapi的中间件
2.路由分发vs
3.堆栈分析
4.__slot__性能优化

"""


"""
bruce_li_tc - Bruce Li 的技术工具集合

包含以下子包：
1. bruce_c: C语言交互工具
2. bruce_network: 网络工具
3. bruce_tools: 通用工具


"""

# 从子包导入所有公共接口
from .bruce_c import *
from .bruce_network import *
from .bruce_tools import *
from .bruce_design_patterns import *
# from .bruce_autostart import *
from .bruce_gui_tool import *
from .bruce_crawler import *
from .wechatauto import *
from .ai_search import *
from ._version import __version__

__version__ = __version__

