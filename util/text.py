# -*- coding: UTF-8 -*-
import string

from zhon import hanzi
import re


def tel_convert(sentences):
    """电话转换"""
    telRegex = re.compile(r'''(
        (\d{3}|\(\d{3}\))?              # area code
        (\s|-|\.)?                      # separator
        (\d{3})                         # first 3 digits
        (\s|-|\.)                       # separator
        (\d{4})                         # last 4 digits
        (\s*(ext|x|ext\.)\s*(\d{2,5}))? # extension
        )''', re.VERBOSE)

    telRegex2 = re.compile(r'''(
        (\d{4}|\(\d{4}\))?              # area code
        (\s|-|\.)?                      # separator
        (\d{4})                         # first 3 digits
        (\s|-|\.)                       # separator
        (\d{4})                         # last 4 digits
        )''', re.VERBOSE)

    telRegex3 = re.compile(r'''(
        (?<=\D)1
        [34789]
        (\d{9})
    )''', re.VERBOSE)

    phone_find = telRegex3.findall(sentences)
    for groups in phone_find:
        sentences = sentences.replace(groups[0], digital_convert(groups[0]))
    phone_find = telRegex.findall(sentences)
    for groups in phone_find:
        sentences = sentences.replace(groups[0], digital_convert(groups[0]))
    phone_find = telRegex2.findall(sentences)
    for groups in phone_find:
        sentences = sentences.replace(groups[0], digital_convert(groups[0]))
    return sentences


def digital_convert(sentences):
    if not sentences:
        return sentences
    mapping = ("零", "一", "二", "三", "四", "五", "六", "七", "八", "九")
    for i in range(10):
        sentences = sentences.replace(str(i), mapping[i], -1)
    return sentences


def number_convert(num):
    if not num or not isinstance(num, int):
        return digital_convert(num)
    mapping = (
        '零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五', '十六', '十七',
        '十八', '十九')
    po = ('十', '百', '千', "万")
    tenM = 10 ** 8
    if num < 0 or num >= tenM:
        return digital_convert(str(num))
    if num < 20:
        return mapping[num]
    else:
        lst = []
        while num >= 10:
            lst.append(num % 10)
            num = num / 10
        lst.append(num)
        c = len(lst)  # 位数
        result = u''

        for idx, val in enumerate(lst):
            val = int(val)
            true_idx = idx % 4
            if val != 0:
                result += mapping[val] if idx == 0 else po[true_idx - 1] + mapping[val]
                if idx < c - 1 and lst[idx + 1] == 0:
                    result += u'零'
        return result[::-1]


def stock_code_convert(sentences):
    """股票代码转换"""
    stockRegex = re.compile(r'''
    [\(|（]|[代码]
    \d{6}
    [\)|）]?
    ''', re.VERBOSE)
    stockRegex2 = re.compile(r'''
    (?<=[\D])0
    \d{5}
    ''', re.VERBOSE)
    stock_find = stockRegex.findall(sentences)
    for groups in stock_find:
        sentences = sentences.replace(groups, digital_convert(groups))
    stock_find = stockRegex2.findall(sentences)
    for groups in stock_find:
        sentences = sentences.replace(groups, digital_convert(groups))
    return sentences


def email_convert(sentences):
    """邮箱转换"""
    emailRegex = re.compile(r'''(
        [a-zA-Z0-9._%+-]+
        @
        [a-zA-Z0-9.-]+
        (\.[a-zA-Z]{2,4})
    )''', re.VERBOSE)

    email_find = emailRegex.findall(sentences)
    for groups in email_find:
        email = digital_convert(groups[0].upper())
        email = email.replace("@", "艾特", -1)
        sentences = sentences.replace(groups[0], email)
        sentences = punctuation_convert(sentences)
    return sentences


def punctuation_convert(sentences):
    """替换掉没有歧义的符号"""
    return sentences.replace("+", "加", -1).replace("*ST", "星号ST", -1).replace("*键", "星号键", -1).replace("*", "星", -1) \
        .replace("#键", "井号键", -1).replace("#", "井", -1).replace(".", "点", -1).replace("$", "美元", -1) \
        .replace("¥", "人民币", -1).replace("=", "等于", -1)


def remove_punctuation(sentences):
    """去除所有标点符号"""
    if not sentences:
        return sentences

    result = sentences.strip()
    result = re.sub(f"[{hanzi.punctuation}]", "", result)
    result = re.sub(f"[{string.punctuation}]", "", result)
    return result


def time_convert(sentences):
    """时间替换"""
    timeRegex = re.compile(r'''(
        ((?<=[\D])\d{4}|^\d{4})?
        (\s|\/|[年])?
        ((?<=\D)\d{1,2})
        (\s|\/|[月])
        ((?<=\D)\d{1,2})?
        (\s|\ |\/|[日])?
        (\d{1,2})?
        (\s|:|[时点])?
        (\d{1,2})?
        (\s|:|[分])?
        (\d{1,2})?
        ([秒])?
    )''', re.VERBOSE)

    mapping = ("", "年", "月", "日", "时", "分", "秒")

    result = u''
    time_find = timeRegex.findall(sentences)
    for groups in time_find:
        for idx, group in enumerate(groups):
            if not group or idx == 0:
                continue
            if idx % 2 == 1:
                result += digital_convert(group) if idx == 1 else number_convert(int(group))
            else:
                result += mapping[int(idx / 2)]
        sentences = sentences.replace(groups[0], result, -1)

    return sentences


def percent_convent(sentences):
    """百分比替换"""
    percentRegex = re.compile(r'''(
        (\d+)
        (\.\d+)?
        %
    )''', re.VERBOSE)
    percent_find = percentRegex.findall(sentences)
    result = u'百分之'
    for groups in percent_find:
        result += number_convert(int(groups[1]))
        if groups[2]:
            point_num = str(groups[2]).replace(".", "点")
            result += digital_convert(point_num)
            sentences = sentences.replace(groups[0], result)
    return sentences


def hyphen_convent(sentences):
    hyphenRegex = re.compile(r'''(
           (\d?|[年月日时分秒点])
           -
           (\d?|[一二三四五六七八九十])
       )''', re.VERBOSE)
    hyphen_find = hyphenRegex.findall(sentences)
    for groups in hyphen_find:
        sentences = sentences.replace(groups[0],
                                      str(groups[0]).replace("-", "到"))
        if groups[2]:
            sentences = sentences.replace(groups[2],
                                          number_convert(int(groups[2])))
    return sentences


def text_convent(text):

    # 邮箱转换
    text = email_convert(text)
    # 电话转换
    text = tel_convert(text)

    text = stock_code_convert(text)

    # 日期转换
    text = time_convert(text)

    text = hyphen_convent(text)

    text = percent_convent(text)

    # 替换掉没有歧义的符号
    text = punctuation_convert(text)

    numbers = re.compile(r'\d+').findall(text)
    for number in numbers:
        text = text.replace(number, number_convert(int(number)))

    # 去掉无意义符号
    return remove_punctuation(text)

