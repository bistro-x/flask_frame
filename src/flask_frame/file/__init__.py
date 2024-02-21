# -*- coding: UTF-8 -*-
import os

import filetype
from pydub.utils import mediainfo

from .audio import get_file_info_audio, is_audio


class FileType:
    audio = "audio"


def get_file_info(file_path):
    """
    统计文件信息
    :param file_path: 文件路径
    :return:
    """
    kind = filetype.guess(file_path)

    if kind is None:
        result = {"ext": os.path.splitext(file_path)[-1].replace(".", "")}
    else:
        result = {"mimetype": kind.mime, "ext": kind.extension}

    media_info = mediainfo(file_path)

    if is_audio(result.get("ext")):
        audio_info = get_file_info_audio(file_path)
        result = {**audio_info, **result, "type": FileType.audio}

        result["framerate"] = (
            result.get("framerate") or media_info.get("sample_rate") or None
        )
        result["framerate"] = (
            int(result["framerate"]) if result["framerate"] else result["framerate"]
        )

    return {**media_info, **result}
