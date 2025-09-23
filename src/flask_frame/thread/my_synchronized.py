
# 导入装饰器工具和线程锁
from functools import wraps
from threading import Lock

# 默认锁对象
default_lock = Lock()
# 锁对象字典，支持多对象锁
lock_list = {'default': Lock()}



def synchronized(func=None, obj=None):
    """
    线程同步装饰器：可用于函数或对象方法的线程安全保护。
    用法：
        @synchronized
        def foo():
            ...
        @synchronized(obj=some_obj)
        def bar():
            ...
    """
    if func is not None:
        # 对单个函数加锁
        @wraps(func)
        def wrapper(*args, **kwargs):
            lock = lock_list['default']
            lock.acquire()  # 加锁
            try:
                return func(*args, **kwargs)
            finally:
                lock.release()  # 释放锁

        return wrapper
    if obj is not None:
        # 对指定对象加锁
        cur_id = id(obj)
        default_lock.acquire()  # 保护锁字典的并发访问
        try:
            current_lock = lock_list.get(cur_id, None)
            if current_lock is None:
                current_lock = Lock()
                lock_list[cur_id] = current_lock
        finally:
            default_lock.release()

        def decorator(func):
            def wrapper(*args, **kwargs):
                current_lock.acquire()  # 加锁
                try:
                    return func(*args, **kwargs)
                finally:
                    current_lock.release()  # 释放锁

            return wrapper

        return decorator
