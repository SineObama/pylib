# coding=utf-8

import cPickle as _pickle

def load(path, defalut=None):
    '''
    @parameter path 文件路径
    @parameter default 文件不存在时默认的返回值
    '''
    try:
        with open(path, 'rb') as f:
            rtn = _pickle.load(f)
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
    with open(path, 'wb') as f:
        _pickle.dump(obj, f)
