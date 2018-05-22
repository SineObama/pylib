# coding: utf-8

# 外部依赖
import sys
import datetime
import os
import threading
# library依赖
from plone.synchronize import synchronized
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


# 栈管理“页面”
# 每个页面有2个函数：
# do接受指令
# reprint输出页面（清屏）
# 具体实现中，dodo返回回调函数编号（大于0），0则退出页面，-1可表示无操作
class Page(dict):
    def do(self, order):
        rtn = self.dodo(order)
        if rtn > 0:
            return self[rtn]()
        if rtn == 0:
            pop()
        return rtn
    def reprint(self):
        pass
    def dodo(self):
        return 0
stack = []
stack_lock = threading.RLock()
@synchronized(stack_lock)
def append(page):
    stack.append(page)
    page.reprint()
    return
@synchronized(stack_lock)
def pop():
    rtn = stack.pop()
    if len(stack):
        stack[-1].reprint()
    return rtn


def cls():
    os.system('cls')
    return

alarmInterval = datetime.timedelta(0, data['config']['alarm_interval'])
fmt = formatter.create(data['config'], data['config']['format'])

# 主页面：闹钟列表

class MainPage(Page):

    def __init__(self):
        self[1] = self.printAndSave

    def reprint(self):
        cls()
        now = getNow()
        if len(data['clocks']):
            isToday = True
            today = datetime.datetime.date(now)
            string = 'alarm clocks:\n'
            for i, clock in enumerate(data['clocks']):
                if isToday and datetime.datetime.date(clock['time']) > today:
                    isToday = False
                    string += '\n'
                string += fmt(i+1, clock) + '\n'
        else:
            string = 'no clock\n'
        sys.stdout.write(string)
        return
    
    def printAndSave(self):
        manager.resortAndSave()
        self.reprint()

    def dodo(self, order):
        now = getNow()
        try: # catch parse exception
            if len(order) == 0: # 'later' and clean screen
                manager.later(now + alarmInterval)
                return 1

            order = order.strip()
            if order == 'q': # quit
                return 0

            # edit clock in new page
            if order.startswith('e'):
                index, unused = parseInt(order[1:], 0)
                append(EditPage(manager.get(index, True)))
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
                char = ''
                char, remain2 = parseString(remain)
            except NoStringException, e:
                pass
            if char == 'w':
                weekdays, msg = parseString(remain2)
                manager.add(WeeklyClock({'time':target,'weekdays':weekdays,'msg':msg}))
                return 1
            if char == 'r':
                period, msg = parseDateAndTime(remain2, zero)
                period -= zero
                manager.add(PeriodClock({'time':target,'period':period,'msg':msg}))
                return 1
            if target <= now:
                target = getNextFromWeekday(now, target, everyday)
            manager.add(OnceClock({'time':target,'msg':remain}))
            return 1
        except ClientException as e:
            print e
            return -1

# 编辑页面

class EditPage(Page):

    def __init__(self, clock):
        self.clock = clock
        self[1] = self.printAndSave
    
    def reprint(self):
        cls()
        clock = self.clock
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
    
    def printAndSave(self):
        manager.resortAndSave()
        self.reprint()
    
    def dodo(self, order):
        clock = self.clock
        try: # catch parse exception
            order = order.strip()
            if order == 'q': # quit
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
                    clock.resetTime(getNextFromWeekday(getNow(), clock['time'], clock['weekdays']))
                else:
                    period, unused = parseDateAndTime(order[1:], zero)
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

# 响铃页面

class AlarmPage(Page):

    def __init__(self):
        self[1] = manager.resortAndSave

    def dodo(self, order):
        order = order.strip()
        now = getNow()
        if len(order) == 0: # 'later' and clean screen
            manager.later(now + alarmInterval)
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


listenThread.on = lambda :append(AlarmPage())
listenThread.off = pop
listenThread.refresh = lambda :stack[-1].reprint()


try:
    # 模块初始化
    import manager
    if data['config']['warning_pause']:
        initUtil.warning_pause()
    append(MainPage())
    listenThread.start()
    while (1):
        order = raw_input()
        stack[-1].do(order)
        if len(stack) == 0:
            break
finally:
    player.play(None)
    listenThread.stop()
