"""
文件锁实现（跨平台），用于多进程/多线程场景下的互斥控制。

锁机制说明：

**Linux/macOS (POSIX 系统)：**
    使用 fcntl.flock() 系统调用，这是内核级的文件锁：
    - LOCK_EX: 排他锁，同一时间只有一个进程能持有
    - 锁绑定到文件描述符，进程退出时内核自动释放（防止死锁）
    - 多进程安全：不同进程竞争同一锁文件时，内核保证只有一个成功

**Windows 系统：**
    通过文件存在性模拟锁（非原子操作，存在短暂竞争窗口）：
    - acquire(): 创建锁文件表示持有锁
    - release(): 删除锁文件表示释放锁
    - 防死锁机制：timeout 超时后自动释放，防止进程崩溃导致锁永久占用

**多线程场景：**
    本锁主要用于多进程互斥。同一进程内的多线程共享同一个 FileLock 实例时，
    需要额外加 threading.Lock() 包装，否则线程间无法互斥。

使用示例：
    lock = FileLock("my_operation", timeout=60)
    lock.acquire()
    try:
        # 执行需要互斥的操作
        ...
    finally:
        lock.release()
"""
import os
import time

WINDOWS = "windows"
LINUX = "linux"
SYSTEM = WINDOWS

try:
    import fcntl
    # fcntl 是 POSIX 系统特有的模块，导入成功说明运行在 Linux/macOS
    SYSTEM = LINUX
except ModuleNotFoundError:
    # Windows 没有 fcntl，使用文件存在性模拟锁
    ...


class FileLock(object):
    """
    跨平台文件锁，用于多进程互斥控制。

    实现原理：
        Linux/macOS: fcntl.flock() 内核级锁，进程退出自动释放
        Windows: 文件存在性模拟锁，timeout 防死锁

    Args:
        lock_file: 锁文件名，建议使用操作名作为文件名（如 "init-db"、"update-cache"）。
        timeout: 超时时间（秒），超过此时间视为锁过期可重新获取。
                 用于防止进程崩溃后锁永久占用。

    Example:
        lock = FileLock("database_init", timeout=120)
        if not lock.locked():
            lock.acquire()
            try:
                init_database()
            finally:
                lock.release()
    """

    def __init__(self, lock_file: str = "FLASK_LOCK", timeout: int | float = 600):
        # Windows 使用临时目录，Linux 使用当前目录
        if SYSTEM == WINDOWS:
            lock_dir = os.environ.get("tmp", "./")
        else:
            lock_dir = "./"

        self.lock_dir = lock_dir
        self.file = os.path.join(lock_dir, lock_file)
        self.timeout = timeout
        self._fn = None  # Linux 下持有文件描述符

    def locked(self) -> bool:
        """
        判断锁是否被占用。

        检查逻辑：
            1. 锁文件不存在 → 未被占用
            2. 锁文件存在但超过 timeout → 视为过期，自动释放后返回未被占用
            3. 锁文件存在且未超时 → 被占用

        Returns:
            True: 锁被占用（其他进程持有）
            False: 锁未被占用（可尝试 acquire）

        Note:
            超时机制防止进程崩溃导致的死锁：如果持有锁的进程崩溃未能 release，
            超时后其他进程可重新获取锁。
        """
        if not os.path.exists(self.file):
            return False

        exist_seconds = get_file_exist_seconds(self.file)
        if exist_seconds > self.timeout:
            # 锁已超时，强制释放（防止死锁）
            self.release()
            return False

        return True

    def acquire(self, blocking: bool = True) -> bool:
        """
        获取锁。

        Args:
            blocking: True 阻塞等待直到获取锁；False 立即返回结果。

        Returns:
            True: 成功获取锁
            False: 获取失败（blocking=False 且锁被占用）

        多进程竞争行为：
            Linux (fcntl): 内核保证只有一个进程成功获取排他锁，
                          其他进程阻塞等待或返回失败（LOCK_NB）
            Windows: 轮询等待锁文件消失，存在短暂竞争窗口（非原子操作）

        Example:
            # 阻塞模式
            lock.acquire()
            # 非阻塞模式
            if lock.acquire(blocking=False):
                # 获取成功
            else:
                # 锁被占用，跳过操作
        """
        if SYSTEM == WINDOWS:
            # Windows: 文件存在性模拟锁（非原子，有竞争窗口）
            if blocking:
                # 阻塞模式：轮询等待锁文件消失
                while self.locked():
                    time.sleep(1)

            # 创建锁文件表示持有锁
            with open(self.file, "w") as f:
                f.write("locked")
            return True

        else:
            # Linux/macOS: fcntl 内核级锁（原子操作，多进程安全）
            self._fn = open(self.file, "w")
            flag = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
            try:
                # LOCK_EX: 排他锁，同一时间只有一个进程能持有
                # LOCK_NB: 非阻塞模式，锁被占用时立即抛出 BlockingIOError
                fcntl.flock(self._fn.fileno(), flag)
            except (BlockingIOError, OSError):
                # 非阻塞模式下锁被占用，返回 False
                self._fn.close()
                self._fn = None
                return False
            self._fn.write("locked")
            return True

    def release(self) -> None:
        """
        释放锁。

        释放机制：
            Linux: 关闭文件描述符，内核自动释放 fcntl 锁
            Windows: 删除锁文件

        Note:
            进程退出时 Linux 内核会自动释放 fcntl 锁，即使未调用 release()。
            这是 fcntl 相比 Windows 文件锁的关键优势——防止进程崩溃导致死锁。

        Example:
            lock.acquire()
            try:
                do_something()
            finally:
                lock.release()  # 确保释放
        """
        try:
            if SYSTEM == WINDOWS:
                if os.path.exists(self.file):
                    os.remove(self.file)
            else:
                # fcntl 锁随文件描述符关闭自动释放
                if self._fn:
                    self._fn.close()
                    self._fn = None
                if os.path.exists(self.file):
                    os.remove(self.file)
        except Exception:
            # 忽略释放异常，防止调用方崩溃
            ...


def get_file_exist_seconds(file_path: str) -> float:
    """
    计算文件存在时间（秒）。

    Args:
        file_path: 文件路径。

    Returns:
        文件从最后修改到现在的秒数。
        文件不存在或读取失败时返回 float('inf')（视为已过期）。

    Note:
        多进程并发场景下，文件可能被其他进程删除，导致 getmtime 抛异常。
        返回 inf 可让上层 locked() 触发超时释放逻辑。
    """
    try:
        if not os.path.exists(file_path):
            return float("inf")
        return time.time() - os.path.getmtime(file_path)
    except (FileNotFoundError, PermissionError, OSError):
        return float("inf")