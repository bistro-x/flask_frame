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
    # 返回当前时间的字符串表示
    curr_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 日期格式化
    return curr_date


def get_file_path_name_ext(file_path):
    """
    获取文件路径， 文件名， 后缀名
    :param file_path: 文件完整路径
    :return: (路径, 文件名, 扩展名)
    """
    filepath, tmpfilename = os.path.split(file_path)
    shotname, extension = os.path.splitext(tmpfilename)
    return filepath, shotname, extension


# 解压单个文件到目标文件夹
def unzip_file(src_file, dest_dir, password=None):
    """
    解压zip文件到指定目录
    :param src_file: zip文件路径
    :param dest_dir: 解压目标目录
    :param password: 可选，zip密码
    :return: 解压后文件路径列表
    """
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

            # 处理文件名编码问题
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

            # 解压到临时目录
            file_path = zf.extract(file_path, temp_path)

            # 移动到目标目录
            if not os.path.exists(os.path.dirname(file_path_final)):
                os.makedirs(os.path.dirname(file_path_final))
            move(file_path, file_path_final)

            result.append(file_path_final)
        return result
    finally:
        # 删除临时目录
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
            # 写入压缩包
            zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
    zip.close()


# 判断文件目录是否存在，不存在则创建
def create_if_dir_no_exists(dir):
    """
    检查目录是否存在，不存在则创建
    :param dir: 目录路径
    """
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
    """
    拼接父url和子url，自动处理斜杠
    :param par_url: 父url
    :param sub_url: 子url
    :return: 拼接后的url
    """
    if par_url.endswith("/"):
        if sub_url.startswith(("/")):
            sub_url = sub_url[1:]
    else:
        if not sub_url.startswith(("/")):
            sub_url = "/" + sub_url
    return par_url + sub_url


# 获取md5代码
def get_md5_code(str):
    """
    获取字符串的md5值
    :param str: 输入字符串
    :return: md5字符串
    """
    hash_md5 = hashlib.md5()
    # 计算
    text = str.encode("utf-8", errors="ignore")
    hash_md5.update(text)
    # 获取计算结果(16进制字符串，32位字符)
    md5_str = hash_md5.hexdigest()

    return md5_str


def get_base64(str):
    """
    对字节串进行base64编码
    :param str: bytes类型
    :return: base64编码后的bytes
    """
    res = base64.b64encode(str)
    return res


def from_base64(str):
    """
    对base64编码的字节串进行解码
    :param str: base64编码的bytes
    :return: 解码后的bytes
    """
    res = base64.b64decode(str)
    return res


def random_value():
    """
    获取当前时间戳的毫秒字符串
    :return: 字符串
    """
    t = time.time()
    value = str(int(t * 1000))
    # int(random.uniform(10000, 100000))
    return value


def if_null(arg1, arg2):
    """
    如果arg1为真，返回arg1，否则返回arg2
    :param arg1:
    :param arg2:
    :return:
    """
    if arg1:
        return arg1
    else:
        return arg2


def str_to_bool(val):
    """将字符串表示的真值转换为 True 或 False。

    True 值包括 'y', 'yes', 't', 'true', 'on', '1'
    False 值包括 'n', 'no', 'f', 'false', 'off', '0'
    如果输入为空或 None，返回 False。
    如果 'val' 是其他值，则引发 ValueError。
    """
    if not val:
        return False
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return 1
    elif val in ("n", "no", "f", "false", "off", "0"):
        return 0
    else:
        raise ValueError(f"无效的真值 {val!r}")
