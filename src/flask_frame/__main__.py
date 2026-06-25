# -*- coding: utf-8 -*-
"""python -m flask_frame sync_apifox --token xxx --project-id xxx"""
import argparse
import importlib
import sys


def _create_app_by_convention():
    """
    按约定自动创建 Flask 应用并生成 swagger spec。

    检测顺序：
    1. config 模块 → create_app(config)
    2. module 包 → module.init_app(app)（如果存在）
    3. context 模块 → context.init_app(app)（如果存在）
    4. flasgger → Swagger(app).get_apispecs()

    Returns:
        tuple: (app, swagger_spec)
    """
    from flask_frame.app import create_app

    # 1. 导入 config
    try:
        from config import config
    except ImportError:
        print("错误：未找到 config.py 或其中没有 config 变量", file=sys.stderr)
        sys.exit(1)

    # 2. 创建 app
    app = create_app(config)

    # 3. 尝试初始化 module（业务模块注册路由）
    try:
        import module
        if hasattr(module, "init_app"):
            module.init_app(app)
    except ImportError:
        pass

    # 4. 尝试初始化 context（应用上下文）
    try:
        import context as ctx
        if hasattr(ctx, "init_app"):
            ctx.init_app(app)
    except ImportError:
        pass

    # 5. 初始化 flasgger 生成 swagger spec
    try:
        from flasgger import Swagger
    except ImportError:
        print("错误：未安装 flasgger，请执行 pip install flasgger", file=sys.stderr)
        sys.exit(1)

    swagger_template = {
        "swagger": "2.0",
        "info": {"title": "API", "version": "1.0.0"},
    }
    swagger_config = {
        "specs": [{
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }]
    }
    swagger = Swagger(app, template=swagger_template, config=swagger_config)

    with app.app_context():
        spec = swagger.get_apispecs()

    return app, spec


def _import_factory(app_path: str):
    """
    从 "module:attr" 格式的路径导入对象。

    Args:
        app_path: 如 "app:create_apifox_app" 或 "run:app"。

    Returns:
        导入的对象。
    """
    if ":" not in app_path:
        print(f"错误：--app 格式应为 'module:attr'，收到: {app_path}", file=sys.stderr)
        sys.exit(1)

    module_path, attr_name = app_path.split(":", 1)
    try:
        mod = importlib.import_module(module_path)
    except ImportError as e:
        print(f"错误：无法导入模块 '{module_path}'：{e}", file=sys.stderr)
        sys.exit(1)

    try:
        return getattr(mod, attr_name)
    except AttributeError:
        print(f"错误：模块 '{module_path}' 中没有 '{attr_name}' 属性", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="flask_frame")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("sync_apifox", help="同步 API 文档到 Apifox")
    p.add_argument(
        "--app", default=None,
        help="自定义 app 工厂路径（格式 'module:attr'），默认按约定自动创建",
    )
    p.add_argument("--token", required=True, help="Apifox API Token")
    p.add_argument("--project-id", required=True, help="Apifox 项目 ID")
    p.add_argument("--title", default="API Documentation", help="API 标题")
    p.add_argument("--modules", nargs="+", default=None, help="按模块名过滤（如 inquiry quotation）")
    p.add_argument("--force", action="store_true", help="强制全量同步（忽略增量）")
    p.add_argument("--snapshot-dir", default=".sync_snapshot", help="快照目录")

    args = parser.parse_args()
    if args.command != "sync_apifox":
        parser.print_help()
        sys.exit(1)

    # 创建 app 和 swagger spec
    if args.app:
        factory = _import_factory(args.app)
        result = factory()
    else:
        result = _create_app_by_convention()

    if isinstance(result, tuple) and len(result) == 2:
        app, swagger_spec = result
    else:
        app = result
        swagger_spec = None

    from flask_frame.openapi import sync_to_apifox
    sync_to_apifox(
        app,
        token=args.token,
        project_id=args.project_id,
        title=args.title,
        modules=args.modules,
        swagger_spec=swagger_spec,
        force=args.force,
        snapshot_dir=args.snapshot_dir,
    )


if __name__ == "__main__":
    main()
