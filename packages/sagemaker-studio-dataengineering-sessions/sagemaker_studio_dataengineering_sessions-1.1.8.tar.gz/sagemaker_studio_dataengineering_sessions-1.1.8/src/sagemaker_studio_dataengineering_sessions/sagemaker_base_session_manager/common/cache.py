import functools
import time

def ttl_cache(ttl_seconds=30):
    def decorator(func):
        cache = {}
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = time.time()
            result = None
            # valid cache result
            if key in cache and now - cache[key]['time'] < ttl_seconds:
                result = cache[key]['value']
            else:
                result = func(*args, **kwargs)
                cache[key] = {'value': result, 'time': now}
            return result
        
        def clear_cache():
            cache.clear()

        wrapper.clear_cache = clear_cache
        return wrapper
    return decorator