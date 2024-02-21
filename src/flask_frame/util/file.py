def zip_path(path, result_path):
    """
    压缩文件夹
    :param path: 压缩路径
    :param result_path: 结果文件路径
    :return: 结果文件路径
    """
    import os
    import zipfile

    z = zipfile.ZipFile(result_path, "w", zipfile.ZIP_DEFLATED)  # 参数一：文件夹名
    for current_path, dir_list, file_list in os.walk(path):
        for file_name in file_list:
            fpath = current_path.replace(path, "")
            fpath = fpath and fpath + os.sep or ""
            z.write(os.path.join(path, file_name), fpath + file_name)

    z.close()
    return result_path


# zip_path("log", "log.zip")
