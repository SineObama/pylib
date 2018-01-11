# coding=utf-8

'''
2017年接触python不久，异想天开的想做单例模式的装饰器，最后还是有各种缺陷。
然而module本身就是单例了，这并没有意义。
现在这些代码已经变得过于复杂……
'''

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
