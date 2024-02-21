def attribute_copy(obj_from, obj_to, include=None, exclude=None):
    """对象之间进行属性复制"""
    for n, v in obj_from.__dict__.items():
        if include and n not in include:
            continue
        if exclude and n in exclude:
            continue
        if n.startswith("_"):
            continue

        if hasattr(obj_to, n):
            setattr(obj_to, n, v)


def attribute_copy_form_dict(dict_from, obj_to, include=None, exclude=None):
    """复制字典属性到对象"""
    for n, v in dict_from.items():
        if include and n not in include:
            continue
        if exclude and n in exclude:
            continue

        if hasattr(obj_to, n):
            setattr(obj_to, n, v)
