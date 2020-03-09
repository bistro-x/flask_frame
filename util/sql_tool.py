# 原生sql分页查询
def mysql_page(db, sql, offset, limit, sort=None, db_schema=None):
    if not sort:
        sort = "id"

    path = ""
    if db_schema:
        path = f"set search_path ={db_schema};"

    total = db.session.execute(f"{path} select count(*) from (" + sql + ") t").fetchall()[0][0]
    page_sql = "select * from ( %s) t " % sql
    asc = " desc "
    if sort:
        if sort[0] == "-":
            sort = sort[1:]
            asc = " desc "
    page_sql = page_sql + "order by %s %s" % (sort, asc)
    page_sql = page_sql + " limit %s offset %s " % (limit, offset)
    res = db.session.execute(path + page_sql).fetchall()
    return res, total


def set_model_sort(query, sort):
    if sort[0] == "-":
        sort = sort[1:]
        asc = False
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
    total = query.count()
    asc = True
    if sort:
        query = set_model_sort(query, sort)
    res = query.offset(offset).limit(limit).all()
    return res, total
