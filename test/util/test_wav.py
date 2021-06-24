import os
import time

from ...util.wav import vad_cut


def test_vad_cut():
    for path, dir_list, file_list in os.walk("./frame/test/data/"):
        for file_name in file_list:
            temp_path = os.path.join("./frame/test/data_temp/", file_name)

            if not os.path.exists(temp_path):
                os.makedirs(temp_path)

            sub_items, framerate = vad_cut(os.path.join(path, file_name), temp_path, audio_rate=16000,
                                           min_audio_millisecond=10)
            print("len:" + str(len(sub_items)))
