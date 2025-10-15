"""
uiauto-helper - 基于uiautomation的UI自动化辅助库
"""

from .core import UIElement
from .finder import ElementFinder
from .actions import ElementActions
from .conditions import WaitConditions
from .utils import extract_number_from_string, get_control_tree_info, print_control_tree
from .exceptions import (
    UIAutomationError,
    ElementNotFoundError,
    ElementNotInteractableError,
    TimeoutError,
    ProcessError,
    ImageRecognitionError
)

__version__ = "0.1.0"
# __author__ = ""
# __email__ = ""

__all__ = [
    "UIElement",
    "ElementFinder",
    "ElementActions",
    "WaitConditions",
    "extract_number_from_string",
    "get_control_tree_info",
    "print_control_tree",
    "UIAutomationError",
    "ElementNotFoundError",
    "ElementNotInteractableError",
    "TimeoutError",
    "ProcessError",
    "ImageRecognitionError"
]