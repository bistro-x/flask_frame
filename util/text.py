# -*- coding: UTF-8 -*-
import string

from zhon import hanzi
import re


def remove_punctuation(text):
    """去除所有标点符号"""
    result = text.strip()
    result = re.sub(f"[{hanzi.punctuation}]", "", result)
    result = re.sub(f"[{string.punctuation}]", "", result)
    return result
