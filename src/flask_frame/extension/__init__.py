from importlib import import_module

__all__ = ["init_app"]


def init_app(app, **kwargs):
    """
    插件系统入口：遍历 ENABLED_EXTENSION 配置列表，动态导入并初始化每个插件。
    每个插件必须实现 init_app(app, **kwargs) 方法。
    插件名称对应 extension/ 目录下的模块名（.py 文件或子包目录）。
    """
    for module_name in app.config['ENABLED_EXTENSION']:
        import_module('.%s' % module_name, package=__name__).init_app(app, **kwargs)
