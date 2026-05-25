"""
装饰器模块。
提供两种装饰器：
  - deprecated: 标记已废弃的函数，调用时发出 DeprecationWarning
  - profile: 性能分析装饰器，超过阈值时生成调用报告文件
"""
import warnings
import functools
from pyinstrument import Profiler

__all__ = ["deprecated", "profile"]


def deprecated(func):
    """
    标记函数已废弃的装饰器。调用时会发出 DeprecationWarning 提醒迁移。
    
    Args:
        func: 要标记的函数。
    
    Returns:
        function: 包装后的函数，调用时会发出警告。
    """

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter("always", DeprecationWarning)  # turn off filter
        warnings.warn(
            "Call to deprecated function {}.".format(func.__name__),
            category=DeprecationWarning,
            stacklevel=2,
        )
        warnings.simplefilter("default", DeprecationWarning)  # reset filter
        return func(*args, **kwargs)

    # 返回
    return new_func


def profile(timeout=1000):
    """
    性能分析装饰器。当函数执行时间超过阈值时，生成调用报告文件。
    仅在请求上下文中且 URL 参数不含 profile、且 PROFILE 配置为真时生效。
    
    Args:
        timeout: 超时阈值（毫秒），超过此值才会生成报告。
    
    Returns:
        function: 装饰器函数。
    """

    def decorate(func):
        @functools.wraps(func)
        def new_func(*args, **kwargs):
            import time
            from flask import has_request_context, g, current_app, request

            if (
                not has_request_context()
                or "profile" in request.args
                or not current_app.config.get("PROFILE")
                or current_app.config.get("PROFILE") == "False"
            ):
                return func(*args, **kwargs)

            g.profiler = Profiler() if "profiler" not in g else g.profiler
            result = None
            with g.profiler:
                result = func(*args, **kwargs)

            # 写入文件
            if g.profiler._last_session.duration * 1000 > timeout:
                time_format = time.strftime("%Y%m%d_%H:%M:%S", time.localtime())
                file_path = f"./log/profile_{func.__name__}_{time_format}.txt"
                profile_file = open(file_path, "w")
                with profile_file:
                    profile_file.write(g.profiler.output_text())

            # 返回
            return result

        return new_func

    return decorate
