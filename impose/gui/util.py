import functools
import threading
import time


class MethodCallRateRestricter:
    def __init__(self, max_rate=10):
        self.methods = []
        self.tdiff = 1 / max_rate
        self._keep_running = True
        self.thread_runner = threading.Thread(target=self.request_check,
                                              daemon=True)
        self.thread_runner.start()

    def add_method(self, parent, method):

        method_data = {"request_args": None,
                       "called_last": 0}

        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            method_data["request_args"] = (args, kwargs)

        wrapper.original_method = method

        self.methods.append((method, parent, method_data))
        setattr(parent, method.__name__, wrapper)

    def close(self):
        self._keep_running = False

    def request_check(self):
        while self._keep_running:
            for method, parent, method_data in self.methods:
                if method_data["request_args"] is not None:
                    # The method call has been requested
                    now = time.perf_counter()
                    last_call = method_data["called_last"]
                    if now - last_call > self.tdiff:
                        # The last call is long enough ago
                        args, kwargs = method_data["request_args"]
                        method_data["called_last"] = time.perf_counter()
                        method(*args, **kwargs)
            time.sleep(.1)
