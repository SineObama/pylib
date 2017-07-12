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

def singleton(clz):
    '''
    singleton pattern
    '''
    __instance = [None]
    def singleton_deliver(*args, **kw):
        if __instance[0] == None:
            __instance[0] = clz(*args, **kw)
        return __instance[0]
    return singleton_deliver
