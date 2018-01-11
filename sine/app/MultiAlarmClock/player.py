# coding=utf-8
'''
“闹铃”播放器。可多次调用，前后值相同不会产生影响。
唯一接口：
play(wav_filename)循环播放wav音频（带后缀）
play('')原版windows beep声（win7可能不适用）
play(None)停止
此外还可以用系统声音：
'SystemAsterisk' Asterisk
'SystemExclamation' Exclamation
'SystemExit' Exit Windows
'SystemHand' Critical Stop
'SystemQuestion' Question
'''

from sine.threads import ReStartableThread as _ReStartableThread

import winsound as _winsound

def _alarm(stop_event):
    import time
    count = 0
    while 1:
        if stop_event.is_set():
            break
        if count % 5 == 1 or count % 5 == 3:
            _winsound.Beep(600, 50)
        count += 1
        time.sleep(0.1)
    return

_name = None
_alarmThread = _ReStartableThread(_alarm)

def play(name):
    global _name
    if _name == name:
        return
    if _name != None: # 正在播则停止当前beep或者音乐
        if _name == '':
            _alarmThread.stop()
        else:
            _winsound.PlaySound(None, _winsound.SND_PURGE)
    if name != None:
        if name == '': # default beep
            _alarmThread.start()
        else:
            _winsound.PlaySound(name, _winsound.SND_ALIAS | _winsound.SND_ASYNC | _winsound.SND_LOOP)
    _name = name
    return
