# coding=utf-8

from mydatetime import *
import sine.myPickle as _pickle
from sine.sync import *
from exception import ClockException
from entity import AlarmClock
from data import data
import sys

class ClockManager(object):
    '''indexes used for specification are showed from 1, and stored from 0 of course, and 0 maybe used for default'''
    _filename = data['config']['datafile']
    
    def _getNextFromWeekday(self, now, time, repeat):
        '''根据当前时间，为星期重复闹钟选择下一个时间'''
        nexttime = now.replace(hour=time.hour, minute=time.minute, second=time.second, microsecond=time.microsecond)
        while nexttime <= now or str(nexttime.weekday()+1) not in repeat:
            nexttime += self._day
        return nexttime

    def __init__(self):
        self._day = datetime.timedelta(1)
        self._sort = lambda x:(x['time'] if x['on'] else datetime.datetime.max)
        acquire(data)
        try:
            data['clocks'] = _pickle.load(self._filename, [])
        except Exception, e:
            print 'load from file', _filename, 'failed'
            sys.exit(1)
        # 只更新过期的星期重复闹钟
        now = getNow()
        for clock in data['clocks']:
            if clock['time'] < now and type(clock['repeat']) == str:
                clock['time'] = self._getNextFromWeekday(now, clock['time'], clock['repeat'])
                clock['remindTime'] = clock['time']
        data['clocks'].sort(key=self._sort)
        release(data)
        return
    
    @synchronized(data)
    def save(self):
        _pickle.dump(self._filename, data['clocks'])
        return
    
    @synchronized(data)
    def getReminds(self): # 供Output提示
        return self._getReminds(data['clocks']);
    
    def _getReminds(self, clocks):
        reminds = []
        now = getNow()
        for clock in clocks:
            if clock['on'] and clock['remindTime'] <= now:
                reminds.append(clock)
        return reminds

    def addOnce(self, date_time, msg=''):
        now = getNow()
        if date_time <= now:
           date_time = self._getNextFromWeekday(now, date_time, '1234567')
        return self._add(AlarmClock(date_time, msg))

    def addRepeatWeekday(self, start_time, repeat, msg=''):
        '''按星期重复，输入开始的时间和重复星期编号字符串，比如星期一和星期二就是'12' '''
        d = {}
        for i in '1234567':
            d[i] = False
        for i in repeat:
            d[i] = True
        weekdays = ''
        for i in '1234567':
            weekdays += i if d[i] else ' '
        if weekdays == '       ':
            raise ClockException('repeat can not be empty')
        start_time = self._getNextFromWeekday(getNow(), start_time, weekdays)
        return self._add(AlarmClock(start_time, msg, weekdays))

    def addRepeatPeriod(self, start_time, delta, msg=''):
        return self._add(AlarmClock(start_time, msg, delta))
    
    @synchronized(data)
    def _add(self, clock):
        data['clocks'].append(clock)
        data['clocks'].sort(key=self._sort)
        return
    
    def _checkIndex(f):
        def _f(self, index, *args, **kw):
            if index > len(data['clocks']) or index < 0:
                raise ClockException('index out of range: ' + str(index))
            return f(self, index, *args, **kw)
        return _f
    
    @synchronized(data)
    @_checkIndex
    def get(self, index, **kw):
        if index == 0:
            index = 1
        return data['clocks'][index - 1]
    
    @synchronized(data)
    @_checkIndex
    def editTime(self, index, date_time, **kw): # and turn on
        if index == 0:
            index = 1
        now = getNow()
        clock = data['clocks'][index - 1]
        if date_time <= now:
            if not clock['repeat']:
                date_time = self._getNextFromWeekday(now, date_time, '1234567')
            if type(clock['repeat']) == str:
                date_time = self._getNextFromWeekday(now, date_time, clock['repeat'])
        clock['time'] = date_time
        clock['remindTime'] = date_time
        clock['on'] = True
        data['clocks'].sort(key=self._sort)
        return
    
    @synchronized(data)
    @_checkIndex
    def cancel(self, index, **kw):
        '''取消一次闹钟
        传入0为默认值，关掉第一个提醒或到期闹钟
        对单次闹钟：关闭
        对星期重复：取消下一个提醒
        对周期重复：以当前时间重新开始计时
        对关闭的闹钟无效'''
        now = getNow()
        
        # choose clock
        if index == 0: # choose first expired
            clock = self._getFirstRemindOrExpired(data['clocks'], now)
            if not clock:
                raise ClockException('no remind or expired clock')
        else:
            clock = data['clocks'][index - 1]
        
        if not clock['on']:
            raise ClockException('the clock is off, can not cancel')
        
        # cancel it
        if not clock['repeat']:
            clock['on'] = False
        else:
            if type(clock['repeat']) == str:
                nexttime = self._getNextFromWeekday(clock['time'], clock['time'], clock['repeat'])
            else:
                nexttime = now + clock['repeat']
            clock['time'] = nexttime
            clock['remindTime'] = nexttime
        data['clocks'].sort(key=self._sort)
        return
    
    @synchronized(data)
    def switch(self, indexs):
        '''变换开关
        传入空列表为默认值，改变第一个提醒或到期闹钟，或者第一个闹钟
        会重置提醒时间为闹钟时间
        对星期重复：开启时以当前时间为准，重置为下一个闹钟时间
        对周期重复：开启时如果过期，则以当前时间重新开始计时'''
        now = getNow()
        
        # choose clock(s)
        chooseds = []
        if len(indexs) == 0:
            found = self._getFirstRemindOrExpired(data['clocks'], now)
            chooseds = [found if found else data['clocks'][0]]
        else:
            for i, clock in enumerate(data['clocks']):
                if i + 1 in indexs:
                    chooseds.append(clock)
        
        # swith them
        for clock in chooseds:
            clock['on'] = not clock['on']
            if clock['on'] and clock['time'] < now:
                if clock['repeat']:
                    if type(clock['repeat']) == str:
                        clock['time'] = self._getNextFromWeekday(now, clock['time'], clock['repeat'])
                    else:
                        clock['time'] = now + clock['repeat']
                else:
                    if clock['time'] <= now:
                        clock['time'] = self._getNextFromWeekday(now, clock['time'], '1234567')
            clock['remindTime'] = clock['time'] # always reset remind time, seems right?
        data['clocks'].sort(key=self._sort)
        return
    
    def _getFirstRemindOrExpired(self, clocks, now):
        found = None
        for clock in clocks:
            if clock['on'] and clock['remindTime'] <= now:
                found = clock
                break
        if not found:
            for clock in clocks:
                if clock['on'] and clock['time'] < now:
                    found = clock
                    break
        return found
    
    @synchronized(data)
    def remove(self, indexs):
        clocks = []
        for i, clock in enumerate(data['clocks']):
            if i + 1 not in indexs:
                clocks.append(clock)
        data['clocks'] = clocks
        return
    
    @synchronized(data)
    def later(self, time):
        '''有正在提醒的闹钟：设置他们为指定时间再提醒
        没有：设置所有到期闹钟为指定时间再提醒'''
        reminds = self._getReminds(data['clocks'])
        if len(reminds):
            for clock in reminds:
                clock['remindTime'] = time
        else:
            now = getNow()
            for clock in data['clocks']:
                if clock['on'] and clock['time'] < now: # former hint it reached
                    clock['remindTime'] = time
        return

instance = ClockManager()
