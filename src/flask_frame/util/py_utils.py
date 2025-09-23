import os


def import_dir(dir_path, module_path):
    """
    导入指定目录下的所有Python模块
    :param dir_path: 目录路径
    :param module_path: 模块路径（包名）
    :return: 无
    """
    for module in os.listdir(dir_path):
        # 跳过__init__.py和非.py文件
        if module == '__init__.py' or module.find('.py') < 1:
            continue
        # 导入模块
        __import__(module_path + "." + module.split(".")[0])
