import functools
import traceback


def retry(num=3, check_func=None):

    """
    重试装饰器
    :param num: 重试次数
    :param check_func: 校验结果函数
    example:
        def check_func(res):
            assert res == 1111


        class A:
            @retry(check_func=check_func)
            def test(self):
                return 1111

            @staticmethod
            @retry(check_func=check_func)
            def test2():
                return 1111

            @classmethod
            @retry(check_func=check_func)
            def test3(cls):
                return 1111


        @retry(check_func=check_func)
        def test4():
            return 1111
    """

    def _retry(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = None
            for i in range(num):
                try:
                    result = func(*args, **kwargs)
                    if check_func is not None:
                        if check_func(result):
                            break
                except Exception as e:
                    traceback.print_exc()
                    if i == num - 1:
                        raise e
            return result

        return wrapper

    return _retry
