import os
import time

WINDOWS = "windows"
LINUX = "linux"
SYSTEM = WINDOWS

try:
    import fcntl

    # 如果能导入 fcntl，说明运行环境为类 Unix（如 Linux / macOS）
    # If fcntl is importable, treat the system as POSIX-like (Linux/macOS).
    SYSTEM = LINUX
except ModuleNotFoundError:
    # Windows 系统没有 fcntl 模块；保留 SYSTEM 为 WINDOWS
    # On Windows fcntl is not available; keep SYSTEM as WINDOWS.
    ...


class FileLock(object):
    """
    文件锁实现（跨平台），根据平台选择不同的锁实现策略。

    - Windows: 通过创建/删除锁文件表示持有锁（简单但存在短时竞争窗口）。
    - Linux/类 Unix: 使用 fcntl.flock 对文件描述符加排他锁（更安全的进程间锁）。

    参数:
        lock_file (str): 锁文件名（相对路径或文件名）。
        timeout (int|float): 超时时间（秒），超过该时间会认为锁已过期并可重试获取。
    """

    def __init__(self, lock_file="FLASK_LOCK", timeout=600):
        # 根据运行系统选择锁文件目录（Windows 使用环境变量 tmp，否则使用当前目录）
        if SYSTEM == WINDOWS:
            lock_dir = os.environ["tmp"]
        else:
            lock_dir = "./"

        self.lock_dir = lock_dir
        self.file = os.path.join(lock_dir, lock_file)
        self.timeout = timeout
        self._fn = None

    def locked(self):
        """判断锁是否已经被持有（存在且未超时）。返回 True/False。

        如果锁文件不存在则返回 False。
        如果存在但已超过超时时间，则会尝试释放该锁并返回 False。
        """
        if not os.path.exists(self.file):
            return False

        # 检查锁文件是否超时，超时则释放并视为未被占用
        exist_seconds = get_file_exist_seconds(self.file)
        if exist_seconds > self.timeout:
            self.release()
            return False

        # 锁文件存在且未超时，认为被占用
        return True

    def acquire(self):
        """请求并持有锁。阻塞直到获取到锁。"""
        if SYSTEM == WINDOWS:
            # Windows 通过文件是否存在来判断锁
            while self.locked():
                time.sleep(1)  # 等待 1 秒后重试
                continue

            # 创建锁文件表示占用
            with open(self.file, "w") as f:
                f.write("1")
        else:
            # Linux/类 Unix 使用 fcntl 排他锁（fcntl.flock）
            self._fn = open(self.file, "w")
            fcntl.flock(self._fn.fileno(), fcntl.LOCK_EX)
            # 标记文件内容（可选）
            self._fn.write("1")

    def release(self):
        """释放锁：关闭文件描述符（若有）并删除锁文件。"""
        try:
            if SYSTEM == WINDOWS:
                # Windows 通过删除锁文件释放锁
                if os.path.exists(self.file):
                    os.remove(self.file)
            else:
                # POSIX：关闭文件句柄并删除锁文件（fcntl 锁随文件描述符关闭而释放）
                if self._fn:
                    self._fn.close()
                if os.path.exists(self.file):
                    os.remove(self.file)
        except:
            # 捕获并忽略任何清理时的异常（确保调用方不会因释放失败而崩溃）
            ...

def get_file_exist_seconds(file_path):
    """
    返回文件最后修改时间距现在的秒数（time.time() - mtime）。

    在文件不存在或无法读取修改时间的情况下，返回 float('inf') 表示无法获取存在时间，
    这样上层逻辑（例如 locked()）会认为锁已过期并可释放/重试获取。

    注意:
    - 在多线程或并发情况下，文件可能瞬间被删除，调用 os.path.getmtime 时会抛出异常；
      本函数捕获此类异常并返回 float('inf')，以增强鲁棒性。
    """
    try:
        if not os.path.exists(file_path):
            # 文件已不存在，视为超时（返回无穷大）
            return float("inf")
        return time.time() - os.path.getmtime(file_path)
    except (FileNotFoundError, PermissionError, OSError):
        # 文件在检查或读取时被删除或不可访问，视为已过期
        return float("inf")
