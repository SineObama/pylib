# coding=utf-8
'''
根据配置的格式，创建格式化对象，格式化输出的闹钟列表。
'''

class Str(object):
    import re as _re
    def __init__(self, s=''):
        self._s = s
        return
    def fill(self, t, t2, o):
        ss = self._re.findall(r'%[^%]*(?='+t+')', self._s)
        for s in ss:
            if callable(o):
                o = o()
            self._s = self._s.replace(s+t, (s+t2) % (o), 1)
        return self._s

def create(config, format):
    warn = config['warn']
    on = config['state.ON']
    off = config['state.OFF']
    def formatter(i, clock):
        s = Str(clock['time'].strftime(format))
        s.fill('warn', 's', warn if clock.isExpired() else '')
        s.fill('idx', 'd', i)
        s.fill('state', 's', on if clock['on'] else off)
        s.fill('msg', 's', clock['msg'])
        return s.fill('rep', 's', clock.repeatStr)
    return formatter
