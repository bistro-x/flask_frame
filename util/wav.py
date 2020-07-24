# coding=utf-8
import os
import wave

import ffmpeg
import numpy as np
from pydub import AudioSegment


def get_wav_info(wav_path):
    """
    获取 wave 文件信息
    :param wav_path: 文件路径
    """
    with wave.open(wav_path, "rb") as f:
        params = f.getparams()
        # print(params)
    return params


def check_wav_format(wav_path):
    """
    检测是否是单声道
    :param wav_path: 文件路径
    """

    params = get_wav_info(wav_path)
    # 判断音频是否是单声道
    if params.nchannels != 1:
        return -1
    else:
        # 返回音频频率 16000 或 8000 是支持的，其他频率无法支持
        return params.framerate


def cut_wav_by_length(file, save_path, length=100):
    """
    根据音频长度切割音频
    :param file: 切割文件
    :param save_path: 保存路径
    :param length: 每段切割长度
    :return: 切割的文件
    """
    result = []

    # 创建目录
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    with wave.open(file) as file:
        nchannels, sampwidth, framerate, nframes = file.getparams()[:4]
        interval = int(framerate * (length / 1000))

        # 初始化数据
        start_time = 44
        end_time = start_time + interval
        wav_data = file.readframes(nframes)
        wave_data = np.fromstring(wav_data, dtype=np.int16)

        # 切割
        while end_time < len(wave_data):
            result.append(cut_wav(wave_data, start_time, end_time, nchannels, sampwidth, framerate, save_path))
            start_time = end_time + 1
            end_time = start_time + interval

        # 最后一段
        result.append(
            cut_wav(wave_data, start_time, len(wave_data), nchannels, sampwidth, framerate, save_path))

    # 返回
    return result


def cut_wav(wave_data, begin, end, nchannels, sampwidth, framerate, save_path=None, file_save_path=None):
    """
    根据音频 开始结束 进行音频切割
    :param wave_data:
    :param begin:
    :param end:
    :param nchannels:
    :param sampwidth:
    :param framerate:
    :param save_path:
    :return:
    """
    # print("cut_wav: %s----%s len:%s" % (begin,end,(end-begin)/16000))
    file_name = file_save_path or os.path.join(save_path,
                                               "%s_%s.wav" % (
                                                   round(begin * 1000 / framerate), round(end * 1000 / framerate)))
    temp_dataTemp = wave_data[begin:end]
    temp_dataTemp.shape = 1, -1
    temp_dataTemp = temp_dataTemp.astype(np.short)  # 打开WAV文档
    with wave.open(r"" + file_name, "wb") as f:
        # 配置声道数、量化位数和取样频率
        f.setnchannels(nchannels)
        f.setsampwidth(sampwidth)
        f.setframerate(framerate)
        # 将wav_data转换为二进制数据写入文件
        f.writeframes(temp_dataTemp.tostring())

    return file_name


def volume_ave(arr, begin, end):
    """
    获取当前数据的平均音调
    :param arr: 数据组
    :param begin: 开始位置
    :param end: 结束位置
    :return: 平均音调
    """
    avg_en = 0
    for i in range(begin, end):
        avg_en = avg_en + abs(arr[i])

    avg_en = avg_en / (end - begin)
    return avg_en


def get_ground_avg(arr, begin, end):
    """
    获取底噪量
    :param arr: 数据组
    :param begin: 开始位置
    :param end: 结束位置
    :return: 底噪音调
    """

    audio_avg = volume_ave(arr, begin, end) / 2

    avg_en = 0
    add_num = 0
    for i in range(begin, end):
        value = abs(arr[i])
        if value < audio_avg:
            avg_en += value
            add_num += 1

    avg_en = avg_en if add_num == 0 else avg_en / add_num
    return avg_en


def vad_cut(wave_path, save_path, audio_rate=16000, min_audio_second=0.2, min_silent_second=0.5):
    """
    根据音量进行断句
    :param wave_path: 音频文件
    :param save_path: 保存路径
    :param audio_rate: 音频采样率
    :param min_audio_second: 最小语音秒数
    :param min_silent_second: 最小间隔长度
    :return:
    """

    # 读取数据
    temp_wave_path = os.path.join(save_path, "audio.wav")
    stream = ffmpeg.input(wave_path)
    stream = ffmpeg.output(stream, temp_wave_path, ar=audio_rate)
    ffmpeg.run(stream, overwrite_output=True)
    file_obj = AudioSegment.from_file(temp_wave_path)

    try:
        with wave.open(temp_wave_path) as file:
            nchannels, sampwidth, framerate, nframes = file.getparams()[:4]
            interval_step = int(framerate / 50)  # 检测间隔
            str_data = file.readframes(nframes)
            wave_data = np.fromstring(str_data, dtype=np.int16)
    except wave.Error as e:  # parent of IOError, OSError *and* WindowsError where available
        message = "vad_cut file: " + wave_path + "  error: " + str(e)
        raise Exception(message)

        return None, None

    # 切断
    items = []
    start = None
    end = None
    current_check = 0  # 当前位置

    ground_avg = get_ground_avg(wave_data, 0, wave_data.shape[0])  # 底噪

    silent_length = 0
    while current_check < wave_data.shape[0] - interval_step:
        interval_avg = volume_ave(wave_data, current_check, current_check + interval_step)  # 平均音量

        # 音频大于1秒，并且底噪大于音量的80%
        if ground_avg > interval_avg * 0.8 and file_obj.duration_seconds > 2:
            # 还未说话
            if not start:
                current_check = current_check + interval_step
                continue

            # 静默
            silent_length += interval_step
            silent_second = silent_length / framerate  # 静默秒数

            # 说话段落
            if end and ((end - start) / framerate) >= min_audio_second and silent_second >= min_silent_second:
                path = cut_wav(wave_data, start, end, nchannels, sampwidth, framerate, save_path)
                item = {"start_time": int(start * 1000 / framerate),
                        "end_time": int(end * 1000 / framerate), "path": path}
                items.append(item)
                start = None
                end = None
                silent_length = 0

            # 没有行程一个最小单位语句，又停顿太久
            if silent_second >= min_silent_second:
                start = None
                end = None
                silent_length = 0
                current_check = current_check + interval_step
                continue

        # 有声音
        else:
            # 调整新的结尾
            if start is not None:
                end = current_check or end
                silent_length = 0

            start = start if start is not None else current_check

        if current_check >= wave_data.shape[0] - interval_step:
            break

        current_check = current_check + interval_step


        # 结尾
    end = wave_data.shape[0]
    if start is not None and (end - start) / framerate > min_audio_second:
        path = cut_wav(wave_data, start, end, nchannels, sampwidth, framerate, save_path)
        item = {"start_time": int(start * 1000 / framerate),
                "end_time": int(end * 1000 / framerate), "path": path}
        items.append(item)

    return items, framerate
