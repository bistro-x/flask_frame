# -*- coding: UTF-8 -*-

"""doc文件操作工具类
"""


import os
import shutil

import mammoth


def docx_convert_to_html(file_path: str, result_path: str):
    """docx 文件 转换成 html 文件

    Args:
        file_path (str): 源文件路径
        result_path (str, optional): 目的文件路径. Defaults to None.

    Returns:
        str: html数据
    """

    convert_image = mammoth.images.inline(ImageWriter(os.path.dirname(result_path)))

    result = mammoth.convert_to_html(file_path, convert_image=convert_image)
    html = result.value  # The generated HTML

    full_html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8"/></head><body>'
        + html
        + "</body></html>"
    )

    # 写文件
    if result_path:
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(full_html)

    return full_html


class ImageWriter(object):
    """图片读写

    Args:
        object (_type_): _description_
    """

    def __init__(self, output_dir):
        self._output_dir = output_dir
        self._image_number = 1

    def __call__(self, element):
        extension = element.content_type.partition("/")[2]
        image_filename = "{0}.{1}".format(self._image_number, extension)
        with open(os.path.join(self._output_dir, image_filename), "wb") as image_dest:
            with element.open() as image_source:
                shutil.copyfileobj(image_source, image_dest)

        self._image_number += 1

        return {"src": image_filename}
