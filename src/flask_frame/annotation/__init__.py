import warnings
import functools
from pyinstrument import Profiler


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""

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

    return new_func


def profile(timeout=1000):
    """
    生成方法的调用性能报告
    路径在 log下 prifle_方法名_时间搓
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
