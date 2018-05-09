# coding: utf-8

# In[ ]:


# 获取当前路径（用于在不同位置运行时找到当前路径下文件），并添加library根目录到系统路径sys.path
import sys
import os
if len(sys.path[0]) == 0: # develop time using jupyter notebook on current path
    curPath = os.getcwd()
else:
    curPath = sys.path[0]
print 'current path:', curPath
root = os.path.dirname(os.path.dirname(os.path.dirname(curPath)))
sys.path.append(root)


# In[ ]:


# 外部依赖
import datetime
# library依赖
from sine.sync import synchronized
from sine.helpers import cls
# 本地依赖
from parsing import *
from mydatetime import getNow
from entity import AlarmClock
from exception import ClientException
from data import data
import initUtil
import listenThread
import formatter
import player
# 模块初始化
import manager


# In[ ]:


# 栈管理“页面”
# 每个页面有2个函数：
# do接受指令，返回回调函数编号（大于0）
# reprint输出页面（清屏）
class Page(dict):
    def __init__(self, do, reprint):
        self._do = do
        self._reprint = reprint
        return
    def do(self, order):
        rtn = self._do(order)
        if rtn > 0:
            return self[rtn]()
        return rtn
    def reprint(self):
        return self._reprint()
stack = []
@synchronized('stack')
def append(page):
    stack.append(page)
    page.reprint()
    return
@synchronized('stack')
def pop():
    rtn = stack.pop()
    if len(stack):
        stack[-1].reprint()
    return rtn


# In[ ]:


remindDelay = datetime.timedelta(0, data['config']['alarm_interval'])

# 主页面：闹钟列表

def addMainPage():

    fmt = formatter.create(data['config'], data['config']['format'])

    @synchronized('clocks')
    def clsAndPrintList():
        cls()
        now = getNow()
        if len(data['clocks']):
            string = 'alarm clocks:\n'
            for i, clock in enumerate(data['clocks']):
                string += fmt(i+1, clock) + '\n'
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

            order = order.strip()
            if order == 'q': # quit
                pop()
                return 0

            # edit clock in new page
            if order.startswith('e'):
                index, unused = parseInt(order[1:], 0)
                addEditPage(manager.get(index, True))
                return -1
            # edit time
            if order.startswith('w'):
                index, remain = parseInt(order[1:])
                target, unused = parseDateTime(remain, now)
                manager.editTime(manager.get(index), target)
                return 1
            # cancel alarm
            if order.startswith('a'):
                index, unused = parseInt(order[1:], 0)
                manager.cancel(manager.get(index))
                return 1
            # switch
            if order.startswith('s'):
                indexs = parseAllToIndex(order[1:])
                manager.switch(indexs)
                return 1
            # remove clock
            if order.startswith('r'):
                indexs = parseAllToIndex(order[1:])
                manager.remove(indexs)
                return 1
            
            # $dtime ($msg)        #普通闹钟
            # $dtime w $wday ($msg)        #星期重复闹钟
            # $dtime r $dtime ($msg)        #周期重复闹钟
            target, remain = parseDateTime(order, now)
            try:
                char, remain2 = parseString(remain)
                if char == 'w':
                    weekdays, msg = parseString(remain2)
                    manager.addRepeatWeekday(target, weekdays, msg)
                    return 1
                if char == 'r':
                    period, msg = parseTime(remain2, zero)
                    manager.addRepeatPeriod(target, period - zero, msg)
                    return 1
            except Exception, e:
                pass
            manager.addOnce(target, remain)
            return 1
        except ClientException as e:
            print e
            return -1
    
    page = Page(main, clsAndPrintList)
    page[1] = printAndSave
    append(page)

# 编辑页面

def addEditPage(clock):
    
    def clsAndPrintClock():
        cls()
        string = ' - Edit - \n'
        string += '%3s\n' % ('ON' if clock['on'] else 'OFF')
        string += 'next time: %s\n' % str(clock['time'])
        string += 'remind ahead: %s\n' % str(clock['remindAhead'])
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
            order = order.strip()
            if order == 'q': # quit
                pop()
                return 0

            # edit time
            if order.startswith('w'):
                target, unused = parseDateTime(order[1:], getNow())
                manager.editTime(clock, target)
                return 1
            # edit remind ahead
            if order.startswith('a'):
                manager.editRemindAhead(clock, parseInt(order[1:])[0])
                return 1
            # edit message
            if order.startswith('m'):
                clock['msg'] = order[1:].strip()
                return 1
            # edit repeat time
            if order.startswith('r'):
                if not clock['repeat']:
                    raise ClientException('this is not repeat clock')
                if type(clock['repeat']) == str:
                    manager.editWeekdays(clock, parseString(order[1:])[0])
                else:
                    period, unused = parseTime(order[1:], zero)
                    manager.editPeriod(clock, period - zero)
                return 1
            # edit sound
            if order.startswith('s'):
                fname = order[1:].strip()
                player.assertLegal(fname)
                clock['sound'] = fname
                return 1
            
            print 'wrong order'
            return -1
        except ClientException as e:
            print e
            return -1
    
    page = Page(editPage, clsAndPrintClock)
    page[1] = printAndSave
    append(page)

# 响铃页面

def addAlarmPage():

    def alarmPage(order):
        order = order.strip()
        now = getNow()
        if len(order) == 0: # 'later' and clean screen
            manager.later(now + remindDelay)
            return 1
        # cancel alarm
        if order == 'a':
            manager.cancel(None)
            return 1
        # switch
        if order == 's':
            manager.switch([])
            return 1
        return -1
    
    page = Page(alarmPage, lambda :None)
    page[1] = manager.save
    append(page)


# In[ ]:


listenThread.remindDelay = remindDelay
listenThread.lastTime = data['config']['alarm_last']
listenThread.on = addAlarmPage
listenThread.off = pop


# In[ ]:


# main loop
def mainLoop():
    try:
        if data['config']['warning_pause']:
            initUtil.warning_pause()
        addMainPage()
        listenThread.start()
        while (1):
            order = raw_input()
            stack[-1].do(order)
            if len(stack) == 0:
                break
    finally:
        player.play(None)
        listenThread.stop()
