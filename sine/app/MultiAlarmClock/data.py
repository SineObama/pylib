# coding=utf-8
'''
全局数据。
'''

class _HashableDict(dict):
    def __init__(self, *args, **kw):
        super(_HashableDict, self).__init__(*args, **kw)
        self._object_for_hash = object()
    def __hash__(self):
        return hash(self._object_for_hash)

data = _HashableDict()
data['clocks'] = []
