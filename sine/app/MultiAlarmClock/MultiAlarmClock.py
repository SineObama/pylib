
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


#保存当前路径
from data import data
data['path0'] = curPath + '\\'


# In[ ]:


# 加载配置并检查。对于缺少的配置赋予默认值并暂停警告

# 从文件读入，暂时保存为字符串
_conf_filename = 'clock.conf'
try:
    f = open(data['path0'] + _conf_filename, 'rb')
    config = {}
    for line in f:
        line = line.replace('\r', '').replace('\n', '')
        if line.startswith('#') or line == '':
            continue
        tokens = line.split('=', 1)
        if len(tokens) == 2:
            config[tokens[0]] = tokens[1]
        else:
            config[tokens[0]] = True
    f.close()
except Exception, e:
    print e
    print 'load from file', _conf_filename, 'failed'
    sys.exit(1)

# 补充默认配置
default_config = [
('alarm_last', 30, int),
('alarm_interval', 300, int),
('format', '%Y-%m-%d %H:%M:%S %%warn %%3idx %%3state %%msg', str),
('warn', '!!!', str),
('state.ON', 'ON', str),
('state.OFF', 'OFF', str),
('datafile', 'clocks.binv2', str),
('defaultSound', 'default', str)]

warning = False
for (key, default, converter) in default_config:
    if not config.has_key(key):
        print 'missing config \'' + key + '\', will use default value \'' + str(default) + '\''
        warning = True
        config[key] = default
    elif converter:
        try:
            config[key] = converter(config[key])
        except Exception, e:
            print 'parsing config \'' + key + '=' + str(config[key]) + '\' failed, will use default value \'' + str(default) + '\'. exception is:' + repr(e)
            warning = True

data['config'] = config

if warning:
    print '\npress enter to continue'
    raw_input()


# In[ ]:


# 外部依赖
import datetime
# library依赖
from sine.sync import synchronized
from sine.helpers import cls
# 本地依赖
from exception import ClockException, ParseException
from parsing import *
from mydatetime import getNow
from entity import AlarmClock
import player
import listenThread


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


# 模块初始化
from manager import instance as manager


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

