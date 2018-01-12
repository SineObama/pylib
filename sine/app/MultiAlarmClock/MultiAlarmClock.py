
# coding: utf-8

# In[ ]:


# add liberary root path
import sys
import os
if len(sys.path[0]) == 0: # develop time using jupyter notebook on current path
    curPath = os.getcwd()
else:
    curPath = sys.path[0]
root = os.path.dirname(os.path.dirname(os.path.dirname(curPath)))
sys.path.append(root)


# In[ ]:


from sine.sync import synchronized
from sine.helpers import cls
from exception import ClockException, ParseException
from parsing import *
from mydatetime import *
from entity import AlarmClock
from manager import instance as manager
from data import data
import player
import listenThread
import sys


# In[ ]:


# 栈管理“页面”
# 每一块是一个字典
# key 0 为指令解析与处理函数。返回值：0表示退出，正整数表示要调用的函数的key，-1表示不调用
# key 'reprint' 为输出页面的函数
# 字典中还可以自定义放别的东西……
stack = []
@synchronized('stack')
def append(dic):
    stack.append(dic)
    if dic.has_key('reprint'):
        dic['reprint']()
    return
@synchronized('stack')
def pop():
    rtn = stack.pop()
    if len(stack):
        stack[len(stack) - 1]['reprint']()
    return rtn


# In[ ]:


remindDelay = datetime.timedelta(0, data['config']['alarm_interval'])

def replace(so, t, t2, o):
    '''对将要格式化的字符串，符合%[]t的，替换为以%[]t2格式化的o'''
    import re
    ss = re.findall(r'%[^%]*(?='+t+')', so)
    for s in ss:
        temp = (s+t2) % (o)
        so = so.replace(s+t, temp, 1)
    return so

# 主页面：闹钟列表

def addMainPage():

    @synchronized(data)
    def clsAndPrintList():
        cls()
        now = getNow()
        if len(data['clocks']):
            config = data['config']
            string = 'alarm clocks:\n'
            for i, clock in enumerate(data['clocks']):
                temp = clock['time'].strftime(config['format'])
                temp = replace(temp, 'warn', 's', config['warn'] if clock['time'] <= now and clock['on'] else '')
                temp = replace(temp, 'idx', 'd', i+1)
                temp = replace(temp, 'state', 's', config['state.ON'] if clock['on'] else config['state.OFF'])
                temp = replace(temp, 'msg', 's', clock['msg'])
                string += temp + '\n'
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


listenThread.remindDelay = remindDelay
listenThread.lastTime = data['config']['alarm_last']
listenThread.on = addAlarmPage
listenThread.off = pop


# In[ ]:


# main flow
def init():
    addMainPage()
    listenThread.start()
    return

def do(order):
    dic = stack[len(stack) - 1]
    rtn = dic[0](order)
    if rtn > 0: # 调用指定函数
        dic[rtn]()
    return 0 if len(stack) == 0 else None

def stop():
    player.play(None)
    listenThread.stop()
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

