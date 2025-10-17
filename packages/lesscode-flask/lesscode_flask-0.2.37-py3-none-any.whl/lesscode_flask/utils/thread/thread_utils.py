import threading
from typing import List

from flask import copy_current_request_context


class FlaskThread:
    def __init__(self, target, args=None, kwargs=None):
        self.target = target
        self.args = args or []
        self.kwargs = kwargs or dict()


def wrapper(_func, _args, _kwargs, _result: list = None, _lock=None, _is_throw_error=True):
    @copy_current_request_context
    def _thread_func():
        try:
            res = _func(*_args, **_kwargs)
            if _result is not None and isinstance(_result, list):
                if _lock:
                    with _lock:
                        _result.append(res)
                else:
                    _result.append(res)
        except Exception as e:
            if _is_throw_error:
                raise e
            else:
                if _result is not None and isinstance(_result, list):
                    if _lock:
                        with _lock:
                            _result.append(None)
                    else:
                        _result.append(None)

    return _thread_func


def run_in_thread(func_list: List[FlaskThread], is_throw_error=False, is_lock=True):
    results = []
    threads = []
    result_locks = []
    for obj in func_list:
        target = obj.target
        args = obj.args or []
        kwargs = obj.kwargs or dict()
        result = []
        if is_lock:
            lock = threading.Lock()
            result_locks.append(lock)
        else:
            lock = None
            result_locks.append(lock)
        thread_func = wrapper(_func=target, _args=args, _kwargs=kwargs, _result=result, _lock=lock,
                              _is_throw_error=is_throw_error)
        t = threading.Thread(target=thread_func)
        threads.append(t)
        results.append(result)
        t.start()

    for t in threads:
        t.join()

    final_results = []
    for result, lock in zip(results, result_locks):
        if is_lock:
            with lock:
                final_results.append(result[0])
        else:
            final_results.append(result[0])
    return final_results


def run_in_background(func_list: List[FlaskThread], is_throw_error=False, is_lock=False):
    thread = threading.Thread(target=wrapper(_func=run_in_thread,
                                             _args=[],
                                             _kwargs=dict(func_list=func_list, is_throw_error=is_throw_error,
                                                          is_lock=is_lock)))
    thread.start()
    return True
