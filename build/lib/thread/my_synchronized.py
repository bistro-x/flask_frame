from functools import wraps
from threading import Lock

default_lock = Lock()
lock_list = {'default': Lock()}


def synchronized(func=None, obj=None):
    if func is not None:
        @wraps(func)
        def wrapper(*args, **kwargs):
            lock = lock_list['default']
            lock.acquire()
            try:
                return func(*args, **kwargs)
            finally:
                lock.release()

        return wrapper
    if obj is not None:
        cur_id = id(obj)
        default_lock.acquire()
        try:
            current_lock = lock_list.get(id(obj), None)
            if current_lock is None:
                current_lock = Lock()
                lock_list[cur_id] = current_lock
        finally:
            default_lock.release()

        def decorator(func):
            def wrapper(*args, **kwargs):
                current_lock.acquire()
                try:
                    return func(*args, **kwargs)
                finally:
                    current_lock.release()

            return wrapper

        return decorator
