# coding: utf-8


# In[ ]:


# 外部依赖
import sys
import datetime
# library依赖
from sine.sync import synchronized
from sine.helpers import cls
# 本地依赖
from parsing import *
from mydatetime import *
from entity import *
from exception import ClientException, NoStringException
from data import data
import initUtil
import listenThread
import formatter
import player


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
        manager.resortAndSave()
        clsAndPrintList()

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
                manager.get(index).editTime(target)
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
            
            # $dtime ($msg)        #一次性闹钟
            # $dtime w $wday ($msg)        #星期重复闹钟
            # $dtime r $dtime ($msg)        #周期重复闹钟
            target, remain = parseDateTime(order, now)
            try:
                char, remain2 = parseString(remain)
                if char == 'w':
                    weekdays, msg = parseString(remain2)
                    manager.add(WeeklyClock({'time':target,'weekdays':weekdays,'msg':msg}))
                    return 1
                if char == 'r':
                    period, msg = parseTime(remain2, zero)
                    period -= zero
                    manager.add(PeriodClock({'time':target,'period':period,'msg':msg}))
                    return 1
            except NoStringException, e:
                pass
            if target <= now:
                target = getNextFromWeekday(now, target, everyday)
            manager.add(OnceClock({'time':target}))
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
        if isinstance(clock, OnceClock):
            string += 'No'
        else:
            if isinstance(clock, WeeklyClock):
                string += 'on weekday \'' + clock['weekdays'] + '\''
            else:
                string += 'every ' + (zero + clock['period']).strftime('%H:%M:%S')
        string += '\n'
        string += 'message: %s\n' % clock['msg']
        string += 'sound: %s\n' % clock['sound']
        sys.stdout.write(string)
        return
    
    def printAndSave():
        manager.resortAndSave()
        clsAndPrintClock()
    
    def editPage(order):
        try: # catch parse exception
            order = order.strip()
            if order == 'q': # quit
                pop()
                return 0

            # edit time
            if order.startswith('w'):
                target, unused = parseDateTime(order[1:], getNow())
                clock.editTime(target)
                return 1
            # edit remind ahead
            if order.startswith('a'):
                ahead = parseInt(order[1:])[0]
                if ahead < 0:
                    raise ClientException('can\'t ahead negative')
                clock.editRemindAhead(ahead)
                return 1
            # edit message
            if order.startswith('m'):
                clock['msg'] = order[1:].strip()
                return 1
            # edit repeat time
            if order.startswith('r'):
                if isinstance(clock, OnceClock):
                    raise ClientException('this is once clock')
                if isinstance(clock, WeeklyClock):
                    clock.editWeekdays(parseString(order[1:])[0])
                else:
                    period, unused = parseTime(order[1:], zero)
                    clock.editPeriod(period - zero)
                    clock.resetTime(getNow() + clock['period'])
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
    page[1] = manager.resortAndSave
    append(page)


# In[ ]:


listenThread.remindDelay = remindDelay
listenThread.lastTime = data['config']['alarm_last']
listenThread.on = addAlarmPage
listenThread.off = pop


# In[ ]:


try:
    # 模块初始化
    import manager
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
