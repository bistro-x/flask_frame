from frame.annotation import deprecated
from frame.util import txt_compare


def get_asr_report(base_record, check_record, clauses_tolerance=50):
    """
    计算准确率等报告信息
    需要以 check_text 去除 base_text 不存在的数据，否则会产生 删除率过高的情况
    base_record 质检数据
    check_record 标注数据
    clauses_tolerance 分句容错
    """

    base_record.sort(key=lambda item: item.get("begin_time"))
    check_record.sort(key=lambda item: item.get("begin_time"))

    # 去除质检中不存在的数据
    check_record_real = []
    check_index = 0
    base_index = 0

    check_claus_error_num = 0  # 分句错误数据
    check_claus_error_last_index = None  # 上一次分句错误索引
    hit = False  # 曾经命中质检项
    while base_index < len(base_record):
        if len(check_record) > 0:
            i = check_record[check_index] if check_index < len(check_record) else check_record[len(check_record) - 1]
        else:
            i = {
                "begin_time": 0,
                "end_time": 0,
                "text": "",
            }
        j = base_record[base_index]

        # 当前检查项为空跳过
        if (j.get("text", "") or "").strip().lower() in ["", "unk"]:
            base_index += 1
            continue

        # 超过检查项，直接跳过
        if j.get("end_time") < i.get("begin_time") or check_index >= len(check_record):
            base_index += 1
            if not hit and check_claus_error_last_index != base_index:
                check_claus_error_last_index = base_index
                check_claus_error_num += 1
            hit = False
            continue

        # 在检查项之前，匹配下一个检查项
        if i.get("end_time") < j.get("begin_time"):
            check_index += 1
            continue

        # 增加检查语句
        check_record_real.append(i)
        check_index += 1

        # 检测分句是否错误
        if check_claus_error_last_index != base_index and (abs(
                i.get("begin_time") - j.get("begin_time")) > clauses_tolerance or abs(
            i.get("end_time") - j.get("end_time")) > clauses_tolerance):
            check_claus_error_last_index = base_index
            check_claus_error_num += 1

        # 设置做了一次匹配
        hit = True

    # 比较
    base_text = ''.join([i.get('text') if i.get('text') is not None else '' for i in base_record])
    check_text = ''.join([i.get('text') if i.get('text') is not None else '' for i in check_record_real])

    result = txt_compare.str_compare(str(base_text).lower(), str(check_text).lower())
    result["check_claus_error_num"] = check_claus_error_num  # 分句错误数
    result["statement_num"] = len(base_record)  # 句数
    result["check_claus_error_ratio"] = round(check_claus_error_num / (len(base_record) or 1), 4)  # 分句错误率

    return result


def get_intersection_data(check_data: list, result_data: list) -> list:
    """
    计算两个时间区域的交集
    :param check_data: 标注数据
    :param result_data: 结果数据
    :return: 结果数据
    """

    result = list()
    for ia in result_data:
        for ib in check_data:
            if ib.get("end_time") < ia.get("begin_time"):
                continue
            if ib.get("begin_time") > ia.get("end_time"):
                break
            if ia.get("begin_time") > ib.get("begin_time") and ia.get("end_time") < ib.get("end_time"):
                result.append({"begin_time": ia.get("begin_time"), "end_time": ia.get("end_time")})
            elif ia.get("begin_time") < ib.get("begin_time") and ia.get("end_time") > ib.get("end_time"):
                result.append({"begin_time": ib.get("begin_time"), "end_time": ib.get("end_time")})
            else:
                result.append(
                    {"begin_time": max(ia.get("begin_time"), ib.get("begin_time")),
                     "end_time": min(ia.get("end_time"), ib.get("end_time"))})

    return result
