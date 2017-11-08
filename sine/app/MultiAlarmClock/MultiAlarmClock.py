
# coding: utf-8

# In[ ]:

import sys
sys.path.append('D:\Users\Git\pylib')


# In[ ]:

from sine.decorator import synchronized
from exception import ClockException, ParseException
from parsing import *
from mydatetime import *
from entity import AlarmClock
from manager import instance as manager
import data


# In[ ]:

import threading
import winsound
import time
import win32gui


# In[ ]:

# 栈管理“页面”
# 每一块是一个字典
# key 0 为指令解析与处理函数。返回值：0表示退出，正整数表示要调用的函数的key，-1表示不调用
# key 'reprint' 为输出页面的函数
# 字典中还可以自定义放别的东西……
stack = []
stackMutex = threading.Lock()
def append(dic):
    stackMutex.acquire()
    stack.append(dic)
    if dic.has_key('reprint'):
        dic['reprint']()
    stackMutex.release()
    return
def pop():
    stackMutex.acquire()
    rtn = stack.pop()
    if len(stack):
        stack[len(stack) - 1]['reprint']()
    stackMutex.release()
    return rtn

# 清屏
import os
def cls():
    os.system('cls')
    return


# In[ ]:

remindDelay = datetime.timedelta(0, 300) # 5 minutes

# 主页面：闹钟列表

def addMainPage():

    @synchronized(data)
    def clsAndPrintList():
        cls()
        clocks = data.get()
        now = getNow()
        if len(clocks):
            string = 'alarm clocks:\n'
            for i, clock in enumerate(clocks):
                string += '%s %3s %3d %3s %s\n'%(clock['time'].strftime('%Y-%m-%d %H:%M:%S'),
                                                ('!!!' if clock['time'] <= now and clock['on'] else ''),
                                                 i+1,
                                                ('ON' if clock['on'] else 'OFF'),
                                                clock['msg'])
        else:
            string = 'no clock\n'
        sys.stdout.write(string)
        return
    
    def printAndSave():
        clsAndPrintList()
        manager.save()

    def main(order):
        now = getNow()
        try: # catch parse exception
            if len(order) == 0: # 'later' and clean screen
                manager.later(now + remindDelay)
                return 1

            if order == 'q': # quit
                pop()
                return 0

            order, remain = parseString(order)

            # anormal clock: (date) time (msg)
            if order.startswith('cc'):
                target, remain = parseDateTimeByOrder(order, remain, now)
                manager.addOnce(target, remain)
                return 1
            # repeat weekday: (date) time repeat_day_num (msg)
            if order.startswith('cv'):
                target, remain = parseDateTimeByOrder(order, remain, now)
                weekdays, msg = parseString(remain)
                manager.addRepeatWeekday(target, weekdays, msg)
                return 1
            # repeat period: (date) time period (msg)
            if order.startswith('cf'):
                target, remain = parseDateTimeByOrder(order, remain, now)
                period, msg = parseTime(remain, zero)
                manager.addRepeatPeriod(target, period - zero, msg)
                return 1

            # edit clock in new page
            if order == 'e':
                index, unused = parseIndexWithDefaultZero(remain)
                addEditPage(manager.get(index))
                return -1
            # edit time
            if order.startswith('w'):
                index, remain = parseIndexWithDefaultZero(remain)
                target, remain = parseDateTimeByOrder(order, remain, now)
                manager.editTime(index, target)
                return 1
            # cancel alarm
            if order == 'a':
                index, unused = parseIndexWithDefaultZero(remain)
                manager.cancel(index)
                return 1
            # switch
            if order == 's':
                indexs = parseAllToIndex(remain)
                manager.switch(indexs)
                return 1
            # remove clock
            if order == 'r':
                indexs = parseAllToIndex(remain)
                if len(indexs) == 0:
                    raise ClockException('no index')
                manager.remove(indexs)
                return 1

            print 'wrong order'
            return -1
        except ParseException as e:
            print e
            return -1
        except ClockException as e:
            print e
            return -1
    
    dic = {}
    dic[0] = main
    dic[1] = printAndSave
    dic['reprint'] = clsAndPrintList
    append(dic)

# 闹铃页面

def addEditPage(clock):
#     import copy
#     src = clock
#     clock = copy.copy(clock)
    
    def clsAndPrintClock():
        cls()
        string = ' - Edit - \n'
        string += '%3s\n' % ('ON' if clock['on'] else 'OFF')
        string += 'next time: %s\n' % str(clock['time'])
        string += 'repeat: '
        if clock['repeat'] == None:
            string += 'No'
        else:
            if type(clock['repeat']) == str:
                string += 'on weekday \'' + clock['repeat'] + '\''
            else:
                string += 'every ' + (zero + clock['repeat']).strftime('%H:%M:%S')
        string += '\n'
        string += 'message: %s\n' % clock['msg']
        string += 'sound: %s\n' % clock['sound']
        sys.stdout.write(string)
        return
    
    def printAndSave():
        clsAndPrintClock()
        manager.save()
    
    def editPage(order):
        try: # catch parse exception
            if order == 'q': # quit
                pop()
                return 0

            order, remain = parseString(order)
            
            # edit sound
            if order == 's':
                if remain == '':
                    clock['sound'] = None
                else:
                    sound, unused = parseString(remain) # TODO check exist
                    clock['sound'] = sound if sound else None
                return 1
            # edit message
            if order == 'm':
                clock['msg'] = remain
                return 1
            
            print 'wrong order'
            return -1
        except ParseException as e:
            print e
            return -1
    
    dic = {}
    dic[0] = editPage
    dic[1] = printAndSave
    dic['reprint'] = clsAndPrintClock
    append(dic)

# 响铃页面

def addAlarmPage():

    def alarmPage(order):
        now = getNow()
        if len(order) == 0: # 'later' and clean screen
            manager.later(now + remindDelay)
            return 1
        # cancel alarm
        if order == 'a':
            manager.cancel(0)
            return 1
        # switch
        if order == 's':
            manager.switch([])
            return 1
        return -1
    
    dic = {}
    dic[0] = alarmPage
    dic[1] = manager.save
    append(dic)


# In[ ]:

# 监控线程

__quit = False
__last = 30

def __alarm():
    import player
    count = 0
    alarm = False
    while 1:
        if __quit: # TODO thread safe?
            break
        reminds = manager.getReminds()
        length = len(reminds)
        if length:
            sound = reminds[len(reminds) - 1]['sound']
        if not alarm and length:
            alarm = True
            player.play('' if sound == None else sound)
            count = 0
            addAlarmPage()
        if alarm and not len(reminds):
            alarm = False
            player.play(None)
            pop()
        if alarm and count > 10 * __last:
            alarm = False
            player.play(None)
            manager.later(getNow() + remindDelay)
            pop()
        if alarm:
            player.play(sound if sound != None else '')
            if count % 10 == 0:
                win32gui.FlashWindow(hWnd, 1)
            if count % 5 == 0:
                cls()
            if count % 5 == 1:
                string = ''
                for clock in reminds:
                    string += str(clock) + '\n'
                sys.stdout.write(string)
        count += 1
        time.sleep(0.1)
    return


# In[ ]:

# main flow
__alarmThread = None
def init():
    global __alarmThread
    global __quit
    global hWnd
    import win32api
    __quit = False
    s = win32api.GetConsoleTitle()
    hWnd = win32gui.FindWindow(0,s)
    addMainPage()
    __alarmThread = threading.Thread(target=__alarm)
    __alarmThread.setDaemon(True)
    __alarmThread.start()
    return

def do(order):
    dic = stack[len(stack) - 1]
    rtn = dic[0](order)
    if rtn > 0: # 调用指定函数
        dic[rtn]()
    return 0 if len(stack) == 0 else None

def stop():
    global __quit
    __quit = True
    winsound.PlaySound(None, winsound.SND_PURGE)
    if __alarmThread:
        __alarmThread.join(2)
        if __alarmThread.is_alive():
            raise RuntimeError('thread can not exit')
    return


# In[ ]:

# main loop
try:
    init()
    while (1):
        order = raw_input()
        rtn = do(order)
        if rtn == 0:
            break
finally:
    stop()

