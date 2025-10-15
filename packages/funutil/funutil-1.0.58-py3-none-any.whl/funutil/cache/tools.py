from cachetools import FIFOCache, LFUCache, LRUCache, RRCache, TTLCache, cached

__all__ = ["cache", "lru_cache", "ttl_cache", "lfu_cache", "fifo_cache", "rr_cache"]


def cache(func, /):
    print(func.__name__)
    return cached(LRUCache(maxsize=100)).__call__(func)


def ttl_cache(maxsize=1000):
    """
    TTLCache: the TTL cache will automatically remove the element in the cache that has expired.
    TTLCache：TTL 缓存会自动移除已过期的缓存元素。
    """
    return lambda func: cached(TTLCache(maxsize=maxsize, ttl=60)).__call__(func)


def lru_cache(maxsize=1000):
    """
    LRUCache: the LRU cache will remove the element in the cache that has not been accessed in the longest time.
    LRUCache：LRU 缓存会移除缓存中自上次访问以来时间最长的元素。
    """
    return lambda func: cached(LRUCache(maxsize=maxsize)).__call__(func)


def lfu_cache(maxsize=1000):
    """
    LFUCache: the LFU cache will remove the element in the cache that has been accessed the least, regardless of time.
    LFUCache：LFU 缓存会移除缓存中访问次数最少的元素，不论其访问时间。
    """
    return lambda func: cached(LFUCache(maxsize=maxsize)).__call__(func)


def fifo_cache(maxsize=1000):
    """
    FIFOCache: the FIFO cache will remove the element that has been in the cache the longest.
    FIFOCache：FIFO 缓存将移除在缓存中停留时间最长的元素。
    """
    return lambda func: cached(FIFOCache(maxsize=maxsize)).__call__(func)


def rr_cache(maxsize=1000):
    """
    RRCache: the RR cache will choose randomly element to remove it to make space when necessary.
    RRCache: RR 缓存会在必要时随机选择一个元素进行移除，以腾出空间。
    """
    return lambda func: cached(RRCache(maxsize=maxsize)).__call__(func)
