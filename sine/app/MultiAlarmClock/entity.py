# coding=utf-8

import datetime
import mydatetime
from mydatetime import getNow, getNextFromWeekday, everyday
from parsing import zero
from data import data
from exception import ClockException

# 闹钟实体
class AlarmClock(dict):
    '''
    time: 闹钟时间
    expired: 提醒过
    remindTime: 提醒时间（响铃时间）
    remindAhead: 提前提醒时间（比如1分钟）
    msg: 信息
    on: 开关
    sound: 铃声，见player模块'''
    def __init__(self, dic):
        '''必须含义time字段'''
        self.update(dic)
        if not self.has_key('time'):
            raise ClockException('internal error, no time')
        self.setdefault('msg', '')
        self.setdefault('expired', False)
        self.setdefault('remindAhead', datetime.timedelta(0, data['config']['default_remindAhead']))
        self.setdefault('remindTime', dic['time'] - self['remindAhead'])
        self.setdefault('on', True)
        self.setdefault('sound', data['config']['default_sound'])
    
    def __repr__(self):
        return self.__class__.__name__ + '(' + dict.__repr__(self) + ')'

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

    def repeatStr(self):
        return ''

    def editTime(self, date_time):
        '''会开启闹钟。'''
        self.resetTime(date_time)
        self['on'] = True
        self['expired'] = False

    def cancel(self):
        self['on'] = False

    def switch(self):
        self['on'] = not self['on']
        self['expired'] = False

    def editRemindAhead(self, seconds):
        self['remindAhead'] = datetime.timedelta(0, seconds)
        self['remindTime'] = self['time'] - self['remindAhead']
        self['expired'] = False

class OnceClock(AlarmClock):
    '''一次性闹钟，用完删除
        weekdays:string 格式如：'12345  ', '1 3 567' '''
    def switch(self):
        self['on'] = False

class WeeklyClock(AlarmClock):
    '''星期重复闹钟，不重复时用完自动关闭'''
    def __init__(self, dic):
        AlarmClock.__init__(self, dic)
        if not self.has_key('weekdays'):
            raise ClockException('internal error, no weekdays')
        self.editWeekdays(self['weekdays'])
        self.refresh()

    def refresh(self):
        '''更新过期闹钟'''
        now = getNow()
        if self['on'] and self['time'] < now:
            self.resetTime(getNextFromWeekday(now, self['time'], self['weekdays']))

    def editWeekdays(self, weekdays):
        '''修改星期，对输入进行格式化'''
        if weekdays == None:
            weekdays = ''
        d = {}
        for i in everyday:
            d[i] = False
        for i in weekdays:
            d[i] = True
        weekdays = ''
        for i in everyday:
            weekdays += i if d[i] else ' '
        self['weekdays'] = weekdays

    def repeatStr(self):
        return self['weekdays']

    def editTime(self, date_time):
        '''过时则从给定时间开始算下一天。'''
        now = getNow()
        if date_time <= now:
            date_time = getNextFromWeekday(now, date_time, self['weekdays'])
        AlarmClock.editTime(self, date_time)

    def cancel(self):
        '''取消下一个提醒'''
        now = getNow()
        if self['weekdays'].isspace():
            self['on'] = False
        else:
            nexttime = getNextFromWeekday(self['time'] if self['time'] > now else now, self['time'], self['weekdays'])
            self.resetTime(nexttime)

    def switch(self):
        '''开启时以当前时间为准，重置为下一个闹钟时间'''
        AlarmClock.switch(self)
        now = getNow()
        if self['on'] and self['time'] < now:
            self.resetTime(getNextFromWeekday(now, self['time'], self['weekdays']))


class PeriodClock(AlarmClock):
    '''周期重复闹钟
       period:datetime.timedelta 比如1小时（冷却时间）'''
    def __init__(self, dic):
        AlarmClock.__init__(self, dic)
        if not self.has_key('period'):
            raise ClockException('internal error, no period')
        self.editPeriod(dic['period'])

    def editPeriod(self, period):
        '''修改周期'''
        if not period:
            raise ClockException('period can not be 0')
        self['period'] = period

    def repeatStr(self):
        return (zero + self['period']).strftime('%H:%M:%S')
        
    def cancel(self):
        '''以当前时间重新开始计时'''
        now = getNow()
        nexttime = now + self['period']
        self.resetTime(nexttime)

    def switch(self):
        '''开启时如果过期，则以当前时间重新开始计时'''
        AlarmClock.switch(self)
        now = getNow()
        if self['on'] and self['time'] < now:
            self.resetTime(now + self['period'])
