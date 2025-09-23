# python 线程池 用于异步数据处理和批量的i/o操作
# python中批量的计算操作不适合用多线程
from concurrent.futures import ThreadPoolExecutor


class dk_thread_pool(object):
    '工作线程池'
    executor = ThreadPoolExecutor(max_workers=5)  # 最大线程数设置为5

    # func 线程执行的函数 ，*args 是func函数的接口， call_back是回调函数
    def submit(self, func, call_back, *args):
        # 任务池加载任务
        task = self.executor.submit(func, *args)
        if call_back:
            task.add_done_callback(call_back)

    def join(self):
        """
        等待所有任务完成
        """
        self.executor.shutdown(wait=True)  # 等待所有线程完成

    def _worker(self):
        """
        线程执行任务的主循环
        """
        while True:
            func, args, kwargs = self.tasks.get()
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"线程池任务异常: {e}")
            self.tasks.task_done()

    def submit(self, func, *args, **kwargs):
        """
        提交任务到线程池
        :param func: 任务函数
        :param args: 任务参数
        :param kwargs: 任务关键字参数
        """
        self.tasks.put((func, args, kwargs))

    def _init_threads(self):
        import threading  # 补充导入线程模块
        """
        创建并启动线程
        """
        for _ in range(self.max_workers):
            t = threading.Thread(target=self._worker)
            t.daemon = True  # 设置为守护线程
            t.start()
            self.threads.append(t)


# 单例模式
dk_thread_pool = dk_thread_pool()
