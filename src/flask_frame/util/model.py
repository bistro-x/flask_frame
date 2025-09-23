from sqlalchemy import inspect


def get_all_column_list(model):
    """
    获取 SQLAlchemy 模型的所有字段列表
    :param model: SQLAlchemy 模型类
    :return: 字段对象列表
    """
    return model.__table__.columns._all_columns


def add_filter(model, query, args):
    """
    根据参数字典为 SQLAlchemy 查询对象添加过滤条件
    :param model: SQLAlchemy 模型类
    :param query: 查询对象
    :param args: 过滤参数字典
    :return: 新的查询对象
    """
    # 获取模型的所有字段名
    mapper = inspect(model)
    attr_names = [c_attr.key for c_attr in mapper.mapper.column_attrs]
    for k, v in args.items():
        if k in attr_names:
            query = query.filter(getattr(model, k) == v)
    return query
