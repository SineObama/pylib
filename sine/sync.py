
# coding: utf-8

import threading as _threading
import weakref as _weakref

_dict = {}
def _recycle(key):
    if _dict.has_key(key):
        _dict.pop(key)
    return

def synchronized(key):
    '''
    函数装饰器（key值对应的线程同步锁）。
    key必须是hashable。
    可以把操作对象本身当做key，也可以是字符串之类的……
    将创建key的弱引用。
    '''
    try:
        _key = _weakref.ref(key)
        if not _dict.has_key(_key):
            _key = _weakref.ref(key, _recycle)
            _dict[_key] = _threading.Lock()
        lock = _dict[_key]
    except Exception, e:
        if not _dict.has_key(key):
            _dict[key] = _threading.Lock()
        lock = _dict[key]
    def _decorator(func):
        def _decorated(*args, **kw):
            lock.acquire()
            try:
                rtn = func(*args, **kw)
            finally:
                lock.release()
            return rtn
        return _decorated
    return _decorator

def acquire(key):
    try:
        _key = _weakref.ref(key)
        if not _dict.has_key(_key):
            _key = _weakref.ref(key, _recycle)
            _dict[_key] = _threading.Lock()
        lock = _dict[_key]
    except TypeError, e:
        if not _dict.has_key(key):
            _dict[key] = _threading.Lock()
        lock = _dict[key]
    lock.acquire()
    return

def release(key):
    try:
        key = _weakref.ref(key)
    except TypeError, e:
        pass 
    if _dict.has_key(key):
        lock = _dict[key]
        lock.release()
    return

__all__ = ['synchronized', 'acquire', 'release']
