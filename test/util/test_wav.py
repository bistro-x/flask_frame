from ...util.wav import vad_cut


def test_vad_cut():
    sub_items, framerate = vad_cut("./items_tmp/0000369.18.wav", "./items_tmp", audio_rate=16000, min_audio_second=0.01)
    print("len:" + str(len(sub_items)))
