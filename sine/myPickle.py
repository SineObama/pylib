# coding=utf-8

import cPickle as _pickle

def load(path, defalut=None):
    '''
    @parameter path 文件路径
    @parameter default 文件不存在时默认的返回值
    '''
    try:
        f = open(path, 'rb')
        rtn = _pickle.load(f)
        f.close()
    except IOError, e:
        if e.errno != 2: # IOError: [Errno 2] No such file or directory: ''
            raise e
        rtn = defalut
    return rtn

def dump(path, obj):
    '''
    @parameter path 文件路径
    @parameter obj 保存的对象
    '''
    f = open(path, 'wb')
    _pickle.dump(obj, f)
    f.close()
