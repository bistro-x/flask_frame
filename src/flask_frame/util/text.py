# -*- coding: UTF-8 -*-
import json
from datetime import datetime, date
import string
import cn2an
import uuid
from decimal import Decimal

from zhon import hanzi
import re


class AppEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%dT%H:%M:%S.%f")
        if isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def tel_convert(sentences):
    """电话转换"""
    telRegex = re.compile(
        r"""(
        (\d{3}|\(\d{3}\))?              # area code
        (\s|-|\.)?                      # separator
        (\d{3})                         # first 3 digits
        (\s|-|\.)                       # separator
        (\d{4})                         # last 4 digits
        (\s*(ext|x|ext\.)\s*(\d{2,5}))? # extension
        )""",
        re.VERBOSE,
    )

    telRegex2 = re.compile(
        r"""(
        (\d{4}|\(\d{4}\))?              # area code
        (\s|-|\.)?                      # separator
        (\d{4})                         # first 3 digits
        (\s|-|\.)                       # separator
        (\d{4})                         # last 4 digits
        )""",
        re.VERBOSE,
    )

    telRegex3 = re.compile(
        r"""(
        (?<=\D)1
        [34789]
        (\d{9})
    )""",
        re.VERBOSE,
    )

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
        "零",
        "一",
        "二",
        "三",
        "四",
        "五",
        "六",
        "七",
        "八",
        "九",
        "十",
        "十一",
        "十二",
        "十三",
        "十四",
        "十五",
        "十六",
        "十七",
        "十八",
        "十九",
    )
    po = ("十", "百", "千", "万")
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
        result = ""

        for idx, val in enumerate(lst):
            val = int(val)
            true_idx = idx % 4
            if val != 0:
                result += mapping[val] if idx == 0 else po[true_idx - 1] + mapping[val]
                if idx < c - 1 and lst[idx + 1] == 0:
                    result += "零"
        return result[::-1]


def stock_code_convert(sentences):
    """股票代码转换"""
    stockRegex = re.compile(
        r"""
    [\(|（]|[代码]
    \d{6}
    [\)|）]?
    """,
        re.VERBOSE,
    )
    stockRegex2 = re.compile(
        r"""
    (?<=[\D])0
    \d{5}
    """,
        re.VERBOSE,
    )
    stock_find = stockRegex.findall(sentences)
    for groups in stock_find:
        sentences = sentences.replace(groups, digital_convert(groups))
    stock_find = stockRegex2.findall(sentences)
    for groups in stock_find:
        sentences = sentences.replace(groups, digital_convert(groups))
    return sentences


def email_convert(sentences):
    """邮箱转换"""
    emailRegex = re.compile(
        r"""(
        [a-zA-Z0-9._%+-]+
        @
        [a-zA-Z0-9.-]+
        (\.[a-zA-Z]{2,4})
    )""",
        re.VERBOSE,
    )

    email_find = emailRegex.findall(sentences)
    for groups in email_find:
        email = digital_convert(groups[0].upper())
        email = email.replace("@", "艾特", -1)
        sentences = sentences.replace(groups[0], email)
        sentences = punctuation_convert(sentences)
    return sentences


def punctuation_convert(sentences):
    """替换掉没有歧义的符号"""
    return (
        sentences.replace("+", "加", -1)
        .replace("*ST", "星号ST", -1)
        .replace("*键", "星号键", -1)
        .replace("*", "星", -1)
        .replace("#键", "井号键", -1)
        .replace("#", "井", -1)
        .replace(".", "点", -1)
        .replace("$", "美元", -1)
        .replace("¥", "人民币", -1)
        .replace("=", "等于", -1)
    )


def remove_punctuation(sentences, includ_variable=True, replace_text=""):
    """去除标点符号


    Args:
        sentences (str): 处理文本
        includ_variable (bool, optional): 是否去除变量符号. Defaults to True.
        replace_text (str): 去除后替换的文本. Defaults to "".

    Returns:
        _type_: 返回文本
    """

    if not sentences:
        return sentences

    result = sentences.strip()
    result = re.sub(f"[{hanzi.punctuation}]", replace_text, result)
    eng_punctuation = [*string.punctuation]

    if not includ_variable:
        eng_punctuation.remove("{")
        eng_punctuation.remove("}")
        
    for item in eng_punctuation:
        result = result.replace(item, replace_text)

    return result


def time_convert(sentences):
    """时间替换"""
    timeRegex = re.compile(
        r"""(
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
    )""",
        re.VERBOSE,
    )

    mapping = ("", "年", "月", "日", "时", "分", "秒")

    result = ""
    time_find = timeRegex.findall(sentences)
    for groups in time_find:
        for idx, group in enumerate(groups):
            if not group or idx == 0:
                continue
            if idx % 2 == 1:
                result += (
                    digital_convert(group) if idx == 1 else number_convert(int(group))
                )
            else:
                result += mapping[int(idx / 2)]
        sentences = sentences.replace(groups[0], result, -1)

    return sentences


def percent_convent(sentences):
    """百分比替换"""
    percentRegex = re.compile(
        r"""(
        (\d+)
        (\.\d+)?
        %
    )""",
        re.VERBOSE,
    )
    percent_find = percentRegex.findall(sentences)
    result = "百分之"
    for groups in percent_find:
        result += number_convert(int(groups[1]))
        if groups[2]:
            point_num = str(groups[2]).replace(".", "点")
            result += digital_convert(point_num)
            sentences = sentences.replace(groups[0], result)
    return sentences


def hyphen_convent(sentences):
    hyphenRegex = re.compile(
        r"""(
           (\d?|[年月日时分秒点])
           -
           (\d?|[一二三四五六七八九十])
       )""",
        re.VERBOSE,
    )
    hyphen_find = hyphenRegex.findall(sentences)
    for groups in hyphen_find:
        sentences = sentences.replace(groups[0], str(groups[0]).replace("-", "到"))
        if groups[2]:
            sentences = sentences.replace(groups[2], number_convert(int(groups[2])))
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

    numbers = re.compile(r"\d+").findall(text)
    for number in numbers:
        text = text.replace(number, number_convert(int(number)))

    # 去掉无意义符号
    return remove_punctuation(text)


def convert_sentence_chinese_number_to_arabic(sentence, no_convert_words=None):
    """
    对输入的句子进行分词和中文数字替换
    使用hanlp进行分词 doc: https://hanlp.hankcs.com/docs/
    :param sentence:  待转换的句子字符串
    :param no_convert_words:  不处理的字符串
    """
    from ..extension.participle import participle_sentence

    numbers = ["零", "一", "幺", "二", "两", "三", "四", "五", "六", "七", "八", "九", "十"]

    def convert_word_list(word_list: list):
        for index, w in enumerate(word_list):
            if any([(n in w) for n in numbers]):
                w = w.replace("两", "二").replace("幺", "一")
                word_list[index] = convert_chinese_number_to_arabic(w)

    # 对指定字符组合不做处理
    if no_convert_words:
        words_span = []  # 句子字符串中指定字符组合外的子字符串索引
        sub_sentences = []  # 句子字符串中指定字符组合外的子字符串

        for word in re.finditer("|".join(no_convert_words), sentence):
            words_span.extend(list(word.span()))

        words_span.insert(0, None)
        words_span.append(None)

        for i in range(0, len(words_span), 2):
            sub_sentences.append(sentence[words_span[i] : words_span[i + 1]])

        participle_sub_sentences = participle_sentence(sub_sentences)
        for sub_sentence in participle_sub_sentences:
            convert_word_list(sub_sentence)

        words = []
        for i, sub_sentence in enumerate(participle_sub_sentences):
            words.append("".join(sub_sentence))
            if i + 1 < len(participle_sub_sentences):
                words.append(sentence[words_span[i * 2 + 1] : words_span[i * 2 + 2]])

    else:
        words = participle_sentence(sentence)

        if not words:
            return sentence

        convert_word_list(words)

    return "".join(words)


def convert_sentence_arabic_number_to_chinese(sentence):
    """
    对输入的句子进行分词和阿拉伯数字替换
    使用hanlp进行分词 doc: https://hanlp.hankcs.com/docs/
    :param sentence:  待转换的句子字符串
    """
    from ..extension.participle import participle_sentence

    words = participle_sentence(sentence)

    if not words:
        return sentence

    converted_words = [convert_arabic_number_to_chinese(word) for word in words]

    return "".join(converted_words)


def convert_chinese_number_to_arabic(word):
    """
    中文数字转阿拉伯数字 使用cn2an进行转换 doc: https://github.com/Ailln/cn2an
    :param word:   待转换的单词字符串
    """
    from ..extension.participle import participle_app

    def cn2an_convert(target, method, method_model=None):
        try:
            func = getattr(cn2an, method)
            result = func(target, method_model) if method_model else func(target)
        except Exception as error:
            if not isinstance(error, ValueError) and hasattr(participle_app, "logger"):
                participle_app.logger.error(f"convert word {word} except {str(error)}")
            return None
        else:
            return str(result)

    # 包含特殊子字符串用cn2an.transform处理
    special_word = ["百分"]
    pure_digital = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]

    # strict模式无法处理的情况下, 如果是纯数字的单词对词中每个字单独处理后拼接, 否则使用transform模式处理
    if any([(w in word) for w in special_word]):
        converted_word = cn2an_convert(word, "transform")
        return converted_word or word
    else:
        converted_word = cn2an_convert(word, "cn2an", "strict")
        if not converted_word:
            if all([(w in pure_digital) for w in word]):
                converted_word = "".join([cn2an_convert(w, "cn2an") or w for w in word])
            else:
                start_with_zero = re.match("^零+", word)
                if not start_with_zero:
                    zero_prefix = ""
                else:
                    zero_prefix = "0" * start_with_zero.span()[-1]
                    word = word[start_with_zero.span()[-1] :]
                converted_word = zero_prefix + (
                    cn2an_convert(word, "cn2an", "smart")
                    or cn2an_convert(word, "transform")
                    or word
                )
        return converted_word


def convert_arabic_number_to_chinese(word, model="low"):
    """
    阿拉伯数字转中文数字 使用cn2an进行转换 doc: https://github.com/Ailln/cn2an
    example: 1989年 -> 一千九百八十九年  2287 -> 二千二百八十七
    :param word:   待转换的单词字符串
    :param model:  cn2an转换模式 low/up/rmb/direct
    """
    from ..extension.participle import participle_app

    number_reg_check = "\d+\.?\d*"

    numbers = re.findall(number_reg_check, word)
    numbers.sort(key=lambda x: len(x), reverse=True)

    for number in numbers:
        chinese_number = None
        try:
            chinese_number = cn2an.an2cn(number, model)
        except Exception as e:
            if not isinstance(e, ValueError) and hasattr(participle_app, "logger"):
                participle_app.logger.error(f"convert number {number} except {str(e)}")
            chinese_number = number
        finally:
            if chinese_number != number:
                word = word.replace(number, chinese_number)

    return str(word)
