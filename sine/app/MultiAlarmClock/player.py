# coding=utf-8
'''
“闹铃”播放器。可多次调用，前后值相同不会产生影响。
唯一接口：
play(wav_filename)循环播放wav音频（不可为'default'）
play('default')原版windows beep声（出现win7没有声音的问题，但在播放音乐时有声音，也可能是声卡问题）
play('')不作变化
play(None)停止
此外还可以用系统声音：
'SystemAsterisk' Asterisk
'SystemExclamation' Exclamation
'SystemExit' Exit Windows
'SystemHand' Critical Stop
'SystemQuestion' Question
'''

from sine.threads import ReStartableThread as _ReStartableThread
from data import data

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

_name = None # 必然非空''
_beep = 'default'
_alarmThread = _ReStartableThread(_alarm)

def play(name):
    global _name
    if _name == name or name == '':
        return
    if _name != None: # 正在播则停止当前beep或者音乐
        if _name == _beep:
            _alarmThread.stop()
        else:
            _winsound.PlaySound(None, _winsound.SND_PURGE)
    if name != None:
        if name == _beep:
            _alarmThread.start()
        else:
            # 播放系统声音，或用绝对路径播放wav音频（后者优先）
            _winsound.PlaySound(name, _winsound.SND_ALIAS | _winsound.SND_ASYNC | _winsound.SND_LOOP)
            _winsound.PlaySound(data['path0'] + name, _winsound.SND_FILENAME | _winsound.SND_ASYNC | _winsound.SND_LOOP)
    _name = name
    return
