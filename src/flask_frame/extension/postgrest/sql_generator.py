# url 转 sql 生成器，postgrest 格式


def generate_sql(
    method: str, path: str, args: dict = None, data: dict = None, headers: dict = {}
):

    """http数据转换成SQL语句

    Args:
        method (str): http方法
        path (str): 访问路径
        args (dict, optional): url参数. Defaults to None.
        data (dict, optional): body数据. Defaults to None.
        headers (dict, optional): 报头. Defaults to {}.

    Returns:
        str: SQL语句
    """

    sql = ""  # 返回条件
    count_sql = None

    table_name = path.replace("/", "")  # 表名
    if args:
        select_sql, where_sql, order_sql, limit_sql, join_table = condition_bulid(
            table_name, args
        )  # 搜索条件
    else:
        select_sql = "*"

    return_data = "return=representation" in headers.get("Prefer", "")  # 是否返回修改数据
    return_sql = " returning * " if return_data else ""  # 数据返回语句

    if method.casefold() == "get":
        table_name_str = '"' + '","'.join(join_table + [table_name]) + '"'
        # 数据查询
        sql = f"select {select_sql} from {table_name_str } where {where_sql} {order_sql} {limit_sql};"
        count_sql = f'select count(*) from { table_name_str} where {where_sql} ;'
    elif method.casefold() == "delete":
        # 数据修改
        sql = f'delete from "{table_name}"  where {where_sql}  {return_sql};'
    elif method.casefold() == "post":
        # 数据新增
        merge = "merge-duplicates" in headers.get("Prefer", "")
        sql = data_build(
            table_name, data, merge, args.get("on_conflict", "").split(","), return_sql
        )
    elif method.casefold() == "patch":
        # 数据修改
        sql = update_sql(table_name, data, None, where_sql, return_sql)

    else:
        # todo throw error
        print("error")
    print("sql:" + str(sql))
    print("count_sql:" + (count_sql or ""))

    return sql, count_sql


def condition_bulid(table_name: str, args: dict):
    """条件转换器

    Args:
        table_name (str): 表名
        args (dict): 传入参数
    """

    where_sql = " 1 = 1 "  # 条件sql
    select_sql = "*"  # 查询字段 sql
    limit_sql = " "  # 翻页参数
    order_sql = " "  # 排序与剧院
    join_table = []  # 关联表

    for key, value in args.items():
        # 转换字段
        if key.casefold() == "select":
            select_value = value

            # 拼接字符串
            if select_value.startswith("("):
                select_value = select_value.replace("(", "").replace(")", "").split(",")
                select_sql = (
                    "("
                    + ",".join([f"{replace_value(item)}" for item in select_value])
                    + ")"
                )
            elif "(" in select_value:
                select_value_array = []
                select_value = select_value.split(",")
                for item in select_value:
                    # 普通字段
                    if "(" in item:
                        # 扩展字段
                        join_table_name = item.split("(")[0]
                        field_name = item.split("(")[1].replace(")", "").split(",")
                        field_name_str = ",".join(
                            [f"{join_table_name}.{item}" for item in field_name]
                        )
                        select_value_array.append(
                            f' (select row_to_json(_) from (select {field_name_str} ) as _) as "{join_table_name}"'
                        )

                        # 增加扩展表
                        join_table.append(join_table_name)
                    elif "->>" in item:
                        select_value_array.append(
                            f"{table_name}.{item.split('->>')[0]}->>'{item.split('->>')[1]}' as \"{item.split('->>')[1]}\""
                        )
                    elif "->" in item:
                        select_value_array.append(
                            f"{table_name}.{item.split('->')[0]}->'{item.split('->>')[1]}' as \"{item.split('->')[1]}\""
                        )
                    else:
                        select_value_array.append(f"{table_name}.{item}")

                select_sql = ",".join(select_value_array)
            else:
                select_sql = ",".join(
                    [f"{table_name}.{item}" for item in select_value.split(",")]
                )

            continue
        elif key.casefold() == "limit":
            limit_sql += f" limit {value}"
            continue
        elif key.casefold() == "offset":
            limit_sql += f" offset {value}"
            continue
        elif key.casefold() == "order":
            values = (
                value.replace("nullslast", "nulls last")
                .replace("nullsfirst", "nulls first")
                .split(".")
            )
            if "->>" in values[0]:
                keys = values[0].split("->>")
                for i in range(1, len(keys)):
                    keys[i] = f"'{keys[i]}'"
                values[0] = "->>".join(keys)
            order_sql += f" order by {' '.join(values)}"
            continue
        else:
            where_sql += " and " + where_sql_build(table_name, value, key)

    # 返回查询语句
    return select_sql, where_sql, order_sql, limit_sql, join_table


def where_sql_build(table_name: str, value: str, key: str = None):
    """构建where语句

    Args:
        table_name (str): 表名
        value (str): 数值
        key (str, optional): 参数名. Defaults to None.

    Returns:
        _type_: _description_
    """
    parse_map = {
        "not.is": "is not",
        "not.eq": "!=",
        "eq": "=",
        "ne": ">",
        "gte": ">=",
        "lt": "<",
        "lte": "<=",
        "neq": "!=",
        "like": "like",
        "ilike": "ilike",
        "in": "in",
        "is": "is",
        "fts": "@@",
        "plfts": "@@",
        "phfts": "@@",
        "wfts": "@@",
        "cs": "@>",
        "cd": "<@",
        "ov": "&&",
        "sl": "<<",
        "sr": ">>",
        "nxr": "&<",
        "nxl": "&>",
        "adj": "-|-",
        "not": "not",
        "or": "or",
        "and": "and",
    }

    where_sql = ""

    while True:
        if not key:
            # 下一个字符是(
            if value.find("(") > 0 and (
                value.find("(") < value.find(".") or value.find(".") < -1
            ):
                key = value.split("(", 1)[0]
                value = "(" + value.split("(", 1)[1]
            # 下一个字符)
            else:
                key = value.split(".", 1)[0]
                value = value.split(".", 1)[1]

        if key in ["not"]:
            where_sql += " not "
            key = None
        elif key.startswith("not."):
            where_sql += " not "
            key = key.replace("not.", "")
            continue
        elif key in ["or", "and"]:
            union_sign = key

            # 拼装子条件
            value_available = value[1:][:-1]
            value_list = []
            scope = False
            begin_index = 0
            for index, item in enumerate(value_available):
                if index == (len(value_available) - 1):
                    index_end = index + 1
                    value_list.append(value_available[begin_index:index_end])
                elif item == "," and not scope:
                    value_list.append(value_available[begin_index:index])
                    begin_index = index + 1
                elif item == "(":
                    scope = True
                elif item == ")":
                    scope = False

            where_sql += " ("
            for index, item in enumerate(value_list):
                where_sql += where_sql_build(table_name, item) + (
                    " " + union_sign + " " if index < len(value_list) - 1 else ""
                )
            where_sql += ")"
            return where_sql
        else:
            break

    # 子条件
    where_sql += f' "{table_name}".{replace_key(key)}  '

    # 拆分表达式和数值
    split_index = 0
    for map_key, map_value in parse_map.items():
        current_index = value.rfind(map_key + ".")
        if current_index < 0:
            continue

        current_index += +len(map_key + ".")
        if current_index > split_index:
            split_index = current_index

    search_reg, search_value = value[:split_index], value[split_index:]

    # 转换表达式
    not_sql = ""
    if (
        search_reg.startswith("not.")
        and not search_reg.startswith("not.is")
        and not search_reg.startswith("not.eq")
    ):
        not_sql = "not "
        search_reg = search_reg.replace("not.", "")

    for map_key, map_value in parse_map.items():
        if map_key in ["like"]:
            search_value = search_value.replace("*", "%")
        search_reg = search_reg.replace(map_key + ".", " " + map_value + " ")
        if "." not in search_reg:
            break

    # 拼接
    where_sql += f"{not_sql} {search_reg} {replace_value(search_value)} "

    return where_sql


def data_build(table_name, data, merge=False, key_field_list=None, return_sql=""):
    """数据转换
    Args:
       data (List[dict]): 传入参数
    """
    if not key_field_list:
        key_field_list = ["id"]

    handle_data = data if isinstance(data, list) else [data]

    sql = []
    for item in handle_data:
        if merge and all(
            [item.get(key_field, None) is not None for key_field in key_field_list]
        ):
            sql.append(
                update_sql(table_name, item, key_field_list, return_sql=return_sql)
            )
        else:
            sql.append(insert_sql(table_name, item, return_sql=return_sql))

    return sql


def update_sql(table_name, data, key_field_list=["id"], where_sql=None, return_sql=""):
    """构建修改数据
    Args:
        data (_type_): _description_
    """
    if not where_sql:
        where_sql = []
        for key_field in key_field_list:
            key_value = data.pop(key_field, None)
            where_sql.append(f"{replace_key(key_field)}={replace_value(key_value)}")
        where_sql = " and ".join(where_sql)

    filed_update_sql = ",".join(
        [f"{replace_key(key)}={replace_value(value)}" for key, value in data.items()]
    )
    sql = (
        f'update "{table_name}" set  {filed_update_sql} where {where_sql} {return_sql};'
    )
    return sql


def insert_sql(table_name, data, return_sql=""):
    """生成插入数据

    Args:
        table_name (_type_): 表名
        data (_type_): 插入数据

    Returns:
        str: 插入语句
    """

    key_sql = ",".join([f"{replace_key(key)}" for key in data.keys()])
    value_sql = ",".join([(f"{replace_value(value)}") for value in data.values()])

    sql = f'insert into "{table_name}" ({key_sql}) values ({value_sql}) {return_sql};'
    return sql


def replace_key(value: str):
    """切换数据值为数据库的字段表示

    Args:
        value (str): 传入字段

    Returns:
        str: 数据库数值
    """
    return f'"{value}"'


def replace_value(value: str):
    """切换数据值为数据库的数值表示

    Args:
        value (str): 传入数值

    Returns:
        str: 数据库数值
    """
    import json

    if value is None:
        return "null"

    if isinstance(value, list) and len(value) == 0:
        return "null"

    if isinstance(value, list) and not isinstance(value[0], dict):
        if isinstance(value[0], int):
            type_name = "integer"
        else:
            type_name = "text"

        return (
            "array["
            + ",".join([f"{replace_value(item)}" for item in value])
            + f"]::{type_name}[]"
            if len(value) > 0
            else f"array[]::{type_name}[]"
        )

    if isinstance(value, dict) or (isinstance(value, list) and isinstance(value[0], dict)):
        result = json.dumps(value, ensure_ascii=False)
        return "'" + result + "'"

    if str(value) == "null":
        return value

    if str(value).startswith("("):
        result = value.replace("(", "").replace(")", "").split(",")
        result = "(" + ",".join([f"{replace_value(item)}" for item in result]) + ")"
        return result
    else:
        return f"'{value}'"


if __name__ == "__main__":
    # print(generate_sql("GET", "/user", {"id": "eq.1","id2": "eq.1","id3": "eq.1", "limit": 3, "offset": 5}))
    print(
        generate_sql(
            "GET",
            "/user",
            {
                "id": "eq.1",
                "limit": 3,
                "select": "id",
                "or": "(age.eq.14,not.and(age.gte.11,age.lte.17))",
                "not.and": "(a.gte.0,a.lte.100)",
            },
        )
    )

    print(generate_sql("DELETE", "/user", {"id": "eq.1"}))
    print(generate_sql("PATCH", "/user", {"id": "eq.1"}, {"category": "child"}))
    print(
        generate_sql(
            "POST",
            "/user",
            {"on_conflict": "name,salary"},
            [
                {"id": 1, "name": "Old employee 1", "salary": 30000},
                {"id": 2, "name": "Old employee 2", "salary": 42000},
                {"name": "New employee 3"},
            ],
            {"Prefer": "merge-duplicates,return=representation"},
        )
    )
