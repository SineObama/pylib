# coding=utf-8

import datetime
from data import data as _data

# 闹钟实体
class AlarmClock(dict):
    '''
    time: 闹钟时间
    expired: 提醒过
    remindTime: 提醒时间（响铃时间）
    remindAhead: 提前提醒时间（比如1分钟）
    msg: 信息
    repeat: 重复方式
        None: 无
        string: 星期重复, 格式如：'12345  ', '1 3 567'
        datetime.timedelta: 周期重复, 比如1小时（冷却时间）
    on: 开关
    sound: 铃声，见player模块'''
    def __init__(self, time, msg, repeat=None):
        self['time'] = time
        self['expired'] = False
        self['remindAhead'] = datetime.timedelta(0, _data['config']['default_remindAhead'])
        self['remindTime'] = time - self['remindAhead']
        self['msg'] = msg
        self['repeat'] = repeat
        self['on'] = True
        self['sound'] = _data['config']['default_sound']
        return
    
    def __str__(self):
        return self['time'].strftime('%Y-%m-%d %H:%M:%S') + ' ' + self['msg']
    
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return None

    def checkRemind(self, now):
        '''新增过期状态。这里只会开启状态。
        返回是否需要提醒。'''
        if self['on'] and self['remindTime'] <= now:
            self['expired'] = True
            return True
        return False

    def isExpired(self):
        '''是否提醒过'''
        return self['on'] and self['expired']
    
    def resetTime(self, time):
        self['time'] = time
        self['remindTime'] = time - self['remindAhead']
        self['expired'] = False

    @staticmethod
    def default(obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S.%f')
        else:
            return repr(obj)

    @staticmethod
    def object_hook(dic):
        clock = AlarmClock(datetime.datetime.now(), '')
        for (k, v) in dic.items():
            clock[k] = v.encode('unicode-escape').decode('string_escape') if isinstance(v, unicode) else v
        clock['remindAhead'] = eval(clock['remindAhead'])
        clock['remindTime'] = datetime.datetime.strptime(clock['remindTime'], '%Y-%m-%d %H:%M:%S.%f')
        clock['time'] = datetime.datetime.strptime(clock['time'], '%Y-%m-%d %H:%M:%S.%f')
        if type(clock['repeat']) == str and clock['repeat'].startswith('datetime'):
            clock['repeat'] = eval(clock['repeat'])
        return clock
