from extension.database import db
from frame import JsonResult as js

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
    from app import app

    global permission_map
    permission_map = {}
    with app.app_context():
        sql = """select p.name,p.url,p.method ,string_agg(cast(r.id as text),',') as role_ids,string_agg(r.name,',') as role_names from sys_permission p 
                    join sys_permission_group_rel gr on gr.permission_id = p.id
                    join sys_permission_group_role pr on gr.permission_group_id = pr.permission_group_id 
                    join sys_role r on r.id = pr.role_id
                group by p.name,p.url,p.method
            """
        res = db.session.execute(sql).fetchall()
        permission_list = js.queryToDict(res)
        for permission in permission_list:
            permission["role_ids"] = permission["role_ids"].split(",")
            permission["role_names"] = permission["role_names"].split(",")
            permission_key = "%s:%s" % (permission["method"], permission["url"])
            permission_map[permission_key] = permission
