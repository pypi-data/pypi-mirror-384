#!/usr/bin/env python3
"""
版本管理和发布脚本
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True):
    """运行shell命令"""
    print(f"🔧 执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"❌ 失败: {result.stderr}")
        return False, result.stderr
    return True, result.stdout.strip()


def get_next_version():
    """基于现有标签确定下一个版本号"""
    success, output = run_command("git tag --list 'v*' --sort=-version:refname")

    if not success or not output.strip():
        print("📝 没有找到现有标签，从v0.8.0开始")
        return "0.8.0"

    latest_tag = output.split('\n')[0].strip()
    if latest_tag.startswith('v'):
        latest_tag = latest_tag[1:]

    print(f"📝 最新标签: v{latest_tag}")

    try:
        major, minor, patch = map(int, latest_tag.split('.'))

        print("\n🎯 请选择版本号递增方式:")
        print(f"1. 主版本号 (v{major + 1}.0.0) - 不兼容的API修改")
        print(f"2. 次版本号 (v{major}.{minor + 1}.0) - 向后兼容的功能性新增")
        print(f"3. 修订号 (v{major}.{minor}.{patch + 1}) - 向后兼容的问题修正")

        choice = input("请输入选择 (1/2/3, 默认3): ").strip() or "3"

        if choice == "1":
            return f"{major + 1}.0.0"
        elif choice == "2":
            return f"{major}.{minor + 1}.0"
        else:
            return f"{major}.{minor}.{patch + 1}"

    except ValueError:
        print("❌ 标签格式错误，使用默认版本v0.8.0")
        return "0.8.0"


def update_changelog(version):
    """更新变更日志文件"""
    changelog_path = Path("CHANGELOG.md")

    if not changelog_path.exists():
        content = f"""# 变更日志

## [v{version}] - 版本发布
### 新增功能
- 初始版本发布
"""
        changelog_path.write_text(content, encoding='utf-8')
        print(f"✅ 创建CHANGELOG.md")
        return True

    content = changelog_path.read_text(encoding='utf-8')

    if f"## [v{version}]" in content:
        print(f"⚠️  版本v{version}已存在于变更日志中")
        return True

    new_section = f"""## [v{version}] - 版本发布
### 新增功能
- 描述新功能...

### 修复问题  
- 修复的问题...
"""

    if content.startswith("# 变更日志"):
        lines = content.split('\n')
        new_content = [lines[0]] + [""] + new_section.split('\n') + lines[1:]
        changelog_path.write_text('\n'.join(new_content), encoding='utf-8')
    else:
        changelog_path.write_text(f"# 变更日志\n\n{new_section}{content}", encoding='utf-8')

    print(f"✅ 更新CHANGELOG.md，添加版本v{version}")
    return True


def main():
    """主函数 - 版本发布流程"""
    print("🚀 Bruce Li TC 版本发布管理")
    print("=" * 50)

    print("1. 检查工作目录状态...")
    success, status = run_command("git status --porcelain", check=False)
    if status.strip():
        print("❌ 工作目录有未提交的更改:")
        print(status)
        print("\n💡 请先提交或暂存更改后再发布版本")
        return 1

    print("2. 同步远程仓库...")
    run_command("git pull origin main")

    print("3. 确定新版本号...")
    next_version = get_next_version()
    print(f"🎯 新版本号: v{next_version}")

    print("4. 更新变更日志...")
    update_changelog(next_version)

    print("5. 提交更改...")
    run_command('git add CHANGELOG.md')
    run_command(f'git commit -m "准备发布v{next_version}"')

    print("6. 创建版本标签...")
    run_command(f'git tag v{next_version}')
    run_command("git push origin main")
    run_command(f"git push origin v{next_version}")

    print("\n🎉 版本发布流程已启动!")
    print("=" * 50)
    print("CI/CD 将自动执行:")
    print("✅ 运行测试套件")
    print("✅ 构建分发包")
    print("✅ 发布到 PyPI")
    print("✅ 创建 GitHub Release")
    print(f"✅ 新版本: v{next_version}")
    print("\n📊 查看进度: https://github.com/LWS-CSDN/Bruce_li_tc/actions")

    return 0


if __name__ == "__main__":
    sys.exit(main())
