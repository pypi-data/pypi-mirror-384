import json
import time
from datetime import datetime
from functools import wraps
from threading import Timer


class CacheDump:
    def __init__(self, elapsed=10):
        """
        :param elapsed: time to dump the cache
        """
        self.dump_data = {}
        self.elapsed = elapsed
        self.last_dump_time = time.time()

    def add(self, key, value, dump_file=None):
        self.dump_data[key] = value
        self.dump(dump_file)

    def dump(self, dump_file=None):
        if dump_file is None:
            return
        if time.time() - self.last_dump_time < self.elapsed:
            return
        dump_data = {
            "data": self.dump_data,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(dump_file, "w", encoding="utf-8") as out_data:
            out_data.write(json.dumps(dump_data, indent=4, sort_keys=True))
        self.last_dump_time = time.time()


class RunTimer:
    cache_dump = CacheDump(elapsed=3)

    def __init__(self, time_func=time.perf_counter, dump_file="runtime.log"):
        self.counter = 0
        self.elapsed = 0
        self.dump_file = dump_file
        self.time_func = time_func
        self.time_snapshot = None

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.start()
            res = func(*args, **kwargs)
            self.stop()
            if self.dump_file is not None:
                key = f"{func.__code__.co_flags}-{func.__name__}"
                value = {
                    "counter": self.counter,
                    "elapsed": self.elapsed,
                    "average": self.elapsed / self.counter,
                }
                self.cache_dump.add(key, value, dump_file=self.dump_file)
            return res

        return wrapper

    def start(self):
        self.time_snapshot = time.time()

    def stop(self):
        self.elapsed += time.time() - self.time_snapshot
        self.time_snapshot = None
        self.counter += 1

    def __str__(self):
        return f"{self.counter}, {self.elapsed / self.counter}s"

    @property
    def running(self) -> bool:
        return self.time_snapshot is not None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return True


class RepeatingTimer(Timer):
    def run(self):
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)


def run_timer(func):
    return RunTimer().__call__(func)
