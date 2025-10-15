#!/usr/bin/env python3
"""
诊断项目文件编码问题
"""

import os
import chardet
import sys
from pathlib import Path


def check_file_encoding(file_path):
    """检查文件编码"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)

            # 尝试用检测到的编码读取
            try:
                content = raw_data.decode(result['encoding'] or 'utf-8')
                return True, result['encoding'], "可读"
            except UnicodeDecodeError as e:
                return False, result['encoding'], f"解码错误: {e}"

    except Exception as e:
        return False, "unknown", f"读取错误: {e}"


def main():
    print("🔍 项目文件编码诊断")
    print("=" * 50)

    problem_files = []

    # 检查关键文件
    key_files = [
        'pyproject.toml',
        'README.md',
        'CHANGELOG.md',
        'requirements.txt',
        'requirements-dev.txt'
    ]

    # 检查Python文件
    python_files = list(Path('src').rglob('*.py'))
    python_files.extend(Path('tests').rglob('*.py'))
    python_files.extend(Path('scripts').rglob('*.py'))

    all_files = [Path(f) for f in key_files if Path(f).exists()] + python_files

    print(f"检查 {len(all_files)} 个文件...")

    for file_path in all_files:
        if file_path.exists():
            success, encoding, message = check_file_encoding(file_path)
            status = "✅" if success else "❌"
            print(f"{status} {file_path}: {encoding} - {message}")

            if not success:
                problem_files.append((file_path, encoding, message))

    # 检查资源文件
    print("\n📁 检查资源文件...")
    resource_files = list(Path('src').rglob('*.png'))
    for res_file in resource_files[:5]:  # 只检查前5个
        print(f"📦 {res_file} (二进制文件)")

    if problem_files:
        print(f"\n🚨 发现 {len(problem_files)} 个有编码问题的文件:")
        for file_path, encoding, message in problem_files:
            print(f"   {file_path}: {message}")

        print("\n💡 解决方案:")
        print("   1. 用文本编辑器（如VSCode）重新保存有问题的文件为UTF-8编码")
        print("   2. 确保所有文本文件使用UTF-8编码")
        print("   3. 删除pyproject.toml中的poetry配置")
        return 1
    else:
        print("\n🎉 所有文件编码正常!")
        return 0


if __name__ == "__main__":
    sys.exit(main())