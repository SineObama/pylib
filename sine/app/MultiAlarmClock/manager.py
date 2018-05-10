# coding=utf-8

import json
from mydatetime import *
from sine.sync import synchronized
from exception import ClockException as _ClockException
from entity import AlarmClock as _AlarmClock
from data import data as _data

_data_filepath = _data['location'].join(_data['config']['datafile'])
_day = datetime.timedelta(1)
_everyday = '1234567'
_sort = lambda x:(x['time'] if x['on'] else datetime.datetime.max)

@synchronized('clocks')
def _init():
    import os
    # 读取数据文件，忽略文件不存在的情况
    try:
        if os.path.isfile(_data_filepath):
            with open(_data_filepath, 'r') as file:
                _data['clocks'] = json.load(file, object_hook=_AlarmClock.object_hook, encoding='Latin-1')
        else:
            _data['clocks'] = []
    except Exception, e:
        print 'load data from file', _data_filepath, 'failed.', e
        import sys
        sys.exit(1)

    # 只更新过期的星期重复闹钟
    now = getNow()
    for clock in _data['clocks']:
        if clock['time'] < now and clock.isWeekly():
            clock.resetTime(_getNextFromWeekday(now, clock['time'], clock['repeat']))
    _data['clocks'].sort(key=_sort)

    # 检查音频文件是否存在
    from player import assertLegal
    from exception import ClientException
    from initUtil import warn
    for clock in _data['clocks']:
        try:
            assertLegal(clock['sound'])
        except ClientException, e:
            warn('illeagal sound \'' + clock['sound'] + '\' of', clock, '.')
    try:
        assertLegal(_data['config']['default_sound'])
    except ClientException, e:
        warn('default sound illeagal, will use default beep.', e)
        _data['config']['default_sound'] = 'default'

def _getNextFromWeekday(now, time, repeat):
    '''为星期重复闹钟选择下一个有效时间。
    使用time的时分秒，找到一个比now晚，且有效的时间（在repeat表示的星期中）'''
    nexttime = now.replace(hour=time.hour, minute=time.minute, second=time.second, microsecond=time.microsecond)
    while nexttime <= now or str(nexttime.weekday()+1) not in repeat:
        nexttime += _day
    return nexttime

@synchronized('clocks')
def save():
    with open(_data_filepath, 'w') as file:
        json.dump(_data['clocks'], file, default=_AlarmClock.default, ensure_ascii=False)
    return

@synchronized('clocks')
def getReminds():
    '''供Output提示'''
    return _getReminds(_data['clocks']);

def _getReminds(clocks):
    reminds = []
    now = getNow()
    for clock in clocks:
        if clock.checkRemind(now):
            reminds.append(clock)
    return reminds

def addOnce(date_time, msg):
    now = getNow()
    if date_time <= now:
       date_time = _getNextFromWeekday(now, date_time, _everyday)
    return _add(_AlarmClock(date_time, msg))

def addRepeatWeekday(start_time, repeat, msg):
    '''按星期重复，输入开始的时间和重复星期编号字符串，比如星期一和星期二就是'12'
    给定时间'''
    clock = _AlarmClock(start_time, msg)
    editWeekdays(clock, repeat)
    return _add(clock)

def addRepeatPeriod(start_time, delta, msg):
    if not delta:
        raise _ClockException('repeat can not be 0')
    return _add(_AlarmClock(start_time, msg, delta))

@synchronized('clocks')
def _add(clock):
    _data['clocks'].append(clock)
    _data['clocks'].sort(key=_sort)
    return

@synchronized('clocks')
def get(index, defaultFirst=False):
    '''参数从1开始（数组从0开始），检查越界（允许0代表默认操作，defaultFirst返回第一个闹钟否则None）'''
    if index > len(_data['clocks']) or index < 0:
        raise _ClockException('index out of range: ' + str(index))
    if index > 0:
        return _data['clocks'][index - 1]
    if not defaultFirst:
        return None
    if len(_data['clocks']) == 0:
        raise _ClockException('no clock!!!')
    return _data['clocks'][0]

@synchronized('clocks')
def editTime(clock, date_time):
    '''不允许None。
    对一次性和星期重复闹钟：过时则从给定时间开始算下一天。
    会开启闹钟。'''
    now = getNow()
    if date_time <= now:
        if not clock.isRepeat():
            date_time = _getNextFromWeekday(now, date_time, _everyday)
        if clock.isWeekly():
            date_time = _getNextFromWeekday(now, date_time, clock['repeat'])
    clock.resetTime(date_time)
    clock['on'] = True
    _data['clocks'].sort(key=_sort)
    return

@synchronized('clocks')
def cancel(clock):
    '''取消闹钟
    传入None为默认操作：关掉第一个提醒或到期闹钟
    对单次闹钟：关闭
    对星期重复：取消下一个提醒
    对周期重复：以当前时间重新开始计时
    对关闭的闹钟无效'''
    now = getNow()
    
    # choose clock
    if clock == None: # choose first expired
        clock = _getFirstRemindOrExpired(_data['clocks'], now)
        if not clock:
            raise _ClockException('no remind or expired clock')
    
    if not clock['on']:
        raise _ClockException('the clock is off, can not cancel')
    
    # cancel it
    if not clock.isRepeat():
        clock['on'] = False
        clock['expired'] = False
    else:
        if clock.isWeekly():
            nexttime = _getNextFromWeekday(clock['time'], clock['time'], clock['repeat'])
        else:
            nexttime = now + clock['repeat']
        clock.resetTime(nexttime)
    _data['clocks'].sort(key=_sort)
    return

@synchronized('clocks')
def switch(indexs):
    '''变换开关。
    传入空列表执行默认操作：改变第一个提醒或到期闹钟，或者第一个闹钟。
    会重置提醒时间。
    对星期重复：开启时以当前时间为准，重置为下一个闹钟时间；
    对周期重复：开启时如果过期，则以当前时间重新开始计时。
    无视越界'''
    now = getNow()
    if len(_data['clocks']) == 0:
        return
    
    # choose clock(s)
    chooseds = []
    if len(indexs) == 0:
        found = _getFirstRemindOrExpired(_data['clocks'], now)
        chooseds = [found if found else _data['clocks'][0]]
    else:
        for i, clock in enumerate(_data['clocks']):
            if i + 1 in indexs:
                chooseds.append(clock)
    
    # swith them
    for clock in chooseds:
        clock['on'] = not clock['on']
        clock['expired'] = False
        if clock['on'] and clock['time'] < now:
            if clock.isRepeat():
                if clock.isWeekly():
                    clock.resetTime(_getNextFromWeekday(now, clock['time'], clock['repeat']))
                else:
                    clock.resetTime(now + clock['repeat'])
            else:
                if clock['time'] <= now:
                    clock.resetTime(_getNextFromWeekday(now, clock['time'], _everyday))
    _data['clocks'].sort(key=_sort)
    return

def _getFirstRemindOrExpired(clocks, now):
    for clock in clocks:
        if clock.checkRemind(now):
            return clock
    for clock in clocks:
        if clock.isExpired():
            return clock
    return None

@synchronized('clocks')
def remove(indexs):
    clocks = []
    for i, clock in enumerate(_data['clocks']):
        if i + 1 not in indexs:
            clocks.append(clock)
    _data['clocks'] = clocks
    return

@synchronized('clocks')
def later(time):
    '''存在提醒闹钟：设置他们的提醒时间；
    不存在：设置所有到期闹钟的提醒时间'''
    reminds = _getReminds(_data['clocks'])
    if len(reminds):
        for clock in reminds:
            clock['remindTime'] = time
    else:
        now = getNow()
        for clock in _data['clocks']:
            if clock.isExpired():
                clock['remindTime'] = time
    return

@synchronized('clocks')
def editRemindAhead(clock, seconds):
    clock['remindAhead'] = datetime.timedelta(0, seconds)
    clock['remindTime'] = clock['time'] - clock['remindAhead']
    clock['expired'] = False
    return

@synchronized('clocks')
def editWeekdays(clock, repeat):
    '''修改星期，重新计算'''
    d = {}
    for i in _everyday:
        d[i] = False
    for i in repeat:
        d[i] = True
    weekdays = ''
    for i in _everyday:
        weekdays += i if d[i] else ' '
    if weekdays == '       ':
        raise _ClockException('repeat can not be empty')
    clock.resetTime(_getNextFromWeekday(getNow(), clock['time'], weekdays))
    clock['repeat'] = weekdays
    _data['clocks'].sort(key=_sort)
    return

@synchronized('clocks')
def editPeriod(clock, delta):
    '''修改周期，重新计算'''
    clock['repeat'] = delta
    clock.resetTime(getNow() + clock['repeat'])
    _data['clocks'].sort(key=_sort)
    return

_init()
