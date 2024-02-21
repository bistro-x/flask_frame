# -*- coding:utf-8 -*-
import os
import re

import chardet
import numpy as np


def enum_path_files(path):
    """遍历目录（子目录），返回所有文件路径"""

    path_len = len(path)
    file_paths = []
    if not os.path.isdir(path):
        print('Error:"', path, '" is not a directory or does not exist.')
        return
    list_dirs = os.walk(path)
    for root, dirs, files in list_dirs:
        for f in files:
            file_paths.append(os.path.join(root, f)[path_len + 1:])
    return file_paths


def standardized_file_encode(path):
    """标准化文件编码"""

    with open(path, "rb") as f:
        data = f.read()
    if len(data) == 0:
        return
    res = chardet.detect(data)
    if res["encoding"] == "GB2312":
        res["encoding"] = "GBK"
    with open(os.path.join(path), "w", encoding="utf-8") as file:
        line = str(data, encoding=res["encoding"])
        line = line.replace("\n", "").replace("\r", "")
        file.write(line)


def standardized_mark_file(path, filename):
    new_filename = filename.replace("_inspection", "").replace("_mark", "")
    if new_filename != filename:
        os.rename(os.path.join(path, filename),
                  os.path.join(path, new_filename))
    return path, new_filename


def num_to_char(num):
    """数字转中文"""
    num = str(num)
    num = num.replace("1_", "幺")
    new_str = ""
    num_dict = {"0": u"零", "1": u"一", "2": u"二", "3": u"三", "4": u"四", "5": u"五", "6": u"六", "7": u"七", "8": u"八",
                "9": u"九"}
    list_num = list(num)

    shu = []
    for i in list_num:
        # print(num_dict[i])
        try:
            tmp = num_dict[i]
        except:
            tmp = i
        shu.append(tmp)
    new_str = "".join(shu)

    return new_str


def init(origin_str, compare_str):
    m = np.empty((len(origin_str) + 1, len(compare_str) + 1))
    m[:] = np.inf
    # initializing the first row
    m[0] = np.arange(m.shape[1])
    # initializing the first column
    counter = 0
    for i in m:
        i[0] = counter
        counter += 1
    return m


def str_compare(origin_str, compare_str):
    """
    计算准确率等数据
    :param origin_str: 正确的原始数据
    :param compare_str: 要比对的数据
    :return:
    """
    if origin_str == '' and compare_str == '':
        return {
            "mark_different": "", "length_different": 0, "origin_str_valid": "",
            "mark_same": "", "compare_str_valid": "",
            "accuracy": 1,
            "ratio_insert": 0,
            "ratio_delete": 0,
            "ratio_update": 0}

    origin_str = re.sub('[,.，。 \n?!？！]', '', origin_str)
    compare_str = re.sub('[,.，。 \n?!？！]', '', compare_str)

    # INITIALIZATION
    m = init(origin_str, compare_str)
    for i in range(1, m.shape[0]):
        for j in range(1, m.shape[1]):

            # first condition : i is an insertion
            con1 = m[i - 1, j] + 1

            # second condition : j is a deletion
            con2 = m[i, j - 1] + 1

            # third condition : i and j are a substitution
            if origin_str[i - 1] == compare_str[j - 1]:
                # if same letters, we add nothing
                con3 = m[i - 1, j - 1]
            else:
                # if different letters, we add one
                con3 = m[i - 1, j - 1] + 1

            # assign minimum value
            m[i][j] = min(con1, con2, con3)

    # Alignment
    zero = 0
    mm = np.c_[[zero] * len(m[:]), m]
    mmm = np.r_[[[zero] * len(mm[1, :])], mm]
    back_matrix = [[' ' for y in range(len(compare_str) + 2)] for x in range(len(origin_str) + 2)]
    back_matrix[1][1] = 0

    for i in range(2, len(origin_str) + 2):
        back_matrix[i][0] = origin_str[i - 2]
    for j in range(2, len(compare_str) + 2):
        back_matrix[0][j] = compare_str[j - 2]

    for i in range(2, len(origin_str) + 2):
        back_matrix[i][1] = '|'

    for j in range(2, len(compare_str) + 2):
        back_matrix[1][j] = '-'

    for i in range(2, len(origin_str) + 2):
        for j in range(2, len(compare_str) + 2):
            vertical = mmm[i - 1][j] + 1
            horizontal = mmm[i][j - 1] + 1
            if origin_str[i - 2] == compare_str[j - 2]:
                diagonal = mmm[i - 1][j - 1]
            else:
                diagonal = mmm[i - 1][j - 1] + 1

            mindist = min(diagonal, vertical, horizontal)
            mmm[i][j] = mindist

            if mindist == diagonal:
                back_matrix[i][j] = 'bn'
            elif mindist == vertical:
                back_matrix[i][j] = '|'
            else:
                back_matrix[i][j] = '-'

    ss1 = ""
    ss2 = ""
    mark_same = ""
    mark_different = ''
    i = len(origin_str) + 1
    j = len(compare_str) + 1
    while not (i == 1 and j == 1):
        c = back_matrix[i][j]
        if c == '|':
            ss1 += origin_str[i - 2] + ' '
            ss2 += '**' + ' '
            mark_same += ' ' + '  '
            mark_different += 'D' + '  '
            i = i - 1
        elif c == 'bn':
            ss1 += origin_str[i - 2] + ' '
            ss2 += compare_str[j - 2] + ' '
            if origin_str[i - 2] == compare_str[j - 2]:
                mark_same += '|' + '  '
                mark_different += ' ' + '  '
            else:
                mark_same += ' ' + '  '
                mark_different += 'S' + '  '
            i = i - 1
            j = j - 1
        else:
            ss1 += '**' + ' '
            ss2 += compare_str[j - 2] + ' '
            mark_same += ' ' + '  '
            mark_different += 'I' + '  '
            j = j - 1

    mark_different, m, origin_str_valid, mark_same, compare_str_valid = mark_different[::-1], m[m.shape[0] - 1][
        m.shape[1] - 1], ss1[::-1], mark_same[::-1], ss2[::-1]

    length_ref = len(origin_str_valid.replace(" ", '').replace("**", ''))

    ratio_insert = mark_different.count('I') / (length_ref or 1)
    ratio_delete = mark_different.count('D') / (length_ref or 1)
    ratio_update = mark_different.count('S') / (length_ref or 1)

    length_different = int(m) or 0
    accuracy = 1 - (length_different / (length_ref or 1))

    return {
        "mark_different": mark_different, "length_different": length_different, "length_ref": length_ref,
        "origin_str_valid": origin_str_valid,
        "mark_same": mark_same, "compare_str_valid": compare_str_valid,
        "accuracy": accuracy,
        "ratio_insert": ratio_insert,
        "ratio_delete": ratio_delete,
        "ratio_update": ratio_update}


def batch_row_compare(origin_file, compare_file):
    """批量计算:多行比较"""

    total_str_length = 0
    total_accuracy = 0  # 准确率
    total_ratio_insert = 0  # 插入率
    total_ratio_delete = 0  # 删除率
    total_ratio_update = 0  # 替换率

    with open(origin_file, 'r', encoding='UTF-8') as a, open(compare_file, 'r', encoding='UTF-8') as b:
        origin_text = a.readlines()
        compare_text = b.readlines()

        for i in range(len(origin_text)):
            # 去除标点符号

            origin_str = num_to_char(origin_text[i])
            compare_str = num_to_char(compare_text[i])

            compare_result = str_compare(origin_str, compare_str)
            ratio_insert, length_different, ratio_delete, ratio_update, accuracy, mark_different, mark_same = compare_result.get(
                "compare_result"), compare_result.get(
                "length_different"), compare_result.get("ratio_delete"), compare_result.get(
                "ratio_update"), compare_result.get("accuracy"), compare_result.get(
                "mark_different"), compare_result.get("mark_same")

            total_str_length += len(origin_str)
            total_accuracy = total_accuracy + accuracy * len(origin_str)
            total_ratio_insert = total_ratio_insert + ratio_insert * len(origin_str)
            total_ratio_delete = total_ratio_delete + ratio_delete * len(origin_str)
            total_ratio_update = total_ratio_update + ratio_update * len(origin_str)

            print({"准确率": accuracy, "原字符串": origin_str, "比对字符串": compare_str, "mark_same": mark_same,
                   "mark_different": mark_different,
                   "origin_str": origin_str, "compare_str": compare_str,
                   "插入率": ratio_insert, "删除率": ratio_delete, "替换率": ratio_update})

    print("总字数:%s ,平均准确率：%s ，平均插入率：%s ，平均删除率：%s，平均替换率：%s " % (total_str_length, total_accuracy / total_str_length,
                                                              total_ratio_insert / total_str_length,
                                                              total_ratio_delete / total_str_length,
                                                              total_ratio_update / total_str_length))


def batch_file_compare(origin_dir, compare_dir):
    """
    batch file compare
    """

    total_str_length = 0
    total_accuracy = 0
    total_ratio_insert = 0  # 插入率
    total_ratio_delete = 0  # 删除率
    total_ratio_update = 0  # 替换率

    res = []

    file_paths = enum_path_files(origin_dir)
    for file_path in file_paths:
        print(file_path)
        origin_dir, file_path = standardized_mark_file(
            origin_dir, file_path)
        standardized_file_encode(os.path.join(origin_dir, file_path))
        origin_str = open(os.path.join(origin_dir, file_path),
                          'r', encoding="utf-8").read()
        standardized_file_encode(os.path.join(compare_dir, file_path))
        hyp_path = os.path.join(compare_dir, file_path)
        compare_str = open(hyp_path, 'r', encoding="utf-8").read()

        origin_str = num_to_char(origin_str)
        compare_str = num_to_char(compare_str)

        # get result
        compare_result = str_compare(origin_str, compare_str)
        ratio_insert, length_different, ratio_delete, ratio_update, accuracy, mark_different, mark_same = compare_result.get(
            "ratio_insert"), compare_result.get(
            "length_different"), compare_result.get("ratio_delete"), compare_result.get(
            "ratio_update"), compare_result.get("accuracy"), compare_result.get(
            "mark_different"), compare_result.get("mark_same")

        #  get total value
        total_str_length += len(origin_str)
        total_accuracy = total_accuracy + accuracy * len(origin_str)
        total_ratio_insert = total_ratio_insert + ratio_insert * len(origin_str)
        total_ratio_delete = total_ratio_delete + ratio_delete * len(origin_str)
        total_ratio_update = total_ratio_update + ratio_update * len(origin_str)

        res.append({"filename": os.path.basename(file_path), "accuracy": accuracy,
                    "ratio_insert": ratio_insert, "ratio_delete": ratio_delete, "ratio_update": ratio_update})

    res.append({"filename": "汇总", "accuracy": total_accuracy / total_str_length,
                "ratio_insert": total_ratio_insert / total_str_length,
                "ratio_delete": total_ratio_delete / total_str_length,
                "ratio_update": total_ratio_update / total_str_length})

    print("总字数:%s ,平均准确率：%s ，平均插入率：%s ，平均删除率：%s，平均替换率：%s " % (total_str_length, total_accuracy / total_str_length,
                                                              total_ratio_insert / total_str_length,
                                                              total_ratio_delete / total_str_length,
                                                              total_ratio_update / total_str_length))
    return res


def min_distance(word1: str, word2: str) -> int:
    """
        计算最小编辑距离
    """

    n1 = len(word1)
    n2 = len(word2)
    dp = [[0] * (n2 + 1) for _ in range(n1 + 1)]
    # 第一行
    for j in range(1, n2 + 1):
        dp[0][j] = dp[0][j - 1] + 1
    # 第一列
    for i in range(1, n1 + 1):
        dp[i][0] = dp[i - 1][0] + 1
    for i in range(1, n1 + 1):
        for j in range(1, n2 + 1):
            if word1[i - 1] == word2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(dp[i][j - 1], dp[i - 1][j], dp[i - 1][j - 1]) + 1
    return dp[-1][-1]
