# 如何从 0.8 版本迁移到 1.0 版本

- api/response.py 的 deprecated 方法进行弃用，
  - result_to_dict 使用 util.db.result_to_dict

## 数据库

- db.session.execute(text(sql_group)) 需要使用 text 封装语句
- db.engine.execute 需要 改成 db.session.execute
- 查询字典数据必须用 mappings().fetchall(), fetchall() 或者 直接 for 循环 获取到的 都是 tuple
- sql 的传入参数 需要从    result = engine.execute(query, object_name=object_name, schema_name=schema_name) 变成 db.session.execute(query, {"object_name": object_name, "schema_name": schema_name})

## schema

- fields 的 default 参数 需要改成 missing
