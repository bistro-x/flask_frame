import importlib
import os


def import_dir(dir_path, module_path):
    """
    导入指定目录下的所有Python模块及子包（递归）
    :param dir_path: 目录路径
    :param module_path: 模块路径（包名）
    """
    for entry in os.listdir(dir_path):
        full_path = os.path.join(dir_path, entry)
        # 跳过非python文件/隐藏文件
        if entry == '__init__.py' or entry.startswith('.'):
            continue
        # 如果是包（目录且含 __init__.py），导入包并递归
        if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, '__init__.py')):
            pkg_name = f"{module_path}.{entry}"
            importlib.import_module(pkg_name)
            import_dir(full_path, pkg_name)
            continue
        # 仅导入 .py 文件
        if entry.endswith('.py'):
            mod_name = entry[:-3]
            importlib.import_module(f"{module_path}.{mod_name}")