import datetime


# 将字典参数批量设置到对象属性
def set_dict_parm(obj, dict_parm):
    for parm in dict_parm:
        setattr(obj, parm, dict_parm[parm])  # 等价于 obj.<parm> = value


# 对象转字典，去除SQLAlchemy内部状态
def model_to_dict(obj):
    dict_obj = obj.__dict__
    dict_obj.pop('_sa_instance_state', None)  # 移除ORM状态字段
    return dict_obj


# 判断字符串是否为None或空
def str_is_empty(str):
    return str is None or str == ''

# 判断字符串是否非空
def str_is_not_empty(str):
    return not str_is_empty(str)


# 获取当前时间字符串（精确到微秒）
def get_curr_time():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

