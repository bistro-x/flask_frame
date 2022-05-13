# coding=utf-8
import os
import shutil
import time
import wave
from math import log

import ffmpeg
import numpy as np
from pydub import AudioSegment

from frame.file import get_file_info
from frame.http.exception import ResourceError


def get_wav_info(wav_path):
    """
    获取 wave 文件信息
    :param wav_path: 文件路径
    """
    with wave.open(wav_path, "rb") as f:
        params = f.getparams()
        # print(params)
    return params


def cut_wav(
    wave_data,
    begin,
    end,
    nchannels,
    sampwidth,
    framerate,
    save_path=None,
    file_save_path=None,
):
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
    file_name = file_save_path or os.path.join(
        save_path,
        "%s_%s.wav" % (round(begin * 1000 / framerate), round(end * 1000 / framerate)),
    )
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
        begin_time = 44
        end_time = begin_time + interval
        wav_data = file.readframes(nframes)
        wave_data = np.fromstring(wav_data, dtype=np.int16)

        # 切割
        while end_time < len(wave_data):
            result.append(
                cut_wav(
                    wave_data,
                    begin_time,
                    end_time,
                    nchannels,
                    sampwidth,
                    framerate,
                    save_path,
                )
            )
            begin_time = end_time + 1
            end_time = begin_time + interval

        # 最后一段
        result.append(
            cut_wav(
                wave_data,
                begin_time,
                len(wave_data),
                nchannels,
                sampwidth,
                framerate,
                save_path,
            )
        )

    # 返回
    return result


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

    avg_en = avg_en / ((end - begin) or 1)
    return avg_en


def get_ground_avg(arr, begin, end):
    """
    获取底噪量
    :param arr: 数据组
    :param begin: 开始位置
    :param end: 结束位置
    :return: 底噪音调
    """
    handle_data = abs(arr[begin:end])
    no_valid_avg = handle_data.sum() / handle_data.shape[0] / 100  # 无效段落的平均

    valid_arr = handle_data[handle_data > no_valid_avg]  # 有效音频，有音量

    audio_avg = valid_arr.sum() / valid_arr.shape[0] / 2  # 二分之一的音频大小
    abs_below_avg_arr = valid_arr[valid_arr < audio_avg]  # 小音量数据

    # 取得小音量的平均值
    avg_en = 0
    if abs_below_avg_arr.shape[0]:
        avg_en = abs_below_avg_arr.sum() / abs_below_avg_arr.shape[0]

    # 返回
    return avg_en


def convert_to_wav(
    file_path,
    save_path,
    file_name=None,
    audio_rate=None,
    sound_track=None,
    bits_per_raw_sample=None,
):
    """
    音频文件为 wave 文件
    :param file_path: 文件路径
    :param save_path: 保存路径
    :param file_name: 文件名
    :param audio_rate: 音频采样率
    :param sound_track: 声道信息 1就是单声道，2就是立体声
    :param bits_per_raw_sample: 采样位数
    :return: 转换后的wav文件路径

    """
    if not os.path.exists(file_path):
        raise ResourceError(f"{file_path}文件不存在！")

    # 读取数据
    temp_wave_path = os.path.join(save_path, file_name or str(time.time()) + ".wav")
    if os.path.splitext(file_path)[-1].lower() == ".pcm":
        stream = ffmpeg.input(file_path, f="s16le", ar=audio_rate)
    else:
        stream = ffmpeg.input(file_path)

    # 处理参数
    param = {
        "ar": audio_rate,
        "ac": sound_track,
        "bits_per_raw_sample": bits_per_raw_sample,
    }
    for key in list(param.keys()):
        if not param.get(key):
            param.pop(key)

    stream = ffmpeg.output(stream, temp_wave_path, **param)
    ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, overwrite_output=True)
    return temp_wave_path


def wav_standardized(file_path, result_path, framerate=None):
    """
    根据系统要求 标准化音频
    不做任何采样率或者声道的修改，只是为了修正某些特殊情况下 无法正常读取音频的问题
    :param file_path:
    :param result_path:
    :param framerate:
    :return:
    """
    import ffmpeg

    if os.path.splitext(file_path)[-1].lower() == ".pcm":
        stream = ffmpeg.input(
            file_path,
            f="s16le",
            ar=framerate,
            # todo ac 是声道数 需指定
            ac=1,
        )
        stream = ffmpeg.output(stream, result_path)
        ffmpeg.run(
            stream, capture_stdout=True, capture_stderr=True, overwrite_output=True
        )
    else:
        item_file_info = get_file_info(file_path)
        if (
            item_file_info
            and item_file_info.get("codec_name") == "pcm_s16le"
            and item_file_info.get("sample_rate") == str(framerate)
        ):
            shutil.copy(file_path, result_path)
        else:
            stream = ffmpeg.input(file_path)
            stream = ffmpeg.output(stream, result_path)
            ffmpeg.run(
                stream, capture_stdout=True, capture_stderr=True, overwrite_output=True
            )


def vad_cut(
    wave_path,
    save_path,
    audio_rate=16000,
    min_audio_millisecond=200,
    min_silent_millisecond=500,
    sound_track=1,
):
    """
    根据音量进行断句
    :param wave_path: 音频文件
    :param save_path: 保存路径
    :param audio_rate: 音频采样率
    :param min_audio_millisecond: 最小语音毫秒数
    :param min_silent_millisecond: 最小间隔长度
    :param sound_track: 声道信息 1就是单声道，2就是立体声
    :return:
    """

    # 单位转换
    min_audio_second = min_audio_millisecond / 1000
    min_silent_second = min_silent_millisecond / 1000

    # 读取数据
    temp_wave_path = convert_to_wav(
        wave_path, save_path, audio_rate=audio_rate, sound_track=sound_track
    )

    # 切割
    try:
        file_obj = AudioSegment.from_file(temp_wave_path)
        with wave.open(temp_wave_path) as file:
            nchannels, sampwidth, framerate, nframes = file.getparams()[:4]
            interval_step = int(framerate / 50)  # 检测间隔
            str_data = file.readframes(nframes)
            wave_data = np.fromstring(str_data, dtype=np.int16)
    except wave.Error as e:  # parent of IOError, OSError *and* WindowsError where available
        message = "vad_cut file: " + wave_path + "  error: " + str(e)
        raise Exception(message)

    # 切断
    items = []
    start = None
    end = None
    current_check = 0  # 当前位置

    ground_avg = get_ground_avg(wave_data, 0, wave_data.shape[0])  # 底噪

    silent_length = 0
    while current_check + interval_step < wave_data.shape[0]:
        interval_avg = volume_ave(
            wave_data, current_check, current_check + interval_step
        )  # 平均音量

        # 音频大于1秒，并且底噪大于音量的80%
        if ground_avg > interval_avg * 0.5 and file_obj.duration_seconds > 2:
            # 还未说话
            if start is None:
                current_check = current_check + interval_step
                continue

            # 静默
            silent_length += interval_step
            silent_second = silent_length / framerate  # 静默秒数

            # 说话段落
            if (
                end
                and ((end - start) / framerate) >= min_audio_second
                and silent_second >= min_silent_second
            ):
                path = cut_wav(
                    wave_data, start, end, nchannels, sampwidth, framerate, save_path
                )
                item = {
                    "begin_time": int(start * 1000 / framerate),
                    "end_time": int(end * 1000 / framerate),
                    "path": path,
                }
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
        path = cut_wav(
            wave_data, start, end - 1, nchannels, sampwidth, framerate, save_path
        )
        item = {
            "begin_time": int(start * 1000 / framerate),
            "end_time": int(end * 1000 / framerate)
            if end / framerate < file_obj.duration_seconds
            else int(file_obj.duration_seconds * 1000),
            "path": path,
        }
        items.append(item)

    return items, framerate


def get_wav_dBV(data=None, wav=None, rms=None):
    """
    获取 wav 音频dBV分贝数
    dBV = log(rms, 10) * 20
    :param data: 文件文件二进制
    :param wav : 文件路径或AudioSegment对象
    :param rms : 音频文件rms
    :return wav 音频的dBV分贝数
    """
    if data:
        if isinstance(data, bytes):
            rms = AudioSegment(data=data).rms
    if wav:
        if not isinstance(wav, AudioSegment):
            wav = AudioSegment.from_file(wav)
        rms = wav.rms

    return log(rms, 10) * 20
