# coding=utf-8
'''
监听线程。检查闹钟状态并进行屏幕闪烁和播放铃声。
需要设置提醒延迟remindDelay(datetime.timedelta)，启动回调on和关闭回调off。
提供start和stop接口，可重复启动。
'''

from data import data
from initUtil import warn
import datetime
config = data['config']

alarmLast = config['alarm_last']
alarmInterval = datetime.timedelta(0, config['alarm_interval'])
on = lambda:None
off = lambda:None
refresh = lambda:None # 刷新周期重复闹钟

def _alarm(stop_event):
    import manager
    from mydatetime import getNow
    import player
    import time
    prev = getNow()
    minGap = datetime.timedelta(0, 300) # 超过300秒，认为是睡眠/待机唤醒
    count = 0
    alarm = False # “闹铃”提醒状态
    while 1:
        if stop_event.is_set():
            break
        cur = getNow()
        if (cur - prev >= minGap):
            manager.refreshWeekly()
            manager.resortAndSave()
            refresh()
        prev = cur
        reminds = manager.getReminds() # 获取需要闹铃提醒的闹钟
        length = len(reminds)
        player.play(reminds[0]['sound'] if length else None)
        if not alarm and length:
            alarm = True
            _taskbarThread.start()
            _screenThread.start()
            on()
            count = 0
        if alarm and not len(reminds):
            alarm = False
            player.play(None)
            _taskbarThread.stop()
            _screenThread.stop()
            off()
        if alarm and count > 10 * alarmLast:
            alarm = False
            player.play(None)
            _taskbarThread.stop()
            _screenThread.stop()
            manager.later(getNow() + alarmInterval) # 推迟提醒
            off()
        count += 1
        time.sleep(0.1)
    return

from sine.threads import ReStartableThread as _ReStartableThread

_alarmThread = _ReStartableThread(target=_alarm)

def start():
    _alarmThread.start()

def stop():
    _alarmThread.stop()

def _taskbar(stop_event):
    import time
    while 1:
        if stop_event.is_set():
            break
        _flash()
        time.sleep(1)
    return

try:
    if config['taskbar_flash']:
        from sine.flashWindow import flash as _flash
        _taskbarThread = _ReStartableThread(target=_taskbar)
except ImportError, e:
    warn('taskbar flashing not supported.', e)
finally:
    if '_taskbarThread' not in locals():
        _taskbarThread = _ReStartableThread(target=None)


tokens = config['screen_flash_mode']

def _screen(stop_event):
    import os
    import manager
    import time
    import formatter
    fmt = formatter.create(config, config['flash_format'])
    sleep_len = 1.0 / len(tokens)
    pos = 0
    last = '2'
    while 1:
        if stop_event.is_set():
            break
        if pos >= len(tokens):
            pos = 0
            last = '2' # 使之更新列表
        if last != tokens[pos]:
            last = tokens[pos]
            if last == '0':
                os.system('cls')
            elif last == '1':
                reminds = manager.getReminds() # 获取需要闹铃提醒的闹钟
                string = ''
                for i, clock in enumerate(reminds):
                    string += fmt(i+1, clock) + '\n'
                print string
        pos += 1
        time.sleep(sleep_len)
    return

_screenThread = _ReStartableThread(target=_screen)
