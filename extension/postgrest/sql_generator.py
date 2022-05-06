# url 转 sql 生成器，postgrest 格式
import string
from turtle import st
from typing import List


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

    if method.casefold() == "get":
        # 数据查询
        sql = f'select {select_sql} from { ",".join(join_table + [table_name])} where {where_sql} {order_sql} {limit_sql};'
        count_sql = f'select count(*) from { ",".join(join_table + [table_name])} where {where_sql} ;'
    elif method.casefold() == "delete":
        # 数据修改
        sql = f'delete from "{table_name}"  where {where_sql};'
    elif method.casefold() == "post":
        # 数据新增
        merge = "merge-duplicates" in headers.get("Prefer", "")
        sql = data_build(table_name, data, merge)
    elif method.casefold() == "patch":
        # 数据修改
        sql = update_sql(table_name, data, None, where_sql)

    else:
        # todo throw error
        print("error")

    return sql,count_sql


def condition_bulid(table_name: str, args: dict):
    """条件转换器

    Args:
        table_name (str): 表名
        args (dict): 传入参数
    """
    parse_map = {
        "not.eq": "is not",
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
            else:
                # 关联表进行查询
                if "(" in select_value:
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
                            select_value_array.append(f"{table_name}.{item.split('->>')[0]}->>'{item.split('->>')[1]}' as \"{item.split('->>')[1]}\"")
                        elif "->" in item:
                            select_value_array.append(f"{table_name}.{item.split('->')[0]}->'{item.split('->>')[1]}' as \"{item.split('->')[1]}\"")
                        else:
                            select_value_array.append(f"{table_name}.{item}")

                    select_sql = ",".join(select_value_array)
            continue
        elif key.casefold() == "limit":
            limit_sql += f" limit {value}"
            continue
        elif key.casefold() == "offset":
            limit_sql += f" offset {value}"
            continue
        elif key.casefold() == "order":
            order_sql += f" order by {value.replace('.',' ').replace('nullslast','nulls last').replace('nullsfirst','nulls first')}"
            continue
        elif key.startswith("not."):
            where_sql += f"and not {table_name}.{key}"
            value = value.replace("not.", "")
        elif key.casefold() == "or":
            continue
        elif key.casefold() == "and":
            continue
        else:
            where_sql += f"and {table_name}.{key}"

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
        for map_key, map_value in parse_map.items():
            search_reg = search_reg.replace(map_key + ".", " " + map_value + " ")
            if "." not in search_reg:
                break

        # 拼接
        where_sql += f"{search_reg} {replace_value(search_value)} "

    # 返回查询语句
    return select_sql, where_sql, order_sql, limit_sql, join_table


def data_build(table_name, data, merge=False):
    """数据转换
    Args:
       data (List[dict]): 传入参数
    """
    key_field = "id"
    handle_data = data if isinstance(data, list) else [data]

    sql = ""
    for item in handle_data:
        if merge and item.get(key_field):
            sql += update_sql(table_name, item, key_field)
        else:
            sql += insert_sql(table_name, item)

    return sql


def update_sql(table_name, data, key_field="id", where_sql=None):
    """构建修改数据

    Args:
        data (_type_): _description_
    """
    if not where_sql:
        key_value = data.pop(key_field, None)
        where_sql = f" {replace_key(key_field)}={replace_value(key_value)}"

    filed_update_sql = ",".join(
        [
            f"{replace_key(key)}={replace_value(value)}"
            for key, value in data.items()
        ]
    )
    sql = f'update "{table_name}" set  {filed_update_sql} where {where_sql};'
    return sql


def insert_sql(table_name, data):
    """生成插入数据

    Args:
        table_name (_type_): 表名
        data (_type_): 插入数据

    Returns:
        str: 插入语句
    """

    key_sql = ",".join([f"{replace_key(key)}" for key in data.keys()])
    value_sql = ",".join(
        [
            (f"{replace_value(value)}")
            for value in data.values()
        ]
    )

    sql = f'insert into "{table_name}" ({key_sql}) values ({value_sql});'
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
    

    if value is None:
        return "null"
    if isinstance(value,list):
        return "'{" + ",".join([f"{replace_value(item)}" for item in value]) + "}'"
    if value in ("null"):
        return value

    if value.startswith("("):
        result = value.replace("(", "").replace(")", "").split(",")
        result = (
            "(" + ",".join([f"{replace_value(item)}" for item in result]) + ")"
        )
        return result
    else:
        return f"'{value}'"


if __name__ == "__main__":
    print(generate_sql("GET", "/user", {"id": "eq.1", "limit": 3, "offset": 5}))
    print(generate_sql("DELETE", "/user", {"id": "eq.1"}))
    print(generate_sql("PATCH", "/user", {"id": "eq.1"}, {"category": "child"}))
    print(
        generate_sql(
            "POST",
            "/user",
            None,
            [
                {"id": 1, "name": "Old employee 1", "salary": 30000},
                {"id": 2, "name": "Old employee 2", "salary": 42000},
                {"name": "New employee 3", "salary": 50000},
            ],
            {"Prefer": "merge-duplicates"},
        )
    )
