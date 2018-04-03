# coding=utf-8
'''
“闹铃”播放器。可多次调用，前后值相同不会产生影响。
唯一接口：
play(wav_filename)循环播放wav音频（不可为'default'）
play('default')原版windows beep声（出现win7没有声音的问题，但在播放音乐时有声音，也可能是声卡问题）
play('')不作变化
play(None)停止
此外还可以用win32自带系统声音：
'SystemAsterisk' Asterisk
'SystemExclamation' Exclamation
'SystemExit' Exit Windows
'SystemHand' Critical Stop
'SystemQuestion' Question
'SystemDefault'
'''

from sine.threads import ReStartableThread as _ReStartableThread

def _alarm(stop_event):
    import time
    import winsound
    count = 0
    while 1:
        if stop_event.is_set():
            break
        if count % 5 == 1 or count % 5 == 3:
            winsound.Beep(600, 50)
        count += 1
        time.sleep(0.1)
    return

_name = None # 必然非空''
_beep = 'default'
_alarmThread = _ReStartableThread(target=_alarm)

def play(name):
    import winsound
    global _name
    if _name == name or name == '':
        return
    if _name != None: # 正在播则停止当前beep或者音乐
        if _name == _beep:
            _alarmThread.stop()
        else:
            winsound.PlaySound(None, winsound.SND_PURGE)
    if name != None:
        if name == _beep:
            _alarmThread.start()
        else:
            # 播放系统声音，或用绝对路径播放wav音频（后者优先）
            winsound.PlaySound(name, winsound.SND_ALIAS | winsound.SND_ASYNC | winsound.SND_LOOP)
            winsound.PlaySound(name, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
    _name = name
    return

_extraLegal = [
'',
_beep,
'SystemAsterisk',
'SystemExclamation',
'SystemExit',
'SystemHand',
'SystemQuestion',
'SystemDefault']

def assertLegal(name):
    '''检查音频文件是否存在或为以上合法系统值。'''
    from exception import ClientException
    import os
    if name in _extraLegal:
        return
    if os.path.exists(name):
        return
    if os.path.exists(name + '.wav'):
        return
    raise ClientException('wav file \''+name+'\' or \''+name+'.wav\' not exists or not system sound')
