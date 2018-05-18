# coding=utf-8

import cPickle
import os.path

def loadOrDefault(path, defalut):
    '''
    @parameter path 文件路径
    @parameter default 文件不存在时默认的返回值
    '''
    if os.path.isfile(path):
        with open(path, 'rb') as f:
            return cPickle.load(f)
    return defalut

def load(path):
    '''
    @parameter path 文件路径
    '''
    with open(path, 'rb') as f:
        return cPickle.load(f)

def dump(path, obj):
    '''
    @parameter path 文件路径
    @parameter obj 保存的对象
    '''
    with open(path, 'wb') as f:
        return cPickle.dump(obj, f)
