# coding=utf-8
'''方便进行路径操作'''

import os as _os

class Path(str):
    def join(self, *args, **kw):
        return Path(_os.path.normpath(_os.path.join(self, *args, **kw)))
