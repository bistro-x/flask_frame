# 如何从 0.8 版本迁移到 1.0 版本

- api/response.py 的 deprecated 方法进行弃用，
  - result_to_dict 使用 util.db.result_to_dict

## 数据库

- db.session.execute(text(sql_group)) 需要使用 text 封装语句
- db.engine.execute 需要 改成 db.session.execute
