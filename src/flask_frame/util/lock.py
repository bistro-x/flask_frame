import os
import time

WINDOWS = "windows"
LINUX = "linux"
SYSTEM = WINDOWS

try:
    import fcntl

    SYSTEM = LINUX
except ModuleNotFoundError:
    ...


class FileLock(object):
    def __init__(self, lock_file="FLASK_LOCK", timeout=600):

        if SYSTEM == WINDOWS:
            lock_dir = os.environ["tmp"]
        else:
            lock_dir = "./"

        self.lock_dir = lock_dir
        self.file = os.path.join(lock_dir, lock_file)
        self.timeout = timeout
        self._fn = None

    def locked(self):
        """判断锁是否已经申请"""
        if not os.path.exists(self.file):
            return False
        if check_file(self.file) > self.timeout:
            self.release()
            return False
        return True

    def acquire(self):
        """请求锁"""
        if SYSTEM == WINDOWS:
            while self.locked():
                time.sleep(1)  # wait 10ms
                continue

            with open(self.file, "w") as f:
                f.write("1")
        else:
            self._fn = open(self.file, "w")
            fcntl.flock(self._fn.fileno(), fcntl.LOCK_EX)
            self._fn.write("1")

        
        
    def release(self):
        """释放锁"""
        try:
            if SYSTEM == WINDOWS:
                if os.path.exists(self.file):
                    os.remove(self.file)
            else:
                if self._fn:
                    self._fn.close()

                if os.path.exists(self.file):
                    os.remove(self.file)
        except:
            ...


def check_file(file_path):
    """检测文件的修改时间"""
    return time.time() - os.path.getmtime(file_path)
