# -*- coding: UTF-8 -*-
import wave
import sndhdr


def is_audio(ext):
    """判断是否是音频"""
    if ext in ["midi", "mp3", 'm4a', 'ogg', 'flac', 'wav', 'amr', 'pcm']:
        return True

    return False


def get_file_info_audio(file_path):
    """
    统计音频文件信息
    :param file_path: 文件路径
    :return: 文件信息
    """
    header = sndhdr.what(file_path)
    if not header:
        return {}

    rate = header.framerate * header.nchannels * header.sampwidth / 8
    return {
        "filetype": header.filetype,  # 文件类型
        "framerate": header.framerate,  # 音频文件的帧率
        "nchannels": header.nchannels,  # 通道数
        "nframes": header.nframes,  # 总帧数
        "sampwidth": header.sampwidth,  # 带宽
        "rate": rate,  # 比特率
        "length": header.nframes / header.framerate * 1000
    }


def get_file_info_wave(file_path):
    """
    统计 wave 信息
    # param file_path 文件路径
    """
    if not file_path:
        return {}

    with wave.open(file_path, "rb") as f:
        nchannels, sampwidth, framerate, nframes, comptype, compname = f.getparams()

        rate = f.getframerate()  # 比特率
        frames = f.getnframes()  #
        original_length = frames / float(rate) * 1000  # 音频长度 毫秒

    return {"original_length": original_length,
            "nchannels": nchannels, "sampwidth": sampwidth, "framerate": framerate,
            "nframes": nframes, "comptype": comptype, "compname": compname}
