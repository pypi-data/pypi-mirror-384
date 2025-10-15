#!/usr/bin/env python3
"""
版本诊断脚本
"""

import subprocess
import os
import sys


def run_command(cmd):
    """运行命令并返回输出"""
    print(f"🔧 执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main():
    print("🔍 版本问题诊断")
    print("=" * 50)

    # 1. 检查 git 状态
    print("1. 检查 Git 状态...")
    ret, out, err = run_command("git status --porcelain")
    if out:
        print("❌ 有未提交的更改")
        print(out)
    else:
        print("✅ 工作目录干净")

    # 2. 检查标签
    print("\n2. 检查 Git 标签...")
    ret, out, err = run_command("git tag --list 'v*'")
    if out:
        print("✅ 找到标签:")
        for tag in out.split('\n'):
            ret, desc, _ = run_command(f"git describe --tags {tag}")
            print(f"   {tag}: {desc}")
    else:
        print("❌ 没有找到 v 开头的标签")

    # 3. 检查 setuptools-scm
    print("\n3. 检查 setuptools-scm...")
    try:
        import setuptools_scm
        version = setuptools_scm.get_version()
        print(f"✅ setuptools-scm 检测到版本: {version}")

        # 检查根目录
        root = setuptools_scm.get_root()
        print(f"   项目根目录: {root}")

    except Exception as e:
        print(f"❌ setuptools-scm 错误: {e}")

    # 4. 检查项目结构
    print("\n4. 检查项目结构...")
    if os.path.exists("src/bruce_li_tc"):
        print("✅ src/bruce_li_tc 目录存在")
        if os.path.exists("src/bruce_li_tc/__init__.py"):
            print("✅ src/bruce_li_tc/__init__.py 存在")
        else:
            print("❌ src/bruce_li_tc/__init__.py 不存在")
    else:
        print("❌ src/bruce_li_tc 目录不存在")

    # 5. 建议
    print("\n5. 建议:")
    if not out:  # 没有标签
        print("💡 创建第一个标签: git tag v0.7.5 && git push origin v0.7.5")
    print("💡 如果问题持续，尝试在 pyproject.toml 中添加:")
    print("""
[tool.setuptools_scm]
write_to = "src/bruce_li_tc/_version.py"
fallback_version = "0.7.5"
""")


if __name__ == "__main__":
    main()