# coding=utf-8

'''
监听线程。检查闹钟状态并进行屏幕闪烁和播放铃声。
需要设置提醒延迟remindDelay，启动回调on和关闭回调off。
提供start和stop接口，可重复启动。
'''

lastTime = 30
remindDelay = None
on = None
off = None

def _alarm(stop_event):
    from manager import instance as manager
    from mydatetime import getNow
    from sine.api import FlashWindow
    from sine.helpers import cls
    import player
    import time
    count = 0 # 时间计数
    alarm = False # “闹铃”提醒状态
    while 1:
        if stop_event.is_set():
            break
        reminds = manager.getReminds() # 获取需要闹铃提醒的闹钟
        length = len(reminds)
        if length:
            sound = reminds[0]['sound']
        if not alarm and length:
            alarm = True
            player.play('' if sound == None else sound)
            count = 0
            on()
        if alarm and not len(reminds):
            alarm = False
            player.play(None)
            off()
        if alarm and count > 10 * lastTime:
            alarm = False
            player.play(None)
            manager.later(getNow() + remindDelay) # 推迟提醒
            off()
        if alarm:
            player.play(sound if sound != None else '')
            if count % 10 == 0:
                FlashWindow()
            if count % 5 == 0:
                cls()
            if count % 5 == 1:
                string = ''
                for clock in reminds:
                    string += str(clock) + '\n'
                print string
        count += 1
        time.sleep(0.1)
    return

from sine.threads import ReStartableThread as _ReStartableThread

_alarmThread = _ReStartableThread(_alarm)

def start():
    _alarmThread.start()

def stop():
    _alarmThread.stop()
