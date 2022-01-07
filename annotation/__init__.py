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


def profile(func):
    """
    生成方法的调用性能报告
    路径在 log下 prifle_方法名_时间搓
    """

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        import time

        profiler = Profiler()
        profiler.start()

        result = None
        with profiler:
            result = func(*args, **kwargs)
        profiler.output_text(f"./log/prfile_{func.__name__}_{str(time.time())}.txt")
        return result

    return new_func
