from sqlalchemy import inspect


def get_all_column_list(model):
    return model.__table__.columns._all_columns


def add_filter(model, query, args):
    """
    add pararm filter to query on model
    :param model:
    :param query:
    :param param:
    :return:
    """
    # set query
    mapper = inspect(model)

    attr_names = [c_attr.key for c_attr in mapper.mapper.column_attrs]
    # query_param = ()
    for k, v in args.items():
        if k in attr_names:
            query = query.filter(getattr(model, k) == v)

    return query
