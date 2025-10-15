# Bruce Li TC

高级Python工具库，提供微信自动化、时间和数据处理功能。

## 功能特性

- ? 微信视频自动化操作
- ? 高级时间处理工具
- ? 数据分析和处理
- ? 网络请求和数据库操作
- ? 图像处理和计算机视觉

## 安装

```bash
pip install bruce-li-tc
```
## 目录结构
```
Bruce_li_tc/                          # ?? 项目根目录（普通文件夹）
├── .github/                          # ?? GitHub配置目录（普通文件夹）
│   └── workflows/                    # ?? GitHub Actions工作流（普通文件夹）
│       ├── ci.yml                    # ? CI测试配置文件
│       └── release.yml               # ? 自动发布配置文件
├── src/                              # ?? 源代码目录（普通文件夹）
│   └── bruce_li_tc/                  # ?? Python包目录（Python包，必须有__init__.py）
│       ├── __init__.py               # ? 包初始化文件（Python包标识）
│       ├── _version.py               # ? 版本管理文件（会被setuptools-scm覆盖）
│       ├── wechatauto/               # ?? 微信自动化模块（Python子包）
│       │   ├── __init__.py           # ? 子包初始化文件
│       │   └── wechat_video_automator/
│       │       └── bruce_uiauto/     # ?? 资源文件目录
│       └── network/                  # ?? 网络工具模块（Python子包）
│           ├── __init__.py           # ? 子包初始化文件
│           └── ...                   # 其他网络模块文件
├── tests/                            # ?? 测试目录（普通文件夹）
│   └── __init__.py                   # ? 测试包初始化文件
├── scripts/                          # ?? 脚本目录（普通文件夹）
│   ├── update_version.py             # ? 版本更新脚本
│   └── test_before_release.py        # ? 发布前测试脚本
├── venv/                             # ?? 虚拟环境（.gitignore忽略）
├── dist/                            # ?? 构建输出（.gitignore忽略）
├── .gitignore                       # ? Git忽略规则
├── pyproject.toml                   # ? 项目构建配置
├── requirements.txt                 # ? 项目依赖
├── requirements-dev.txt             # ? 开发依赖
├── CHANGELOG.md                     # ? 变更日志（也是当前README）
└── README.md                        # ? 项目介绍文档（新增）
```