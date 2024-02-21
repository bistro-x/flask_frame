from .extension.database import db, db_schema
from .api.response import queryToDict

permission_map = None


# 判断权限
def check_permission(uri, method, usr_roles):
    global permission_map
    can_access = False
    if permission_map == None:
        load_permission()

    key = "%s:%s" % (method, uri)
    if key in permission_map:
        permission = permission_map[key]
        for role_id in usr_roles:
            if role_id in permission["role_ids"]:
                can_access = True
                break
    else:  # 权限没有配置到权限表中，默认可以访问
        return True

    return can_access


# 加载角色权限
def load_permission():
    from flask import current_app

    global permission_map
    permission_map = {}
    with current_app.app_context():
        sql = f"""
            SET search_path to {db_schema};
            select * from permission_role
            """
        res = db.session.execute(sql).fetchall()
        permission_list = queryToDict(res)
        for permission in permission_list:
            permission["role_ids"] = permission["role_ids"].split(",")
            permission["role_names"] = permission["role_names"].split(",")
            permission_key = "%s:%s" % (permission["method"], permission["url"])
            permission_map[permission_key] = permission
