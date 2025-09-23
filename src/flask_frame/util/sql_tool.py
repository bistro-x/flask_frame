# 原生sql分页查询
def mysql_page(db, sql, offset, limit, sort=None, db_schema=None):
    """
    使用原生SQL进行分页查询。
    :param db: 数据库连接对象
    :param sql: 查询SQL语句（不带分页）
    :param offset: 偏移量
    :param limit: 每页数量
    :param sort: 排序字段，'-'开头表示降序
    :param db_schema: 可选，指定schema
    :return: (查询结果, 总数)
    """
    if not sort:
        sort = "id"

    path = ""
    if db_schema:
        # 设置schema
        path = f"set search_path ={db_schema};"

    # 统计总数
    total = db.session.execute(f"{path} select count(*) from (" + sql + ") t").fetchall()[0][0]
    # 构造分页SQL
    page_sql = "select * from ( %s) t " % sql
    asc = " desc "
    if sort:
        if sort[0] == "-":
            sort = sort[1:]
            asc = " desc "
    # 添加排序
    page_sql = page_sql + "order by %s %s" % (sort, asc)
    # 添加limit和offset
    page_sql = page_sql + " limit %s offset %s " % (limit, offset)
    # 执行分页查询
    res = db.session.execute(path + page_sql).fetchall()
    return res, total


def set_model_sort(query, sort):
    """
    根据sort参数设置SQLAlchemy查询的排序。
    :param query: SQLAlchemy查询对象
    :param sort: 排序字段，'-'开头表示降序
    :return: 排序后的查询对象
    """
    if sort[0] == "-":
        sort = sort[1:]
        asc = False
    else:
        asc = True
    # 遍历所有列，找到匹配的列进行排序
    for col in query.selectable._columns_plus_names:
        if col[1].description == sort:
            if asc:
                query = query.order_by(col[1].asc())
            else:
                query = query.order_by(col[1].desc())
            break
    return query


# SQLAlchemy 对象分页查询
def model_page(query, limit, offset, sort=None):
    """
    使用SQLAlchemy ORM对象进行分页查询。
    :param query: SQLAlchemy查询对象
    :param limit: 每页数量
    :param offset: 偏移量
    :param sort: 排序字段，'-'开头表示降序
    :return: (查询结果, 总数)
    """
    total = query.count()
    # 默认升序
    asc = True
    if sort:
        query = set_model_sort(query, sort)
    # 分页查询
    res = query.offset(offset).limit(limit).all()
    return res, total
