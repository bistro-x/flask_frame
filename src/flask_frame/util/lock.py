import os
import time

WINDOWS = "windows"
LINUX = "linux"
SYSTEM = WINDOWS

try:
    import fcntl

    # 如果能导入fcntl，说明是Linux系统
    SYSTEM = LINUX
except ModuleNotFoundError:
    # Windows系统没有fcntl
    ...


class FileLock(object):
    """
    文件锁实现，支持Windows和Linux
    """

    def __init__(self, lock_file="FLASK_LOCK", timeout=600):
        # 根据系统选择锁文件目录
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
        # 检查锁文件是否超时
        if check_file(self.file) > self.timeout:
            self.release()
            return False
        return True

    def acquire(self):
        """请求锁"""
        if SYSTEM == WINDOWS:
            # Windows通过文件存在与否实现锁
            while self.locked():
                time.sleep(1)  # wait 1s
                continue

            with open(self.file, "w") as f:
                f.write("1")
        else:
            # Linux使用fcntl加锁
            self._fn = open(self.file, "w")
            fcntl.flock(self._fn.fileno(), fcntl.LOCK_EX)
            self._fn.write("1")

    def release(self):
        """释放锁"""
        try:
            if SYSTEM == WINDOWS:
                # 删除锁文件
                if os.path.exists(self.file):
                    os.remove(self.file)
            else:
                # 关闭文件并删除锁文件
                if self._fn:
                    self._fn.close()
                if os.path.exists(self.file):
                    os.remove(self.file)
        except:
            ...


def check_file(file_path):
    """
    检测文件的修改时间，返回距离现在的秒数
    :param file_path: 文件路径
    :return: 距离现在的秒数
    """
    return time.time() - os.path.getmtime(file_path)
