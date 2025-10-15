"""
WARNING: DO NOT ABUSE !!!

Cache is stored on disk at the location specified by `cache_dir`,
and is by default deleted after 14 days of inactivity.

Since the cache is saved on disk, it will persist across kernel or
computer restarts. However, this may introduce a risk of computation
errors.

Additionally, because the cache is stored on disk, using it might
be less efficient than recomputing when the input data or function
output is very large.

Thus, caching is generally most effective for time-consuming
computations where the input and output data sizes are relatively small.
"""


import os
import shutil
import inspect
import pickle
import time

from glob import glob
from functools import wraps
from hashlib import md5


cache_dir = os.path.join(os.path.dirname(__file__), '__hduq_cache__/')
expiration_time = 14 * 24 * 60 * 60

if not os.path.exists(cache_dir):
    os.mkdir(cache_dir)


__all__ = [
    'clean_all_cache',
    'clean_expired_cache',
    'open_cache_dir',
    'cache'
]


def extract_timestamp(file_path):
    base_name = os.path.basename(file_path)
    timestamp = base_name.split('_')[1].split('.pkl')[0]
    return int(timestamp)


def find_cache(hash_key):
    time_stamp = int(time.time())
    prefix_name = os.path.join(cache_dir, f'{hash_key}_*')
    cache_file = glob(prefix_name)

    if len(cache_file) == 0:
        cache_file = os.path.join(cache_dir, f'{hash_key}_{time_stamp}.pkl')
        return cache_file, False
    
    elif len(cache_file) == 1:
        cache_file = cache_file[0]
        return cache_file, True
    
    else:
        raise


def update_timestamp(cache_file):
    time_stamp = int(time.time())
    base_name = os.path.basename(cache_file)
    hash_key = base_name.split('_')[0]
    new_name = f'{hash_key}_{time_stamp}.pkl'
    os.rename(cache_file, os.path.join(cache_dir, new_name))
    


def open_cache_dir():
    import platform
    if platform.system() == 'Windows':
        os.system('start ' + cache_dir)
    else:
        os.system('open ' + cache_dir)


def clean_all_cache():
    shutil.rmtree(cache_dir)
    os.mkdir(cache_dir)
    print('done')


def clean_expired_cache():
    now = int(time.time())
    for file_name in os.listdir(cache_dir):
        file_path = os.path.join(cache_dir, file_name)
        
        if file_name.endswith('.pkl'):
            try:
                timestamp = extract_timestamp(file_path)
                if now - timestamp > expiration_time:
                    os.remove(file_path)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")


def cache(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        abspath = lambda p: os.path.abspath(os.path.normpath(p))
        
        args = tuple(
            abspath(arg) if isinstance(arg, str) and os.path.isfile(arg) else arg
            for arg in args
        )

        kwargs = {
            k: abspath(v) if isinstance(v, str) and os.path.isfile(v) else v
            for k, v in kwargs.items()
        }

        cache_key = str(inspect.getsource(func)) + str(func.__name__) + str(args) + str(kwargs)
        cache_key = cache_key.encode('utf-8')
        hash_key = md5(cache_key).hexdigest()
        
        cache_file, success = find_cache(hash_key)
            
        if success and os.path.isfile(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    result = pickle.load(f)
                update_timestamp(cache_file)
                print('cache hit: reading result from cache file')
                return result
            except (EOFError, pickle.UnpicklingError, ValueError):
                os.remove(cache_file)
            
        result = func(*args, **kwargs)
        with open(cache_file, 'wb') as f:
            pickle.dump(result, f)
        return result
    
    return wrapper
