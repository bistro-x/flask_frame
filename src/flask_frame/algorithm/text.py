#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# 文本算法相关工具
import difflib

def compute_edit_distance(base_text: str, text: str) -> int:
    """
    计算编辑距离（Levenshtein距离），用于衡量两个字符串的差异。
    :param base_text: 原始文本
    :param text: 比较文本
    :return: 编辑距离
    """
    leven_cost = 0
    s = difflib.SequenceMatcher(None, base_text, text)
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'replace':
            leven_cost += max(i2 - i1, j2 - j1)
        elif tag == 'insert':
            leven_cost += (j2 - j1)
        elif tag == 'delete':
            leven_cost += (i2 - i1)
    return leven_cost

def compute_compatibility(base_text: str, text: str) -> int:
    """
    计算文本相似度，返回值越接近1表示越相似。
    :param base_text: 原始文本
    :param text: 比较文本
    :return: 相似度分数（0~1）
    """
    return 1 - compute_edit_distance(base_text, text) / max(len(base_text), len(text))
