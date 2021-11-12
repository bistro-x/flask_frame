#!/usr/bin/python
# -*- coding: UTF-8 -*-

import base64
import datetime
import hashlib
import os
import time
import zipfile

# 常用函数，时间格式，文件读写等。
from shutil import move, rmtree


# 获取当前日期，格式%Y-%m-%d %H:%M:%S


def get_curr_date():
    curr_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 日期格式化
    return curr_date


def get_file_path_name_ext(file_path):
    """
    获取文件路径， 文件名， 后缀名
    :param file_path:
    :return:
    """
    filepath, tmpfilename = os.path.split(file_path)
    shotname, extension = os.path.splitext(tmpfilename)
    return filepath, shotname, extension


# 解压单个文件到目标文件夹
def unzip_file(src_file, dest_dir, password=None):
    result = []

    if password:
        password = password.encode()
    zf = zipfile.ZipFile(src_file)

    temp_path = dest_dir + "/__temp"
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)

    try:
        for file_path in zf.namelist():
            # apple cache skip
            if zf.getinfo(file_path).file_size <= 0 or "__MACOSX" in file_path:
                continue

            # get the real path
            try:
                file_path_final = file_path

                try:
                    file_path_final = file_path.encode("cp437").decode(
                        "utf-8", errors="strict"
                    )
                except:
                    file_path_final = file_path.encode("cp437").decode("gbk", "ignore")
            except:
                pass

            file_path_final = dest_dir + "/" + file_path_final

            # extract
            file_path = zf.extract(file_path, temp_path)

            # move to real path
            if not os.path.exists(os.path.dirname(file_path_final)):
                os.makedirs(os.path.dirname(file_path_final))
            move(file_path, file_path_final)

            result.append(file_path_final)
        return result
    finally:
        # delete temp file
        rmtree(temp_path)
        zf.close()


def zip_dir(dirpath, outFullName):
    """
    压缩指定文件夹
    :param dirpath: 目标文件夹路径
    :param outFullName: 压缩文件保存路径+xxxx.zip
    :return: 无
    """
    zip = zipfile.ZipFile(outFullName, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dirpath):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dirpath, "")

        for filename in filenames:
            zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
    zip.close()


# 判断文件目录是否存在，不存在则创建
def create_if_dir_no_exists(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def enum_path_files(path):
    """
     遍历目录（子目录），返回所有文件路径
    :param path: file path
    :return: file list
    """
    file_paths = []
    if not os.path.isdir(path):
        print('Error:"', path, '" is not a directory or does not exist.')
        return
    list_dirs = os.walk(path)
    for root, dirs, files in list_dirs:
        for f in files:
            file_paths.append(os.path.join(root, f))
    return file_paths


# url 路径拼接
def url_join(par_url, sub_url):
    if par_url.endswith("/"):
        if sub_url.startswith(("/")):
            sub_url = sub_url[1:]
    else:
        if not sub_url.startswith(("/")):
            sub_url = "/" + sub_url
    return par_url + sub_url


# 获取md5代码
def get_md5_code(str):
    hash_md5 = hashlib.md5()
    # 计算
    text = str.encode("utf-8", errors="ignore")
    hash_md5.update(text)
    # 获取计算结果(16进制字符串，32位字符)
    md5_str = hash_md5.hexdigest()

    return md5_str


def get_base64(str):
    res = base64.b64encode(str)
    return res


def from_base64(str):
    res = base64.b64decode(str)
    return res


def random_value():
    t = time.time()
    value = str(int(t * 1000))
    # int(random.uniform(10000, 100000))
    return value


def if_null(arg1, arg2):
    if arg1:
        return arg1
    else:
        return arg2


if __name__ == "__main__":
    print(from_base64("asdfad"))
