# coding=utf-8

# core data model
class AlarmClock(dict):
    '''
    time: 闹钟时间
    remindTime: 提醒时间（响铃时间）
    msg: 信息
    repeat: 重复方式
        None: 无
        string: 星期重复, 格式如：'12345  ', '1 3 567'
        datetime.timedelta: 周期重复, 比如1小时（冷却时间）
    on: 开关'''
    def __init__(self, time, msg='', repeat=None):
        self['time'] = time
        self['remindTime'] = time
        self['msg'] = msg
        self['repeat'] = repeat
        self['on'] = True
        return
    
    def __str__(self):
        return self['time'].strftime('%Y-%m-%d %H:%M:%S') + ' ' + self['msg']
    
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return None
