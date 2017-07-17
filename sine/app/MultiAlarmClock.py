
# coding: utf-8

# In[ ]:

import sys
sys.path.append('D:\Users\Git\pylib')


# In[ ]:

from sine.decorator import singleton, synchronized


# In[ ]:

import datetime
def getNow():
    return datetime.datetime.now()


# In[ ]:

# format to read and corresponding fields to be replaced
tformats = [  '%M',
          '%H:',
               ':%S',
          '%H:%M',
            ':%M:%S',
          '%H:%M:%S']
tfieldss = [     ['minute', 'second', 'microsecond'],
         ['hour', 'minute', 'second', 'microsecond'],
                           ['second', 'microsecond'],
         ['hour', 'minute', 'second', 'microsecond'],
                 ['minute', 'second', 'microsecond'],
         ['hour', 'minute', 'second', 'microsecond']]
dformats = [   '-%d',
             '%m-%d',
          '%y-%m-%d']
dfieldss = [              ['day'],
                 ['month', 'day'],
         ['year', 'month', 'day']]
def tryReplace(now, s, formats, fieldss):
    target = None
    for i, fm in enumerate(formats):
        try:
            target = datetime.datetime.strptime(s, fm)
        except Exception, e:
            continue
        break
    if not target:
        return None
    d = {}
    for field in fieldss[i]:
        exec('d[field] = target.' + field)
    return now.replace(**d)

# refactor by parsing step by step, and catching Exception
# parse return the parsed object and the remain string
class ParseException(Exception):
    pass
def parseString(s):
    '''length check should be outside for further info'''
    if len(s) == 0:
        raise ParseException('no string to parse')
    s = s.split(' ', 1)
    return s[0], (s[1] if len(s) > 1 else '')
def parseTime(s, reference):
    s = s.split(' ', 1)
    target = tryReplace(reference, s[0], tformats, tfieldss)
    if not target:
        raise ParseException('can not parse as time: ' + s[0])
    return target, (s[1] if len(s) > 1 else '')
def parseDateAndTime(s, reference): # (date) time
    try:
        target, s = parseTime(s, reference)
    except ParseException as e:
        s = s.split(' ', 1)
        if len(s) < 2:
            raise ParseException('can not parse as time (no date): ' + s[0])
        target = tryReplace(reference, s[0], dformats, dfieldss)
        if not target:
            raise ParseException('can not parse as date or time: ' + s[0])
        target, s = parseTime(s[1], target)
    return target, s
def parseDateTimeByOrder(order, s, zero, now):
    if order.endswith('d'):
        target, remain = parseTime(s, zero)
        return target - zero + now, remain
    else:
        return parseDateAndTime(s, now)
def parseIndexWithDefaultZero(s):
    if len(s) == 0:
        return 0, ''
    s = s.split(' ', 1)
    try:
        index = int(s[0])
    except ValueError as e:
        raise ParseException('can not parse as int: ' + s[0])
    return index, (s[1] if len(s) > 1 else '')
def parseAllToIndex(s):
    '''return [] when empty'''
    if len(s) == 0:
        return []
    s = s.split()
    indexs = []
    try:
        for i in s:
            indexs.append(int(i))
    except ValueError as e:
        raise ParseException('can not parse as int: ' + i)
    return indexs


# In[ ]:

@singleton
class DataManager(object):
    '''
    one show acquire() before get() and set(), and then release() after complete r/w
    '''
    import threading as __threading
    __mutex = __threading.Lock()
    
    def __init__(self):
        self.__data = { }
        return
    
    def acquire(self):
        return self.__mutex.acquire()
    
    def set(self, data, key='__root'):
        self.__data[key] = data
        return
    
    def get(self, key='__root'):
        if not self.__data.has_key(key):
            raise KeyError('no key ' + str(key))
        return self.__data[key]
    
    def release(self):
        return self.__mutex.release()
    


# In[ ]:

# core data model
class AlarmClock(dict):
    '''
    time: event time
    remindTime: alarm time
    msg: message
    repeat:
        None
        string: for weekday, e.g. '12345  ', '1 3 567'
        datetime.timedelta: every the time, e.g. 1 hour
    on: on or off'''
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
    


# In[ ]:

data = DataManager()


# ### indexes used for specification are showed from 1, and stored from 0 of course, and 0 maybe used for default

# In[ ]:

class ClockException(Exception):
    pass
@singleton
class ClockManager(object):
    __filename = 'clocks.binv2'
    
    def __resetWeekday(self, now, time, repeat):
        nexttime = now.replace(hour=time.hour, minute=time.minute, second=time.second, microsecond=time.microsecond)
        while nexttime <= now or str(nexttime.weekday()+1) not in repeat:
            nexttime += self.__day
        return nexttime

    def __init__(self):
        from sine.helpers import PresistentManager
        self.__presistent = PresistentManager()
        self.__day = datetime.timedelta(1)
        self.__sort = lambda x:x['time']
        clocks = self.__presistent.getOrDefault(self.__filename, [])
        # 更新星期重复的闹钟
        now = getNow()
        for clock in clocks:
            if clock['time'] <= now and type(clock['repeat']) == str:
                clock['time'] = self.__resetWeekday(now, clock['time'], clock['repeat'])
                clock['remindTime'] = clock['time']
        clocks.sort(key=self.__sort)
        data.acquire()
        data.set(clocks)
        data.release()
        return
    
    @synchronized(data)
    def save(self):
        self.__presistent.set(self.__filename, data.get())
        return
    
    @synchronized(data)
    def getExpireds(self): # 供Output提示
        expireds = []
        now = getNow()
        for clock in data.get():
            if clock['remindTime'] <= now and clock['on']:
                expireds.append(clock)
        return expireds

    def addOnce(self, date_time, msg=''):
        return self.__add(AlarmClock(date_time, msg))

    def addRepeatWeekday(self, start_time, repeat, msg=''):
        '''按星期重复，输入开始的时间和重复星期编号字符串，比如星期一和星期二就是'12' '''
        if repeat == '':
            raise ClockException('repeat can not be empty')
        d = {}
        for i in '1234567':
            d[i] = False
        for i in repeat:
            d[i] = True
        weekdays = ''
        for i in '1234567':
            weekdays += i if d[i] else ' '
        while str(start_time.weekday()+1) not in weekdays:
            start_time += self.__day
        return self.__add(AlarmClock(start_time, msg, weekdays))

    def addRepeatPeriod(self, start_time, delta, msg=''):
        return self.__add(AlarmClock(start_time, msg, delta))
    
    @synchronized(data)
    def __add(self, clock):
        clocks = data.get()
        clocks.append(clock)
        clocks.sort(key=self.__sort)
        return
    
    @synchronized(data)
    def edit(self, index, msg):
        if index == 0:
            index = 1
        clocks = data.get()
        if index > len(clocks) or index < 1:
            raise ClockException('index out of range')
        clocks[index - 1]['msg'] = msg
        return
    
    @synchronized(data)
    def editTime(self, index, date_time):
        if index == 0:
            index = 1
        clocks = data.get()
        if index > len(clocks) or index < 1:
            raise ClockException('index out of range')
        clocks[index - 1]['time'] = date_time
        clocks[index - 1]['remindTime'] = date_time
        clocks.sort(key=self.__sort)
        return
    
    @synchronized(data)
    def close(self, index):
        '''对于单次闹钟，会关掉，对于还未到的重复闹钟，就会取消下一个提醒
        传入0关掉第一个到期闹钟'''
        clocks = data.get()
        if index > len(clocks):
            raise ClockException('out of index: ' + str(index))
        
        # choose clock
        now = getNow()
        if index != 0:
            clock = clocks[index - 1]
        else: # close first expired
            found = False
            for clock in clocks:
                if clock['time'] <= now and clock['on']:
                    found = True
                    break
            if not found:
                raise ClockException('no expired clock')
        
        # close it
        if clock['repeat'] == None:
            clock['on'] = False
        else:
            if type(clock['repeat']) == str:
                nexttime = clock['time']
                nexttime += self.__day
                while str(nexttime.weekday()+1) not in clock['repeat']:
                    nexttime += self.__day
            else:
                nexttime = now + clock['repeat']
            clock['time'] = nexttime
            clock['remindTime'] = nexttime
            clocks.sort(key=self.__sort)
        return
    
    @synchronized(data)
    def switch(self, indexs):
        '''0 stands for the first one(1)'''
        if len(indexs) == 0:
            indexs = [1]
        clocks = data.get()
        now = getNow()
        for i, clock in enumerate(clocks):
            if i+1 in indexs:
                clock['on'] = not clock['on']
                if clock['repeat']:
                    if type(clock['repeat']) == str: # always renew 'weekday'
                        clock['time'] = self.__resetWeekday(now, clock['time'], clock['repeat'])
                    else:
                        if clock['on']: # renew 'period' when open
                            clock['time'] = now + clock['repeat']
                clock['remindTime'] = clock['time']
        clocks.sort(key=self.__sort)
        return
    
    @synchronized(data)
    def remove(self, indexs):
        '''0 stands for the first one(1)'''
        if len(indexs) == 0:
            indexs = [1]
        clocks = []
        for i, clock in enumerate(data.get()):
            if i+1 not in indexs:
                clocks.append(clock)
        data.set(clocks)
        return
    
    @synchronized(data)
    def later(self, time):
        '''remind me at a later @Parameter time'''
        for clock in data.get():
            if clock['remindTime'] < time:
                clock['remindTime'] = time
        return
    


# In[ ]:

@singleton
class OutputManager(object):
    import winsound as __winsound
    import os as __os
    import time as __time
    import threading as __threading
    __helper = datetime.datetime.min.replace(year=1900)
    __sound = 600
    __last = 30

    def __init__(self, clockManager):
        self.__quit = False
        self.__clockManager = clockManager
        
        t = self.__threading.Thread(target=self.__alarm)
        t.setDaemon(True)
        t.start()
        self.__alarmThread = t
        return
    
    def stop(self):
        self.__quit = True
        self.__clockManager = None
        self.__alarmThread.join(2)
        if self.__alarmThread.is_alive():
            raise RuntimeError('thread can not exit')
        return
    
    @synchronized(data)
    def clsAndPrintList(self):
        self.__cls()
        clocks = data.get()
        now = getNow()
        if len(clocks):
            string = 'alarm clocks:\n'
            for i, clock in enumerate(clocks):
                string += '%3d %3s %8s %3s %s\n'%(i+1,
                    ('ON' if clock['on'] else 'OFF'),
                    ('' if clock['repeat'] == None else (clock['repeat'] if type(clock['repeat']) == str else (self.__helper + clock['repeat']).strftime('%H:%M:%S'))),
                    ('!!!' if clock['time'] <= now and clock['on'] else ''),
                    str(clock))
        else:
            string = 'no clock\n'
        sys.stdout.write(string)
        return
    
    def __alarm(self):
        count = 0
        alarm = False
        while 1:
            if self.__quit:
                break
            expireds = self.__clockManager.getExpireds()
            if not alarm and len(expireds):
                alarm = True
                count = 0
            if alarm and not len(expireds):
                alarm = False
            if alarm and count > 10 * self.__last:
                alarm = False
                self.__clockManager.later(getNow() + remindDelay)
            if alarm:
                if count % 5 == 0:
                    self.__cls()
                if count % 5 == 1:
                    string = ''
                    for clock in expireds:
                        string += str(clock) + '\n'
                    sys.stdout.write(string)
                if count % 5 == 1 or count % 5 == 3:
                    self.__winsound.Beep(self.__sound,50)
            count += 1
            self.__time.sleep(0.1)
        return
    
    def __cls(self):
        self.__os.system('cls')
        return
    


# In[ ]:

try:
    # main loop

    manager = ClockManager()
    output = OutputManager(manager)

    zero = datetime.datetime.min # 用于计算时长类数据
    remindDelay = datetime.timedelta(0, 300) # 5 minutes

    output.clsAndPrintList()
    renew = False
    while (1):
        if renew:
            output.clsAndPrintList()
            manager.save()
        renew = True
        order = raw_input()
        now = getNow()

        try: # catch parse exception
            if len(order) == 0: # 'pause'  and clean screen
                manager.later(now + remindDelay)
                continue

            order, remain = parseString(order)

            if order == 'q': # quit
                break

            # anormal clock: (date) time (msg)
            if order.startswith('cc'):
                target, remain = parseDateTimeByOrder(order, remain, zero, now)
                manager.addOnce(target, remain)
                continue
            # repeat weekday: (date) time repeat_day_num (msg)
            if order.startswith('cv'):
                target, remain = parseDateTimeByOrder(order, remain, zero, now)
                weekdays, msg = parseString(remain)
                manager.addRepeatWeekday(target, weekdays, msg)
                continue
            # repeat period: (date) time period (msg)
            if order.startswith('cf'):
                target, remain = parseDateTimeByOrder(order, remain, zero, now)
                period, msg = parseTime(remain, zero)
                manager.addRepeatPeriod(target, period - zero, msg)
                continue

            # edit message
            if order == 'e':
                index, msg = parseIndexWithDefaultZero(remain)
                manager.edit(index, msg)
                continue
            # edit time
            if order.startswith('et'):
                index, remain = parseIndexWithDefaultZero(remain)
                target, remain = parseDateTimeByOrder(order, remain, zero, now)
                manager.editTime(index, target)
                continue
            # close alarm
            if order == 'a':
                index, unused = parseIndexWithDefaultZero(remain)
                manager.close(index)
                continue
            # switch
            if order == 's':
                indexs = parseAllToIndex(remain)
                manager.switch(indexs)
                continue
            # remove clock
            if order == 'r':
                indexs = parseAllToIndex(remain)
                manager.remove(indexs)
                continue
            
            renew = False
            print 'wrong order'
            
        except ParseException as e:
            renew = False
            print e
        except ClockException as e:
            renew = False
            print e

finally:
    output.stop()

