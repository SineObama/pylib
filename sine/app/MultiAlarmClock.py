
# coding: utf-8

# In[1]:

import sys
sys.path.append('D:\Users\Git\pylib')


# In[2]:

from sine.decorator import singleton, synchronized


# In[3]:

import datetime


# In[4]:

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


# In[5]:

class AlarmClock(object):
    def __init__(self, time, msg=''):
        self.time = time
        self.remindTime = time
        self.msg = msg
    def __str__(self):
        return self.time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + self.msg


# In[6]:

@singleton
class ClockManager(object):
    __filename = 'clocks.bin'
    from threading import Lock as __Lock
    __mutex = __Lock()

    def __init__(self):
        from sine.helpers import PresistentManager
        self.__clocks = PresistentManager().getOrDefault(self.__filename, [])
        self.__remindDelay = datetime.timedelta(0, 300) # 5 minutes
        self.__presistent = PresistentManager

    @synchronized(__mutex)
    def stop(self):
        self.__presistent().set(self.__filename, self.__clocks)
    
    @synchronized(__mutex)
    def getAll(self):
        clocks = []
        for clock in self.__clocks:
            clocks.append(clock)
        return clocks
    
    @synchronized(__mutex)
    def getExpireds(self):
        expireds = []
        now = datetime.datetime.now()
        for clock in self.__clocks:
            if clock.remindTime <= now:
                expireds.append(clock)
        return expireds

    @synchronized(__mutex)
    def add(self, time, msg=''):
        self.__addNormal(time, msg='')

    @synchronized(__mutex)
    def addCountDown(self, delta, msg=''):
        self.__addNormal(delta + datetime.datetime.now(), msg)
        
    def __addNormal(self, time, msg=''):
        clock = AlarmClock(time, msg)
        self.__clocks.append(clock)
        self.__clocks = sorted(self.__clocks, key=lambda x:x.time)
        
    @synchronized(__mutex)
    def remove(self, indexs):
        clocks = []
        for i, clock in enumerate(self.__clocks):
            if i not in indexs:
                clocks.append(clock)
        self.__clocks = clocks

    @synchronized(__mutex)
    def pauseAll(self):
        now = datetime.datetime.now()
        for clock in self.__clocks:
            if clock.remindTime <= now:
                clock.remindTime = now + self.__remindDelay


# In[7]:

@singleton
class OutputManager(object):
    import winsound as __winsound
    import os as __os
    import time as __time
    import threading as __threading
    __mutex = __threading.Lock()

    def __init__(self, clockManager):
        self.__quit = False
        self.__clockManager = clockManager
        
        t = self.__threading.Thread(target=self.__alarm)
        t.setDaemon(True)
        t.start()
        self.__alarmThread = t
        
    def stop(self):
        self.__mutex.acquire()
        self.__quit = True
        self.__mutex.release()
        self.__alarmThread.join(2)
        if self.__alarmThread.is_alive():
            raise RuntimeError('thread can not exit')

    def clsAndPrintList(self):
        self.__cls()
        clocks = self.__clockManager.getAll()
        now = datetime.datetime.now()
        if len(clocks):
            string = 'alarm clocks:\n'
            for i, clock in enumerate(clocks):
                string += '%3d'%i + ' '
                if clock.time <= now:
                    string += '!!! '
                string += str(clock) + '\n'
        else:
            string = 'no clock\n'
        sys.stdout.write(string)
        
    def __alarm(self):
        count = 0
        mark = 0
        while 1:
            if self.__quit:
                break
            expireds = self.__clockManager.getExpireds()
            if not mark and len(expireds):
                mark = (count + 1) % 5
            if mark and not len(expireds):
                mark = 0
            if mark:
                if count % 5 == mark - 1:
                    self.__cls()
                if count % 5 == mark % 5:
                    string = ''
                    for clock in expireds:
                        string += str(clock) + '\n'
                    sys.stdout.write(string)
                if count % 5 == mark % 5 or count % 5 == (mark+2) % 5:
                    self.__winsound.Beep(600,50)
            count += 1
            self.__time.sleep(0.1)
    
    def __cls(self):
        self.__os.system('cls')


# In[8]:

# main loop
manager = ClockManager()
output = OutputManager(manager)
output.clsAndPrintList()
wrong_input = False
while (1):
    if wrong_input:
        print 'wrong input'
    wrong_input = True
    
    order = raw_input()
    
    if len(order) == 0: # 'pause'  and clean screen
        manager.pauseAll()
        output.clsAndPrintList()
        wrong_input = False
        continue
        
    if order[0] == 'q': # quit
        break
        
    if order[0] == 'c': # add clock
        
        # normal clock
        if order[1] == ' ':
            ss = order.split(' ', 1)
            if len(ss) < 2:
                continue
            ss = ss[1].split(' ', 1)

            now = datetime.datetime.now()
            target = tryReplace(now, ss[0], tformats, tfieldss)
            if not target: # try date
                if len(ss) < 2:
                    continue
                target = tryReplace(now, ss[0], dformats, dfieldss)
                if not target:
                    continue
                ss = ss[1].split(' ', 1)
                target = tryReplace(target, ss[0], tformats, tfieldss)
                if not target:
                    continue
            
            msg = ''
            if len(ss) == 2:
                msg = ss[1]
            manager.add(target, msg)
            output.clsAndPrintList()
            wrong_input = False
            
        # count down
        if order[1] == 'd':
            ss = order.split(' ', 1)
            if len(ss) < 2:
                continue
            ss = ss[1].split(' ', 1)

            zero = datetime.datetime.min
            target = tryReplace(zero, ss[0], tformats, tfieldss)
            if not target:
                continue
            
            msg = ''
            if len(ss) == 2:
                msg = ss[1]            
            manager.addCountDown(target - zero, msg)
            output.clsAndPrintList()
            
    if order[0] == 'r': # remove clock
        
        ss = order.split(' ', 1)
        if len(ss) < 2: # default to remove the first one
            ss = ['0']
        else:
            ss = ss[1].split()
        indexs = []
        try:
            for s in ss:
                indexs.append(int(s))
        except:
            print 'wrong input'
            continue
        manager.remove(indexs)
        output.clsAndPrintList()
        
    wrong_input = False

manager.stop()
output.stop()

