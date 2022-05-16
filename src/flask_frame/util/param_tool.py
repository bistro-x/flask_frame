import datetime


# 将dict_parm（dict类型）参数设置到obj对象中
def set_dict_parm(obj, dict_parm):
    for parm in dict_parm:
        setattr(obj, parm, dict_parm[parm])  # 相当于obj.name = value赋值语句


# 将object对象的dict对象
def model_to_dict(obj):
    dict_obj = obj.__dict__
    dict_obj.pop('_sa_instance_state', None)
    return dict_obj


# 判断字符串为None或空
def str_is_empty(str):
    return str is None or str == ''


# 判断字符串不为空
def str_is_not_empty(str):
    return not str_is_empty(str)


def get_curr_time():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

