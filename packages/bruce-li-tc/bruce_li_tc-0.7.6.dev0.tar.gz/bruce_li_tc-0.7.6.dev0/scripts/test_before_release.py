#!/usr/bin/env python3
"""
发布前测试脚本
"""

import subprocess
import sys


def run_command(cmd):
    """运行命令并检查结果"""
    print(f"🧪 测试: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 失败: {result.stderr}")
        return False
    print("✅ 通过")
    return True


def main():
    """主测试流程"""
    print("🔍 Bruce Li TC 发布前检查")
    print("=" * 40)

    tests_passed = True

    print("1. Python语法检查...")
    tests_passed &= run_command("python -m py_compile src/bruce_li_tc/__init__.py")

    print("2. 包导入测试...")
    tests_passed &= run_command(
        'python -c "import sys; sys.path.insert(0, \\"src\\"); from bruce_li_tc import __version__; print(f\\"版本: {__version__}\\")"')

    print("3. 包构建测试...")
    tests_passed &= run_command("python -m build")

    print("4. 包格式验证...")
    tests_passed &= run_command("python -m twine check dist/*")

    if tests_passed:
        print("\n🎉 所有检查通过! 可以安全发布。")
        return 0
    else:
        print("\n❌ 检查失败! 请修复问题后再发布。")
        return 1


if __name__ == "__main__":
    sys.exit(main())