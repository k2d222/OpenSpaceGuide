import os
import pickle
from functools import wraps
import hashlib


class Persistent:
    def __init__(self, cls, cache_dir='cache'):
        self.cls = cls
        self.cache_dir = cache_dir


    def __call__(self, *args, **kwargs):
        return PersistentInstance(self.cls(*args, **kwargs), self.cache_dir)


class PersistentInstance:
    def __init__(self, instance, cache_dir='cache'):
        self._cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        self._instance = instance


    def _hash(self, func_name, args, kwargs):
        hasher = hashlib.sha256()
        hasher.update(pickle.dumps((func_name, args, tuple(kwargs.items()))))
        return hasher.hexdigest()


    def _cache_path(self, func_name, args, kwargs):
        filename = f"{func_name}_{self._hash(func_name, args, kwargs)}.pkl" # TODO: depends on the instance state too
        return os.path.join(self._cache_dir, filename)


    def _cache_result(self, func_name, args, kwargs, result):
        path = self._cache_path(func_name, args, kwargs)
        try:
            with open(path, 'wb') as f:
                pickle.dump(result, f)
        except pickle.PickleError:
            print(f'cannot cache {func_name}')
            os.remove(path)


    def _load_cached_result(self, func_name, args, kwargs):
        cache_path = self._cache_path(func_name, args, kwargs)

        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                return pickle.load(f)

        return None


    def __getattr__(self, name):
        orig_attr = getattr(self._instance, name)
        
        if callable(orig_attr):
            @wraps(orig_attr)
            def hooked(*args, **kwargs):
                cached_result = self._load_cached_result(name, args, kwargs)
                if cached_result is not None:
                    print(f"using cached result for {name}")
                    return cached_result
                else:
                    print(f"proxying {name}")
                    result = orig_attr(*args, **kwargs)
                    self._cache_result(name, args, kwargs, result)
                    return result
            
            return hooked

        elif hasattr(orig_attr, '__dict__'):
            return PersistentInstance(orig_attr, self._cache_dir)

        else:
            return orig_attr
