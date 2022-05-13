# -*- coding: UTF-8 -*-

import difflib


def compute_edit_distance(base_text: str, text: str) -> int:
    """
    结算编辑距离
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
    结算文本相似度
    """

    return 1 - compute_edit_distance(base_text, text) / max(
        len(base_text), len(text))
