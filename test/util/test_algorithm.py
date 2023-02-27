# -*- coding:utf-8 -*-
from src.flask_frame.util.algorithm import get_asr_report


def test_get_asr_report():
    result = get_asr_report(
        [{"begin_time": 0, "end_time": 4, "text": "测试内容"}],
        [{"begin_time": 0, "end_time": 4, "text": "测信息内容2"}],
    )
    print(result)
