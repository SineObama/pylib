# coding=utf-8
'''“闹铃”播放器，为了方便多次调用（可以重复调用，连续两次使用同样的值不会产生影响）
play(wav_filename)循环播放wav音频
play('')原版beep声
play(None)停止'''

import threading as __threading
import winsound as __winsound
import time as __time

__quit = True
__name = None
__alarmThread = None

def __alarm():
    global __quit
    count = 0
    while 1:
        if __quit:
            break
        if count % 5 == 1 or count % 5 == 3:
            __winsound.Beep(600, 50)
        count += 1
        __time.sleep(0.1)
    return

def play(name):
    global __quit
    global __name
    global __alarmThread
    if __name == name:
        return
    if __name != None: # 正在播
        if __name == '':
            __quit = True
            __alarmThread.join(2)
            if __alarmThread.is_alive():
                raise RuntimeError('thread can not exit')
        else:
            __winsound.PlaySound(None, __winsound.SND_PURGE)
    if name != None:
        if name == '': # default beep
            __quit = False
            __alarmThread = __threading.Thread(target=__alarm)
            __alarmThread.setDaemon(True)
            __alarmThread.start()
        else:
            __winsound.PlaySound(name, __winsound.SND_FILENAME | __winsound.SND_ASYNC | __winsound.SND_LOOP)
    __name = name
    return
