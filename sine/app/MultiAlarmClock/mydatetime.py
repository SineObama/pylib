# coding=utf-8

import datetime

everyday = '1234567'
day = datetime.timedelta(1)

def getNow(): # 用于在可能的测试中控制时间
    return datetime.datetime.now()

def getNextFromWeekday(now, time, weekdays):
    '''为星期重复闹钟选择下一个有效时间。
    使用time的时分秒，找到一个比now晚，且有效的时间（在 weekdays 表示的星期中）
    repeat如果会空则默认每天都可以'''
    if weekdays.isspace():
        weekdays = everyday
    nexttime = now.replace(hour=time.hour, minute=time.minute, second=time.second, microsecond=time.microsecond)
    while nexttime <= now or str(nexttime.weekday()+1) not in weekdays:
        nexttime += day
    return nexttime
