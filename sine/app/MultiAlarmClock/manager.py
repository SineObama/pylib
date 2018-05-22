# coding=utf-8

import threading
from plone.synchronize import synchronized
from mydatetime import *
from exception import ClockException
from entity import *
from data import data

_data_filepath = data['config']['datafile']
_sort = lambda x:(x['time'] if x['on'] else datetime.datetime.max)
_clock_lock = threading.RLock()

@synchronized(_clock_lock)
def _init():
    import os
    # 读取数据文件，忽略文件不存在的情况
    try:
        data['clocks'] = []
        with open(_data_filepath, 'a+') as file:
            for line in file:
                data['clocks'].append(eval(line))
    except Exception, e:
        print 'load data from file', _data_filepath, 'failed.', e
        import sys
        sys.exit(1)

    # 检查音频文件是否存在
    from player import isLegal
    from exception import ClientException
    from initUtil import warn
    for clock in data['clocks']:
        if not isLegal(clock['sound']):
            warn('illeagal sound \'' + clock['sound'] + '\' of', clock, '.')
    if not isLegal(data['config']['default_sound']):
        warn('default sound illeagal, will use default beep.', e)
        data['config']['default_sound'] = 'default'

def getReminds():
    '''供Output提示'''
    reminds = []
    now = getNow()
    for clock in data['clocks']:
        if clock.checkRemind(now):
            reminds.append(clock)
    return reminds

@synchronized(_clock_lock)
def add(clock):
    '''新的添加函数'''
    data['clocks'].append(clock)
    return

@synchronized(_clock_lock)
def get(index, defaultFirst=False):
    '''参数从1开始（数组从0开始），检查越界（允许0代表默认操作，defaultFirst返回第一个闹钟否则None）'''
    if index > len(data['clocks']) or index < 0:
        raise ClockException('index out of range: ' + str(index))
    if index > 0:
        return data['clocks'][index - 1]
    if not defaultFirst:
        return None
    if len(data['clocks']) == 0:
        raise ClockException('no clock!!!')
    return data['clocks'][0]

@synchronized(_clock_lock)
def cancel(clock):
    '''取消闹钟
    传入None为默认操作：关掉第一个提醒或到期闹钟
    对一次性闹钟：删除
    对星期重复：取消下一个提醒
    对周期重复：以当前时间重新开始计时
    对关闭的闹钟无效'''
    now = getNow()
    
    # choose clock
    if clock == None: # choose first expired
        clock = _getFirstRemindOrExpired(data['clocks'], now)
        if not clock:
            raise ClockException('no remind or expired clock')
    
    if not clock['on']:
        raise ClockException('the clock is off, can not cancel')
    
    # cancel it
    clock.cancel()
    if isinstance(clock, OnceClock):
        data['clocks'].remove(clock)
    return

@synchronized(_clock_lock)
def switch(indexs):
    '''变换开关。
    传入空列表执行默认操作：改变第一个提醒或到期闹钟，或者第一个闹钟。
    会重置提醒时间。
    会删除一次性闹钟。
    对星期重复：开启时以当前时间为准，重置为下一个闹钟时间；
    对周期重复：开启时如果过期，则以当前时间重新开始计时。
    无视越界'''
    now = getNow()
    if len(data['clocks']) == 0:
        return
    
    # choose clock(s)
    chooseds = []
    if len(indexs) == 0:
        found = _getFirstRemindOrExpired(data['clocks'], now)
        chooseds = [found if found else data['clocks'][0]]
    else:
        for i, clock in enumerate(data['clocks']):
            if i + 1 in indexs:
                chooseds.append(clock)
    
    # switch them
    for clock in chooseds:
        clock.switch()
        if isinstance(clock, OnceClock):
            data['clocks'].remove(clock)
    return

def _getFirstRemindOrExpired(clocks, now):
    for clock in clocks:
        if clock.checkRemind(now):
            return clock
    for clock in clocks:
        if clock.isExpired():
            return clock
    return None

@synchronized(_clock_lock)
def remove(indexs):
    clocks = []
    for i, clock in enumerate(data['clocks']):
        if i + 1 not in indexs:
            clocks.append(clock)
    data['clocks'] = clocks
    return

@synchronized(_clock_lock)
def later(time):
    '''存在提醒闹钟：设置他们的提醒时间；
    不存在：设置所有到期闹钟的提醒时间'''
    reminds = getReminds()
    if len(reminds):
        for clock in reminds:
            clock['remindTime'] = time
    else:
        now = getNow()
        for clock in data['clocks']:
            if clock.isExpired():
                clock['remindTime'] = time
    return

@synchronized(_clock_lock)
def resortAndSave():
    data['clocks'].sort(key=_sort)
    with open(_data_filepath, 'w') as file:
        for clock in data['clocks']:
            file.write(repr(clock))
            file.write('\n')
    return

@synchronized(_clock_lock)
def refreshWeekly():
    for clock in data['clocks']:
        if isinstance(clock, WeeklyClock):
            clock.refresh()

_init()
