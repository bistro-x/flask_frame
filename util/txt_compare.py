# -*- coding:utf-8 -*-
import numpy as np,chardet
import re, sys, os


def num_to_char(num):
    """数字转中文"""
    num = str(num)
    num = num.replace("1_", "幺")
    new_str = ""
    num_dict = {"0": u"零", "1": u"一", "2": u"二", "3": u"三", "4": u"四", "5": u"五", "6": u"六", "7": u"七", "8": u"八",
                "9": u"九"}
    listnum = list(num)
    # print(listnum)
    shu = []
    for i in listnum:
        # print(num_dict[i])
        try:
            tmp = num_dict[i]
        except:
            tmp = i
        shu.append(tmp)
    new_str = "".join(shu)
    # print(new_str)
    return new_str


def init(s1, s2):
    m = np.empty((len(s1) + 1, len(s2) + 1))
    m[:] = np.inf
    # initializing the first row
    m[0] = np.arange(m.shape[1])
    # initializing the first column
    counter = 0
    for i in m:
        i[0] = counter
        counter += 1
    return m


def med_classic_gui(s1, s2):
    # INITIALIZATION
    m = init(s1, s2)
    for i in range(1, m.shape[0]):
        for j in range(1, m.shape[1]):

            # first condition : i is an insertion
            con1 = m[i - 1, j] + 1

            # second condition : j is a deletion
            con2 = m[i, j - 1] + 1

            # third condition : i and j are a substitution
            if s1[i - 1] == s2[j - 1]:
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
    backmatrix = [[' ' for y in range(len(s2) + 2)] for x in range(len(s1) + 2)]
    backmatrix[1][1] = 0

    for i in range(2, len(s1) + 2):
        backmatrix[i][0] = s1[i - 2]
    for j in range(2, len(s2) + 2):
        backmatrix[0][j] = s2[j - 2]

    for i in range(2, len(s1) + 2):
        backmatrix[i][1] = '|'

    for j in range(2, len(s2) + 2):
        backmatrix[1][j] = '-'

    for i in range(2, len(s1) + 2):
        for j in range(2, len(s2) + 2):
            vertical = mmm[i - 1][j] + 1
            horizontal = mmm[i][j - 1] + 1
            if s1[i - 2] == s2[j - 2]:
                diagonal = mmm[i - 1][j - 1]
            else:
                diagonal = mmm[i - 1][j - 1] + 1

            mindist = min(diagonal, vertical, horizontal)
            mmm[i][j] = mindist

            if mindist == diagonal:
                backmatrix[i][j] = 'bn'
            elif mindist == vertical:
                backmatrix[i][j] = '|'
            else:
                backmatrix[i][j] = '-'

    ss1 = ""
    ss2 = ""
    op = ""
    op2 = ''
    i = len(s1) + 1
    j = len(s2) + 1
    while not (i == 1 and j == 1):
        c = backmatrix[i][j]
        if c == '|':
            ss1 += s1[i - 2] + ' '
            ss2 += '**' + ' '
            op += ' ' + '  '
            op2 += 'D' + '  '
            i = i - 1
        elif c == 'bn':
            ss1 += s1[i - 2] + ' '
            ss2 += s2[j - 2] + ' '
            if s1[i - 2] == s2[j - 2]:
                op += '|' + '  '
                op2 += ' ' + '  '
            else:
                op += ' ' + '  '
                op2 += 'S' + '  '
            i = i - 1
            j = j - 1
        else:
            ss1 += '**' + ' '
            ss2 += s2[j - 2] + ' '
            op += ' ' + '  '
            op2 += 'I' + '  '
            j = j - 1

    # print("")
    # print("ALIGNMENT:")
    # print("")
    # print(ss1[::-1])
    # print(op[::-1])
    # print(ss2[::-1])

    # printing result and running time
    print(" ")
    # print("{} {} {} {}".format("MINIMUM EDIT DISTANCE :", int(m[m.shape[0] - 1][m.shape[1] - 1]),
    #                            "TOTAL STRING LENGTH :", len(s1)))

    op2, m, s1, op, s2 = op2[::-1], m[m.shape[0] - 1][m.shape[1] - 1], ss1[::-1], op[::-1], ss2[::-1]

    ref_length = len(s1.replace(" ", '').replace("**", '*'))
    I_COUNT_PCT = op2.count('I') / ref_length
    D_COUNT_PCT = op2.count('D') / ref_length
    S_COUNT_PCT = op2.count('S') / ref_length

    return op2, m, s1, op, s2, I_COUNT_PCT, D_COUNT_PCT, S_COUNT_PCT


# 批量计算：单文件多行
def batch_row_classice(ref_file, hyp_file):
    TOTAL_STRING_LENGTH = 0
    TOTAL_accuracy = 0  # 准确率
    TOTAL_I_COUNT_PCT = 0  # 插入率
    TOTAL_D_COUNT_PCT = 0  # 删除率
    TOTAL_S_COUNT_PCT = 0  # 替换率

    # ref = open(ref_file, 'r',encoding='UTF-8').read()  # realtexts
    # hyp = open(hyp_file, 'r',encoding='UTF-8').read()  # asrtexts

    with open(ref_file, 'r', encoding='UTF-8') as a, open(hyp_file, 'r', encoding='UTF-8') as b:
        realtexts = a.readlines()
        asrtexts = b.readlines()

        for i in range(len(realtexts)):
            # 去除标点符号
            ref = re.sub('[,.，。 \n?!？！]', '', realtexts[i])
            hyp = re.sub('[,.，。 \n?!？！]', '', asrtexts[i])
            ref = num_to_char(ref)
            hyp = num_to_char(hyp)

            op2, m, s1, op, s2, I_COUNT_PCT, D_COUNT_PCT, S_COUNT_PCT = med_classic_gui(ref, hyp)
            accuracy = 1 - (m / len(s1.replace(" ", '')))

            TOTAL_STRING_LENGTH = TOTAL_STRING_LENGTH + len(ref)
            TOTAL_accuracy = TOTAL_accuracy + accuracy * len(ref)
            TOTAL_I_COUNT_PCT = TOTAL_I_COUNT_PCT + I_COUNT_PCT * len(ref)
            TOTAL_D_COUNT_PCT = TOTAL_D_COUNT_PCT + D_COUNT_PCT * len(ref)
            TOTAL_S_COUNT_PCT = TOTAL_S_COUNT_PCT + S_COUNT_PCT * len(ref)

            print({"准确率": accuracy, "ref": ref, "hyp": hyp, "op": op, "op2": op2, "s1": s1, "s2": s2,
                   "插入率": I_COUNT_PCT, "删除率": D_COUNT_PCT, "替换率": S_COUNT_PCT})

    print("总字数:%s ,平均准确率：%s ，平均插入率：%s ，平均删除率：%s，平均替换率：%s " % (TOTAL_STRING_LENGTH, TOTAL_accuracy / TOTAL_STRING_LENGTH,
                                                              TOTAL_I_COUNT_PCT / TOTAL_STRING_LENGTH,
                                                              TOTAL_D_COUNT_PCT / TOTAL_STRING_LENGTH,
                                                              TOTAL_S_COUNT_PCT / TOTAL_STRING_LENGTH))


# 遍历目录（子目录），返回所有文件路径
def enum_path_files(path):
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

# 标准化文件编码
def standardized_file_encode(path):
    with open(path, "rb") as f:
        data = f.read()
    if len(data) == 0:
        return
    res = chardet.detect(data)
    if res["encoding"] == "GB2312":
        res["encoding"] = "GBK"
    with open(os.path.join(path), "w", encoding="utf-8") as file:
        line = str(data, encoding = res["encoding"])
        line = line.replace("\n","").replace("\r","")
        file.write(line)

def standardized_mark_file(path,filename):
    new_filename = filename.replace("_inspection","").replace("_mark","")
    if new_filename != filename :
        os.rename(os.path.join(path,filename),os.path.join(path,new_filename))
    return path,new_filename

# 批量计算：单行多文件
def batch_file_classice(ref_file_dir, hyp_file_dir):
    TOTAL_STRING_LENGTH = 0
    TOTAL_accuracy = 0
    TOTAL_I_COUNT_PCT = 0  # 插入率
    TOTAL_D_COUNT_PCT = 0  # 删除率
    TOTAL_S_COUNT_PCT = 0  # 替换率
    res = []

    file_paths = enum_path_files(ref_file_dir)
    for file_path in file_paths:
        print(file_path)
        ref_file_dir, file_path = standardized_mark_file(ref_file_dir, file_path)
        standardized_file_encode(os.path.join(ref_file_dir, file_path))
        ref = open(os.path.join(ref_file_dir, file_path), 'r', encoding="utf-8").read()
        standardized_file_encode(os.path.join(hyp_file_dir, file_path))
        hyp_path = os.path.join(hyp_file_dir, file_path)
        hyp = open(hyp_path, 'r', encoding="utf-8").read()

        ref = re.sub('[,.，。 \n\t?!？！]', '', ref)
        hyp = re.sub('[,.，。 \n\t?!？！]', '', hyp)
        ref = num_to_char(ref)
        hyp = num_to_char(hyp)

        op2, m, s1, op, s2, I_COUNT_PCT, D_COUNT_PCT, S_COUNT_PCT = med_classic_gui(ref, hyp)
        accuracy = 1 - (m / len(s1.replace(" ", '')))

        TOTAL_STRING_LENGTH = TOTAL_STRING_LENGTH + len(ref)
        TOTAL_accuracy = TOTAL_accuracy + accuracy * len(ref)
        TOTAL_I_COUNT_PCT = TOTAL_I_COUNT_PCT + I_COUNT_PCT * len(ref)
        TOTAL_D_COUNT_PCT = TOTAL_D_COUNT_PCT + D_COUNT_PCT * len(ref)
        TOTAL_S_COUNT_PCT = TOTAL_S_COUNT_PCT + S_COUNT_PCT * len(ref)

        res.append({"filename": os.path.basename(file_path),"accuracy": accuracy,"I_COUNT_PCT": I_COUNT_PCT, "D_COUNT_PCT": D_COUNT_PCT, "S_COUNT_PCT": S_COUNT_PCT})
        print({"准确率": accuracy, "ref": ref, "hyp": hyp, "op": op, "op2": op2, "s1": s1, "s2": s2,
               "插入率": I_COUNT_PCT, "删除率": D_COUNT_PCT, "替换率": S_COUNT_PCT})

    res.append({"filename":"汇总","accuracy": TOTAL_accuracy / TOTAL_STRING_LENGTH, "I_COUNT_PCT": TOTAL_I_COUNT_PCT / TOTAL_STRING_LENGTH,
                "D_COUNT_PCT": TOTAL_D_COUNT_PCT / TOTAL_STRING_LENGTH, "S_COUNT_PCT": TOTAL_S_COUNT_PCT / TOTAL_STRING_LENGTH})
    print("总字数:%s ,平均准确率：%s ，平均插入率：%s ，平均删除率：%s，平均替换率：%s " % (TOTAL_STRING_LENGTH, TOTAL_accuracy / TOTAL_STRING_LENGTH,
                                                              TOTAL_I_COUNT_PCT / TOTAL_STRING_LENGTH,
                                                              TOTAL_D_COUNT_PCT / TOTAL_STRING_LENGTH,
                                                              TOTAL_S_COUNT_PCT / TOTAL_STRING_LENGTH))
    return res

if __name__ == "__main__":
        # standardized_file_encode(r"F:\Z-ASR\ths脱敏录音撰写\14181_143023.txt")
    print(r"""
===========================================
用法举例：
单文件对比：python txt_compare.pyc C:\Users\czc\Desktop\txt\txt_comp\mark_out.txt C:\Users\czc\Desktop\txt\dir_comp\lei_out.txt
多文件对比：python txt_compare.pyc C:\Users\czc\Desktop\txt\dir_comp\mark_108 C:\Users\czc\Desktop\txt\dir_comp\asr_108
===========================================     

    """)

    # 读取文件
    if len(sys.argv) < 2:
        print("传参错误，需要2个参数：人工标注文本路径  机转文本路径 ")
    else:
        ref_file_path = sys.argv[1]
        hyp_file_path = sys.argv[2]
        print("人工标注文本路径：%s \n机转文本路径:%s " % (ref_file_path, hyp_file_path))

        # ref_file_path = r"C:\Users\czc\Desktop\txt\dir_comp\mark_108"
        # hyp_file_path = r"C:\Users\czc\Desktop\txt\dir_comp\asr_108"

        # ref_file_path = r"C:\Users\czc\Desktop\txt\txt_comp\mark_out.txt"
        # hyp_file_path = r"C:\Users\czc\Desktop\txt\txt_comp\lei_out.txt"

        print("param: %s , %s" % (ref_file_path, hyp_file_path))

        if os.path.isdir(ref_file_path):
            batch_file_classice(ref_file_path, hyp_file_path)
        elif os.path.isfile(ref_file_path):
            batch_row_classice(ref_file_path, hyp_file_path)
        else:
            print("参数错误，文件或目录不存在")
