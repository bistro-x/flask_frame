# encoding: utf-8


def api_init(app, table_list):
    from frame.extension.database import db

    db.Model.metadata.reflect(bind=db.engine, schema='user_auth')

    class Permission(db.Model):
        __tablename__ = 'permission'
        __table_args__ = {'extend_existing': True, 'schema': "user_auth"}

    class PermissionScope(db.Model):
        __tablename__ = 'permission_scope'
        __table_args__ = {'extend_existing': True, 'schema': "user_auth"}

    class PermissionScopeDetail(db.Model):
        __tablename__ = 'permission_scope_detail'
        __table_args__ = {'extend_existing': True, 'schema': "user_auth"}

    method_map = {
        "GET": "查询",
        "POST": "新增",
        "DELETE": "删除",
        "PATCH": "修改",
        "PUT": "覆盖",
        "EXPORT": "导出",
        "IMPORT": "导入"
    }

    product_key = app.config.get("PRODUCT_KEY")

    for table in table_list:
        # permission
        for method in ["GET", "POST", "DELETE", "PATCH", "PUT"]:
            key = table.get("key") + "_" + method.lower()
            if not Permission.query.filter_by(product_key=product_key, key=key).first():
                db.session.add(
                    Permission(product_key=product_key, name=table.get("name") + "_" + method_map.get(method),
                               url="/" + table.get("key"),
                               method=method,
                               key=key))

        # permission scope
        parent_key = table.get("key") + "_" + "get"
        if not PermissionScope.query.filter_by(product_key=product_key, key=parent_key).first():
            db.session.add(
                PermissionScope(product_key=product_key, name=table.get("name"),
                                key=parent_key, parent_key="login"))
            db.session.flush()

        db.session.add(PermissionScopeDetail(permission_key=parent_key, permission_scope_key=parent_key))

        #  permission method scope
        for method in ["POST", "DELETE", "PATCH", "EXPORT", "IMPORT"]:
            key = table.get("key") + "_" + method.lower()
            if not PermissionScope.query.filter_by(product_key=product_key, key=key).first():
                db.session.add(
                    PermissionScope(product_key=product_key, name=table.get("name") + "_" + method_map.get(method),
                                    key=table.get("key") + "_" + method.lower(), parent_key=parent_key))

                db.session.flush()

                #  permission method scope
                permission_key = key
                if method == "EXPORT":
                    permission_key = table.get("key") + "_" + "get"
                elif method == "IMPORT":
                    permission_key = table.get("key") + "_" + "post"

                db.session.add(PermissionScopeDetail(product_key=product_key, permission_key=permission_key,
                                                     permission_scope_key=key))

    if app and app.url_map:
        for record in app.url_map.iter_rules():
            for method in record.methods:
                if method in method_map.keys():
                    if len(record.rule) > 1 and Permission.query.filter_by(
                            product_key=product_key,
                            key=record.rule[1:].replace("/", "_") + "_" + method.lower()).count() < 1:
                        db.session.add(
                            Permission(product_key=product_key, url=record.rule,
                                       method=method,
                                       key=record.rule[1:].replace("/", "_") + "_" + method.lower()))

                    db.session.commit()
