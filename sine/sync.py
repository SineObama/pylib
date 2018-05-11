
# coding: utf-8

'''
模拟其他语言的线程同步锁（函数装饰器），和获取可重复同步锁函数get。
可以看作锁定key对象，也可以把key视作键，使用字符串等。
key必须是hashable的，必须提供。
'''

import threading as _threading
import weakref as _weakref

_dLock = _threading.RLock()
_dict = {}
def _recycle(key):
    _dLock.acquire()
    if _dict.has_key(key):
        _dict.pop(key)
    _dLock.release()
    return

def synchronized(key):
    '''
    线程同步锁（函数装饰器）。
    可以把操作对象本身当做key，也可以是字符串之类的……
    '''
    lock = get(key)
    def _decorator(func):
        def _decorated(*args, **kw):
            lock.acquire()
            try:
                return func(*args, **kw)
            finally:
                lock.release()
        return _decorated
    return _decorator

def get(key):
    _dLock.acquire()
    try:
        _key = _weakref.ref(key)
        if not _dict.has_key(_key):
            _key = _weakref.ref(key, _recycle)
            _dict[_key] = _threading.RLock()
        return _dict[_key]
    except TypeError, e: # 不可创建弱引用（字符串等）
        if not _dict.has_key(key):
            _dict[key] = _threading.RLock()
        return _dict[key]
    finally:
        _dLock.release()

__all__ = ['synchronized', 'get']
