# coding=utf-8
'''
监听线程。检查闹钟状态并进行屏幕闪烁和播放铃声。
需要设置提醒延迟remindDelay(datetime.timedelta)，启动回调on和关闭回调off。
提供start和stop接口，可重复启动。
'''

from data import data as _data
config = _data['config']

lastTime = 30
remindDelay = None
on = None
off = None

def _alarm(stop_event):
    import manager
    from mydatetime import getNow
    import player
    import time
    count = 0
    alarm = False # “闹铃”提醒状态
    while 1:
        if stop_event.is_set():
            break
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
        if alarm and count > 10 * lastTime:
            alarm = False
            player.play(None)
            _taskbarThread.stop()
            _screenThread.stop()
            manager.later(getNow() + remindDelay) # 推迟提醒
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
        _FlashWindow()
        time.sleep(1)
    return

try:
    if config['taskbar_flash']:
        from sine.api import FlashWindow as _FlashWindow
        _taskbarThread = _ReStartableThread(target=_taskbar)
except ImportError, e:
    raise e#todo


tokens = config['screen_flash_mode']

def _screen(stop_event):
    import manager
    from sine.helpers import cls
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
                cls()
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