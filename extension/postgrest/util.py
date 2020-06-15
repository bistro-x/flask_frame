def get_args_delete_prefix(arg):
    """
    获取删除前缀表表达式的参数,只支持 eq.
    :return:
    """

    if not arg:
        return arg

    return arg.replace("eq.", "")
