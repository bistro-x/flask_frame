# -*- coding: UTF-8 -*-
import filetype
from pydub.utils import mediainfo

from frame.file.audio import get_file_info_audio, is_audio


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
        print('Cannot guess file type!')
        return

    result = {
        "mimetype": kind.mime,
        "ext": kind.extension
    }

    if is_audio(kind.extension):
        audio_info = get_file_info_audio(file_path)
        result = {**audio_info, **result, "type": FileType.audio}

    return {**mediainfo(file_path), **result}
