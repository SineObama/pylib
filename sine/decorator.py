# coding=utf-8

def paralleling(func):
    '''
    @Decorator

    use multi-thread to speed up (almost) unrelated work

    @Function
    
        @origin     deal(data, ...) with single piece of data
        @decorated  deal(@Iterable dataSet, ...) each piece of data will be treated in each thread
    '''
    import threading
    def helper(data,args,kwargs):
        func(data,*args,**kwargs)
    def decorated(dataSet, *args, **kwargs):
        threads = []
        for data in dataSet:
            t = threading.Thread(target=helper,args=(data,args,kwargs))
            t.setDaemon(True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    return decorated

def printTime(func):
    '''
    @Decorator

    print time info before and after the function
    '''
    from helpers import info
    def decorated(*args, **kwargs):
        info('begin')
        func(*args, **kwargs)
        info('end')
    return decorated

def acceptIterable(func):
    '''
    @Decorator

    make function to accept iterable data for its first Parameter.

    @Example

        @origin     printf(str, ...) prints string str
        @decorated  printf(@Iterable list, ...) prints a list of string.

    @Function

        accept @Iterable Parameter at the first position.
        e.g. list, array

    this just call the origin function for several times
    '''
    from collections import Iterable
    def decorated(data, *args, **kwargs):
        if not isinstance(data, Iterable):
            return func(data, *args, **kwargs)
        rtns = []
        for item in data:
            rtn = func(item, *args, **kwargs)
            rtns.append(rtn)
        return rtns
    return decorated

def acceptMultiIterable(stop_type=None, info_inject={}, max_depth=10):
    '''
    @Decorator (returned)

    make function to accept 'multi-dimensions' iterable data for its first Parameter.
    itertion stops when it's not iterable or meet the stop_type or meet max iteration depth.

        @Parameter stop_type a class, type, or a @Iterable set of them, or None

        @Parameter info_inject @dict mapping from info name to argument name
            available info:
            index: represent the iteration index

        @Parameter max_depth @int max iteration depth

        @Return truely @Decorator

    @Example

        @origin     printf(str, ...) prints string str
        @decorated  printf(@Iterable list, ...) prints a list of string.

    @Function

        accept 'multi' @Iterable Parameter at the first position.
        e.g. array of array (or two-dimension array)

        @Return list(s) of returned object by the origin function
    
    will recursively call @decorated function itself

    the parameters are use with a copy, so it will not change when it's changed by outside reference
    '''
    available_info = ['index']

    from collections import Iterable

    # parameter check
    # arg 1
    if stop_type != None:
        if isinstance(stop_type, Iterable):
            for i in stop_type:
                if type(i) != type:
                    raise TypeError('arg 1 stop_type has a none type value ' + str(i))
        else:
            if type(stop_type) != type:
                raise TypeError('arg 1 stop_type is not a type or Iterable')
    # arg 2
    if not isinstance(info_inject, dict):
        raise TypeError('arg 2 info_inject is not a dict')
    for k in info_inject:
        if k not in available_info:
            raise KeyError('unsupport key \'' + k + '\' in arg 2 info_inject')

    info_inject = info_inject.copy()

    if isinstance(stop_type, Iterable):
        stop_type = tuple(stop_type)
    if stop_type == None:
        meetStopType = lambda x : False
    else:
        meetStopType = lambda x : isinstance(x, stop_type)

    # store private info as a @dict in the @Parameter **kwargs with this key
    private_info_key = acceptMultiIterable.__module__ + '.' + acceptMultiIterable.__name__ + '.private_info'

    # clean private info and copy required ones into specified key
    def finalizeKwargs(kw):
        private_info = kw.pop(private_info_key)
        for k in info_inject:
            kw[info_inject.get(k, 'error_keyname')] = private_info.get(k, None)

    def decorator(func):
        def decorated(data, *args, **kwargs):

            # private info
            info = kwargs.setdefault(private_info_key, {})
            index = info.setdefault('index', [])

            # stop iteration and call the @origin directly
            if not isinstance(data, Iterable) or meetStopType(data) or len(index) >= max_depth:
                finalizeKwargs(kwargs)
                return func(data, *args, **kwargs)

            # iterate among data, recursive calls
            rtns = []
            index.append(0)
            for i, item in enumerate(data):
                index[len(index) - 1] = i
                rtn = decorated(item, *args, **kwargs)
                rtns.append(rtn)
            index.pop()
            return rtns

        return decorated
    return decorator

# 在A类中使用super(A...)...出现问题，因为A已经被更改，继承关系已经变了
# def singleton(c):
#     '''
#     singleton pattern
#     '''
#     _instance = [None, False]
#     class Singleton(c):
#         def __new__(clz, *args, **kw):
#             if _instance[0] == None:
#                 _instance[0] = object.__new__(clz, *args, **kw)
#             return _instance[0]
#         def __init__(self, *args, **kw):
#             if not _instance[1]:
#                 _instance[1] = True
#                 c.__init__(self, *args, **kw)
#     return Singleton

def singleton_autodel(C):
    '''
    singleton pattern

    do not use the class in the definition body (properties and methods) any more
    because it is changed to a function to get the instance
    always use 'self' in the methods
    I think this is ok because it is all about that instance
    if you use, there maybe a two-way reference, causing the __del__ will not be called
    '''
    from threading import Lock
    instances = [None, Lock()]
    def init_or_get_singleton(*args, **kw):
        instances[1].acquire()
        if not instances[0]:
            instances[0] = C(*args, **kw)
        instances[1].release()
        return instances[0]
    return init_or_get_singleton

# 似乎由于循环引用而无法自动调用析构函数
def singleton(C):
    '''
    singleton pattern

    it seems the gc will not collect this, __del__ will not be called automatically at termination
    due to a circle reference
    '''
    from types import MethodType
    from threading import Lock
    _instance = [None, False, Lock(), Lock()] # contain the instance and whether it is initialized, and theirs Lock
    _new = C.__new__
    _init = C.__init__
    def _singleton_new(clz, *args, **kw):
        _instance[2].acquire()
        if not _instance[0]:
            _instance[0] = _new(C, *args, **kw)
        _instance[2].release()
        return _instance[0]
    def _singleton_init(self, *args, **kw):
        _instance[3].acquire()
        if not _instance[1]:
            _instance[1] = True
            _init(self, *args, **kw)
        _instance[3].release()
    C.__new__ = staticmethod(_singleton_new)
    C.__init__ = MethodType(_singleton_init, None, C)
    return C

# 本来想用Descriptor以便外部更改new和init
# 但好像只有实例set会使用Descriptor，通过类set就是一般意义的赋值（覆盖）了
# 而实例创建之后set也没有意义，因为两个函数不会再被调用了，所以就不用了
# def singleton(c):
#     '''
#     singleton pattern
#     '''
#     from types import MethodType
#     _instance = [None, False]
#     _new = c.__new__
#     _init = c.__init__
#     def _real_new(clz, *args, **kw):
#         if _instance[0] == None:
#             _instance[0] = _new(c, *args, **kw)
#         return _instance[0]
#     def _real_init(self, *args, **kw):
#         if not _instance[1]:
#             _instance[1] = True
#             _init(self, *args, **kw)
#     class NewDescriptor(object):
#         def __get__(self, obj, objtype):
#             return _real_new
#         def __set__(self, obj, val):
#             _new = val
#     class InitDescriptor(object):
#         def __get__(self, obj, objtype):
#             def warrper(*args, **kw):
#                 _real_init(obj, *args, **kw)
#             return warrper
#         def __set__(self, obj, val):
#             _init = val
#     c.__new__ = NewDescriptor()
#     c.__init__ = InitDescriptor()
#     return c

def synchronized(mutex):
    def _decorator(func):
        def _decorated(*args, **kw):
            mutex.acquire()
            try:
                rtn = func(*args, **kw)
            finally:
                mutex.release()
            return rtn
        return _decorated
    return _decorator
