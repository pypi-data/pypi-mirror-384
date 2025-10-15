import os


def format_path(path):
    """统一路径格式为斜杠分隔"""
    return path.replace("\\", "/") if path else ""


def get_default_icon():
    """获取默认图标路径"""
    default_icons = ["app.ico", "icon.ico", "favicon.ico"]
    for icon in default_icons:
        if os.path.exists(icon):
            return icon
    return ""


def create_config(venv_path, entry_file, output_name, project_dir, **kwargs):
    """创建配置字典"""
    python_exec = os.path.join(venv_path, "Scripts", "python.exe")
    dist_dir = os.path.join(project_dir, "dist")

    return {
        'venv_path': venv_path,
        'python_exec': python_exec,
        'entry_file': entry_file,
        'output_name': output_name,
        'project_dir': project_dir,
        'dist_dir': dist_dir,
        'onefile': kwargs.get('onefile', True),
        'noconsole': kwargs.get('noconsole', False),
        'clean': kwargs.get('clean', True),
        'icon': kwargs.get('icon', ''),
        'data': kwargs.get('data', []),
        'hidden_imports': kwargs.get('hidden_imports', []),
        'exclude_modules': kwargs.get('exclude_modules', [])
    }