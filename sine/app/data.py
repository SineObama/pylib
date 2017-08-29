# coding=utf-8
'''简单粗暴保证多线程安全
you should acquire() before get() and set(), and then release() after complete r/w
'''

import threading as __threading
__mutex = __threading.Lock()

__data = { }

def acquire():
    global __mutex
    return __mutex.acquire()

def set(data, key='__root'):
    __data[key] = data
    return

def get(key='__root'):
    if not __data.has_key(key):
        raise KeyError('no key ' + str(key))
    return __data[key]

def release():
    global __mutex
    return __mutex.release()