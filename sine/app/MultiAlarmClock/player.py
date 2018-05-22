# coding=utf-8
'''
“闹铃”播放器。可多次调用，前后值相同不会产生影响。
唯一接口：
play(wav_filename)循环播放wav音频（不可为'default'）
play('default')播放windows beep声，可以在配置文件beep.conf设置样式（出现win7没有声音的问题，但在播放音乐时有声音，也可能是声卡问题）
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

import winsound
from sine.threads import ReStartableThread
from exception import ClientException

_list = []

def _init():
    def create_beep(Hz, last):
        def __func_bepp():
            winsound.Beep(Hz, last)
        return __func_bepp

    import time
    def create_sleep(last):
        def __func_sleep():
            time.sleep(last)
        return __func_sleep

    import data
    from initUtil import warn
    import sine.propertiesReader as reader

    # 读入beep样式信息
    beep_filename = 'beep.conf'
    default_pattern = [(600,50),(200,),(600,50),(300,)]
    lines = []
    try:
        data.useDefault(data.data['location'], beep_filename)
        lines = reader.readAsList(beep_filename)
    except Exception, e:
        warn('load beep pattern from file', beep_filename, 'failed, will use default value.', e)
        beep_pattern = default_pattern

    try:
        if 'beep_pattern' not in locals():
            beep_pattern = []
            for i, (s, unuse) in enumerate(lines):
                array = s.split(',')
                if len(array) > 1:
                    frequency = int(array[0].strip())
                    if (frequency < 37 or frequency > 32767):
                        raise ClientException('frequency must be in 37 thru 32767, but meet ' + frequency)
                    duration = int(array[1].strip())
                    if (duration <= 0):
                        raise ClientException('duration must be positive, but meet ' + duration)
                    if (duration > 10000):
                        raise ClientException('duration is too big, more than 10000, but meet ' + duration)
                    beep_pattern.append((frequency, duration))
                else:
                    last = int(array[0].strip())
                    if (last <= 0):
                        raise ClientException('last must be positive, but meet ' + last)
                    beep_pattern.append((last,))
    except Exception, e:
        warn('parse beep pattern failed, will use default value.', e)
        beep_pattern = default_pattern

    for s in beep_pattern:
        if len(s) > 1:
            _list.append(create_beep(s[0], s[1]))
        else:
            _list.append(create_sleep(s[0] / 1000.0))

_init()

def _alarm(stop_event):
    while 1:
        for func in _list:
            if stop_event.is_set():
                return
            func()
    return

_name = None # 必然非空''
_beep = 'default'
_alarmThread = ReStartableThread(target=_alarm)

def play(name):
    global _name
    if _name == name or name == '':
        return
    if _name != None: # 正在播则停止当前beep或者音乐
        _alarmThread.stop()
        winsound.PlaySound(None, winsound.SND_PURGE)
    if name != None:
        if name == _beep or not isLegal(name):
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

def isLegal(name):
    '''检查音频文件是否存在或为以上合法系统值。'''
    import os
    if name in _extraLegal:
        return True
    if os.path.isfile(name):
        return True
    if os.path.isfile(name + '.wav'):
        return True
    return False

def assertLegal(name):
    if not isLegal(name):
        raise ClientException('wav file \''+name+'\' or \''+name+'.wav\' not exists or not system sound')
