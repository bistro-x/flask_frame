import os


def import_dir(dir_path, module_path):
    """
    import all file form dir
    :return:
    """

    for module in os.listdir(dir_path):
        if module == '__init__.py' or module.find('.py') < 1:
            continue
        __import__(module_path + "." + module.split(".")[0])
