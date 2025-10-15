import hashlib
import inspect
import os
import pickle
from functools import cache, cached_property, lru_cache, wraps

from funutil.util.log import get_logger

logger = get_logger("funutil")

__all__ = ["lru_cache", "PickleCache", "pkl_cache", "cache", "cached_property"]


class PickleCache:
    def __init__(self, cache_key, cache_dir=".cache", is_cache="cache", printf=False):
        self.cache_key = cache_key
        self.cache_dir = cache_dir
        self.is_cache = is_cache

        self.printf = printf

    def log(self, msg):
        if self.printf:
            print(msg)
        logger.debug(msg)

    def get_cache_file(self, key):
        key = str(key)
        # 使用 MD5 值作为缓存文件名
        return os.path.join(
            self.cache_dir, hashlib.md5(key.encode()).hexdigest() + ".pkl"
        )

    @staticmethod
    def load_cache(cache_file):
        try:
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        except (FileNotFoundError, pickle.PickleError):
            return None

    def save_cache(self, cache_file, data):
        os.makedirs(self.cache_dir, exist_ok=True)
        ignore_file = f"{self.cache_dir}/.gitignore"
        if not os.path.exists(ignore_file):
            with open(ignore_file, "w") as f:
                f.write("*")

        with open(cache_file, "wb") as f:
            pickle.dump(data, f)

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i, (name, param) in enumerate(
                list(inspect.signature(func).parameters.items())
            ):
                if name in kwargs.keys():
                    continue
                kwargs[name] = args[i] if i < len(args) else param.default

            is_cache = kwargs.get(self.is_cache, True)
            cache_key = kwargs.get(
                self.cache_key, ""
            )  # 假设输入参数中有一个名为 '${cache_key}' 的字段
            is_cache = is_cache and cache_key is not None
            cache_file = (
                self.get_cache_file(cache_key) if is_cache else None
            )  # 将 SQL 语句作为缓存的键

            if is_cache:
                # 检查缓存中是否存在该键
                cached_result = self.load_cache(cache_file)
                if cached_result is not None:
                    self.log(
                        f"Cache hit for function '{func.__name__}' with key: {cache_key}"
                    )
                    return cached_result

            # 如果没有缓存，执行函数并缓存结果
            result = func(**kwargs)
            if is_cache:
                self.save_cache(cache_file, result)
                self.log(
                    f"Cache data for function '{func.__name__}' with key: {cache_key}"
                )
            return result

        return wrapper


def pkl_cache(
    cache_key, cache_dir=".cache", is_cache="cache", printf=False, *args, **kwargs
):
    return PickleCache(cache_key, cache_dir, is_cache, printf=printf, *args, **kwargs)
