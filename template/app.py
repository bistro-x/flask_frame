"""
业务服务入口示例。
展示 flask_frame 的基本使用方式。
"""
from flask import Blueprint
from flask_frame import Response, FlaskFrameConfig, create_app
from flask_frame.api.request import get_request_param
from flask_frame.extension.database import db
from flask_frame.api.exception import ResourceError


# 配置
config: FlaskFrameConfig = {
    "PRODUCT_KEY": "example_service",
    "SQLALCHEMY_DATABASE_URI": "postgresql://postgres:password@localhost:5432/example_db",
    "DB_SCHEMA": "public",
    "REDIS_URL": "redis://localhost:6379",
    "ENABLED_EXTENSION": ["database", "redis", "lock", "permission"],
    "AUTO_UPDATE": False,
    "CHECK_API": False,
}

# 创建应用
app = create_app({"default": config})

# 注册蓝图
example_bp = Blueprint("example", __name__, url_prefix="/api/example")


@example_bp.route("/list", methods=["GET"])
def list_items():
    """查询列表接口示例"""
    # ORM 查询
    # items = db.session.query(Item).all()
    
    # 返回响应
    return Response(data={"items": [], "total": 0}).make_flask_response()


@example_bp.route("/create", methods=["POST"])
def create_item():
    """创建接口示例"""
    params, _ = get_request_param()
    
    name = params.get("name")
    if not name:
        raise ResourceError(description="缺少 name 参数", code=400)
    
    # 创建记录
    # item = Item(name=name)
    # db.session.add(item)
    # 不需要手动 commit，teardown_request 自动提交
    
    return Response(data={"id": 1, "name": name}).make_flask_response()


@example_bp.route("/update/<int:item_id>", methods=["PUT"])
def update_item(item_id: int):
    """更新接口示例"""
    params, _ = get_request_param()
    
    # 更新记录
    # item = db.session.query(Item).filter(Item.id == item_id).first()
    # if not item:
    #     raise ResourceError(description="记录不存在", code=404)
    # item.name = params.get("name", item.name)
    
    return Response(message="更新成功").make_flask_response()


@example_bp.route("/delete/<int:item_id>", methods=["DELETE"])
def delete_item(item_id: int):
    """删除接口示例"""
    # db.session.query(Item).filter(Item.id == item_id).delete()
    
    return Response(message="删除成功").make_flask_response()


app.register_blueprint(example_bp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)