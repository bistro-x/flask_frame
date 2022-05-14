# python 线程池 用于异步数据处理和批量的i/o操作
# python中批量的计算操作不适合用多线程
from concurrent.futures import ThreadPoolExecutor


class dk_thread_pool(object):
    '工作线程池'
    executor = ThreadPoolExecutor(max_workers=2)

    # func 线程执行的函数 ，*args 是func函数的接口， call_back是回调函数
    def submit(self, func, call_back, *args):
        # 任务池加载任务
        task = self.executor.submit(func, *args)
        if call_back:
            task.add_done_callback(call_back)


# 单例模式
dk_thread_pool = dk_thread_pool()
