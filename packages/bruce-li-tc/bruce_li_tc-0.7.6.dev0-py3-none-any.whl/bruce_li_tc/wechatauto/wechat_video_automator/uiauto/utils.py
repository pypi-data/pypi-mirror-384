import re
from typing import Optional, List, Dict, Any
import uiautomation as auto


def extract_number_from_string(s: str) -> str:
    """
    从字符串中提取数字部分，支持整数、小数和带'万'或'万+'的数字

    参数说明：
    - s: 输入的字符串

    返回值: 提取出的数字字符串，如果没有数字则返回"0"

    使用示例：
    # 从字符串中提取数字
    number = extract_number_from_string("喜欢8.8万")
    print(number)  # 输出: "8.8万"
    """
    pattern = r'\d+\.?\d*\s*万\+?|\d+\.?\d+|\b\d+\b'
    matches = re.findall(pattern, s)

    if not matches:
        return "0"

    # 取第一个匹配项
    matched_str = matches[0]

    # 移除数字和单位之间的任何空格
    matched_str = re.sub(r'(\d)\s*万', r'\1万', matched_str)

    return matched_str


def get_control_tree_info(control, max_depth=5) -> List[Dict[str, Any]]:
    """
    获取控件树信息

    参数说明：
    - control: 起始控件
    - max_depth: 最大深度

    返回值: 控件信息列表
    """
    controls_info = []

    def _get_control_info(ctrl, depth):
        if depth > max_depth:
            return

        try:
            rect = ctrl.BoundingRectangle
            control_info = {
                'depth': depth,
                'name': ctrl.Name,
                'control_type': ctrl.ControlTypeName,
                'automation_id': ctrl.AutomationId,
                'class_name': ctrl.ClassName,
                'is_enabled': ctrl.IsEnabled,
                'is_visible': not ctrl.IsOffscreen,
                'position': (rect.left, rect.top, rect.right, rect.bottom),
                'size': (rect.width(), rect.height()),
                'process_id': ctrl.ProcessId,
            }
            controls_info.append(control_info)

            # 递归获取子控件信息
            children = ctrl.GetChildren()
            for child in children:
                _get_control_info(child, depth + 1)

        except Exception as e:
            error_info = {
                'depth': depth,
                'name': f'ERROR: {str(e)}',
                'control_type': 'Unknown',
                'automation_id': '',
                'class_name': '',
                'is_enabled': False,
                'is_visible': False,
                'position': (0, 0, 0, 0),
                'size': (0, 0),
                'process_id': 0,
            }
            controls_info.append(error_info)

    _get_control_info(control, 0)
    return controls_info


def print_control_tree(controls_info: List[Dict[str, Any]]):
    """
    打印控件树信息

    参数说明：
    - controls_info: 控件信息列表
    """
    for info in controls_info:
        indent = "  " * info['depth']
        print(f"{indent}[{info['control_type']}] {info['name']}")
        print(f"{indent}  AutomationId: {info['automation_id']}")
        print(f"{indent}  ClassName: {info['class_name']}")
        print(f"{indent}  Enabled: {info['is_enabled']}, Visible: {info['is_visible']}")
        print(f"{indent}  Position: {info['position']}")
        print(f"{indent}  Size: {info['size']}")
        print(f"{indent}  ProcessId: {info['process_id']}")