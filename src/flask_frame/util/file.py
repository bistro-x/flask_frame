# -*- coding: utf-8 -*-

import os
import shutil
import time
import urllib
from contextlib import closing

from tenacity import retry, stop_after_attempt
from requests.utils import requote_uri
from flask import has_request_context, request

from flask_frame.annotation import deprecated
import base64


def retry_warning(retry_state):
    """
    tenacity重试时的警告回调函数。
    记录重试时的参数和异常信息到日志。
    :param retry_state: tenacity.RetryCallState对象，包含重试状态信息
    """
    from flask import current_app as app

    app.logger.warning(
        f"save file args: {retry_state.args} kwargs: {retry_state.kwargs} except {retry_state.outcome.exception()}"
    )


def get_file_name(file=None, file_link=None, file_path=None, **kwargs):
    """
    获取文件名。
    优先顺序：file_path > file > file_link
    :param file: werkzeug.datastructures.FileStorage对象
    :param file_link: 文件链接（字符串）
    :param file_path: 文件路径（字符串）
    :return: 文件名字符串
    """
    if file_path:
        return file_path.split("/")[-1]
    # 保存
    if file:
        return file.filename
    elif file_link:
        return file_link.split("/")[-1]


def get_file_name(file=None, file_link=None, file_path=None, **kwargs):
    """
    获取文件名。
    优先顺序：file_path > file > file_link
    :param file: werkzeug.datastructures.FileStorage对象
    :param file_link: 文件链接（字符串）
    :param file_path: 文件路径（字符串）
    :return: 文件名字符串
    """
    if file_path:
        return os.path.basename(file_path)
    if file:
        return file.filename
    if file_link:
        return os.path.basename(urllib.parse.urlparse(file_link).path)
    return None


def clean_file_param(param):
    """清楚参数里面的文件相关参数

    Args:
        param (_type_): _description_

    Returns:
        _type_: _description_
    """

    if "file" in param:
        del param["file"]
    if "file_path" in param:
        del param["file_path"]
    if "file_link" in param:
        del param["file_link"]
    return param


@retry(reraise=True, stop=stop_after_attempt(3), after=retry_warning)
def save_file(file=None, file_link=None, file_path=None, save_dir=None, **kwargs):
    """
    保存上传文件，支持三种方式：
    1. 直接指定文件路径（file_path）
    2. 通过文件链接下载（file_link，支持ftp/http）
    3. 通过上传文件对象（file）
    :param file_path: 文件路径
    :param file_link: 文件链接
    :param file: werkzeug.datastructures.FileStorage对象
    :return: 保存后的文件路径
    """
    from context import app

    if file_path:
        return file_path

    if not file and not file_link and not file_path:
        # 没有文件参数，直接返回空
        raise ValueError("没有提供文件参数")

    if not save_dir:
        save_dir = get_upload_item_root_path()

    # 保存
    if file:
        # 上传了文件
        result_file_path = os.path.join(
            save_dir,
            str(time.time()) + os.path.splitext(file.filename)[-1],
        )
        not os.path.exists(os.path.dirname(result_file_path)) and os.makedirs(
            os.path.dirname(result_file_path)
        )
        file.save(result_file_path)

    elif file_link:
        # ftp 文件
        file_type = os.path.splitext(file_link)[-1] or ""
        result_file_path = os.path.join(save_dir, str(time.time()) + file_type)

        result_file_path = result_file_path
        not os.path.exists(os.path.dirname(result_file_path)) and os.makedirs(
            os.path.dirname(result_file_path)
        )

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0"
        }
        with closing(
            urllib.request.urlopen(
                urllib.request.Request(url=requote_uri(file_link), headers=headers)
            )
        ) as response:
            with open(result_file_path, "wb") as file:
                shutil.copyfileobj(response, file)
    else:
        # 默认返回空
        result_file_path = None

    # 返回
    return result_file_path


def get_return_item_root_path():
    """
    获取返回文件的保存根目录路径（RETURN_FOLDER）。
    若目录不存在则自动创建。
    :return: 返回文件夹路径字符串
    """
    from flask import current_app as app

    item_root_path = app.config.get("RETURN_FOLDER") or "return_files"
    if not os.path.exists(item_root_path):
        os.makedirs(item_root_path)
    return item_root_path


def get_item_temp_path():
    """
    获取临时文件夹路径（TEMP_FOLDER）。
    若目录不存在则自动创建。
    :return: 临时文件夹路径字符串
    """
    from flask import current_app as app

    tmp_path = app.config.get("TEMP_FOLDER") or "temp"
    if not os.path.exists(tmp_path):
        try:
            os.makedirs(tmp_path)
        except FileExistsError:
            ...

    # 返回
    return tmp_path


def get_upload_item_root_path():
    """
    获取上传文件的保存根目录路径（UPLOAD_FOLDER）。
    若目录不存在则自动创建。
    :return: 上传文件夹路径字符串
    """
    from flask import current_app as app

    item_root_path = app.config.get("UPLOAD_FOLDER") or "upload_files"
    if not os.path.exists(item_root_path):
        try:
            os.makedirs(item_root_path)
        except FileExistsError:
            ...
    return item_root_path


def create_temp_file_path(extension):
    """
    创建临时文件路径，文件名包含时间戳和进程ID。
    :param extension: 文件扩展名，默认为"wav"
    :return: 临时文件完整路径字符串
    """
    return os.path.join(
        get_item_temp_path(), str(time.time()) + f"_{os.getpid()}" + "." + extension
    )


def create_upload_file_path(extension):
    """
    创建上传文件路径，文件名包含时间戳和进程ID。
    :param extension: 文件扩展名，默认为"wav"
    :return: 上传文件完整路径字符串
    """
    return os.path.join(
        get_upload_item_root_path(),
        str(time.time()) + f"_{os.getpid()}" + "." + extension,
    )


def get_file_link(file_path, file_link_prefix=None, remove_path_prefix=None):
    """
    获取文件的外网访问链接。
    :param file_path: 文件相对路径
    :param file_link_prefix: 指定的外网访问前缀（如http://host:port/）
    :param remove_path_prefix: 要删除的相对路径前缀（如"items/"）
    :return: 文件外网访问URL字符串
    """
    from flask import current_app as app

    file_link_prefix = file_link_prefix or app.config.get("FILE_SERVICE_PREFIX", None)

    # 没有指定文件服务前缀的默认使用当前服务的地址
    if not file_link_prefix and has_request_context():
        file_link_prefix = request.host_url

    rel_file_path = file_path  # 相对路径
    if (
        remove_path_prefix
        and file_path.startswith(remove_path_prefix)
        and file_link_prefix != request.host_url
    ):
        rel_file_path = file_path.replace(remove_path_prefix, "", 1)

    # 拼接
    file_link = urllib.parse.urljoin(file_link_prefix, rel_file_path)

    # 返回
    return file_link


def file_to_base64(file_path: str) -> str:
    """
    将文件内容转换为Base64编码字符串。
    :param file_path: 文件路径
    :return: Base64编码字符串
    """
    with open(file_path, "rb") as file:
        file_data = file.read()
        base64_encoded_data = base64.b64encode(file_data)
        base64_message = base64_encoded_data.decode("utf-8")
        return base64_message


def zip_path(path, result_path):
    """
    压缩指定文件夹为zip文件。
    :param path: 需要压缩的文件夹路径
    :param result_path: 生成的zip文件路径
    :return: 生成的zip文件路径
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
