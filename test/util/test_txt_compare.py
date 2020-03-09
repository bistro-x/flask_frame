# -*- coding:utf-8 -*-
from ...util.txt_compare import str_compare


def test_func():
    result = str_compare("1241我说2", "1231我")
    print(result)
# 1231我说2
# 1231我哈111290
