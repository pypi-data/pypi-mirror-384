from collections import OrderedDict
from threading import Thread


def thread_task(task_list: list, result_type="list", error_ignore=False):
    class _MyThread(Thread):

        def __init__(self, target, error_ignore=False, *args, **kwargs):
            super(_MyThread, self).__init__()
            self.error_ignore = error_ignore
            self.func = target
            self.func_name = target.__qualname__
            self.args = args
            self._kwargs = kwargs
            self.result = None

        def run(self):
            try:
                self.result = self.func(*self.args, **self._kwargs)
            except Exception as e:
                if not self.error_ignore:
                    raise e

        def get_result(self):
            return self.result

    name_list = list()
    thread_list = []
    for i, task in enumerate(task_list):
        if isinstance(task, list):
            name_list.append(i)
            if len(task) == 1:
                thread_list.append(_MyThread(target=task[0], error_ignore=error_ignore))
            elif len(task) == 2:
                if isinstance(task[1], list) or isinstance(task[1], tuple):
                    thread_list.append(_MyThread(target=task[0], error_ignore=error_ignore, *task[1]))
                elif isinstance(task[1], dict):
                    thread_list.append(_MyThread(target=task[0], error_ignore=error_ignore, **task[1]))
            else:
                raise Exception("task format error")
        elif isinstance(task, dict):
            name = task.get("name") or i
            name_list.append(name)
            params = task.get("params") or {}
            thread_list.append(_MyThread(target=task.get("func"), error_ignore=error_ignore, **params))
        else:
            raise Exception("task_list is not list or dict")
    for j in thread_list:
        j.start()
    for t in thread_list:
        t.join()

    if result_type == "list":
        return [i.get_result() for i in thread_list]
    else:
        result = OrderedDict()
        for i, _thread in enumerate(thread_list):
            result.update(
                {name_list[i]: {"func": _thread.func_name, "name": name_list[i], "data": _thread.get_result()}})
        return result
