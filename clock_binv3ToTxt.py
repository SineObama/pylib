# coding=utf-8

# 导入原来的路径，用于对应上使用pickle反序列化所需要的实体类entity.AlarmClock
import sys
import os
from sine.path import Path
location = Path(__file__).join('..').join('sine').join('app').join('MultiAlarmClock')
sys.path.append(location)

import json
import sine.myPickle as _pickle
from entity import *

src = raw_input('enter source data file with postfix binv3:')
if src == '':
    src ='clocks.binv3'
dst = raw_input('enter new data file name:')
if dst == '':
    dst ='clocks.txt'

class MyException(Exception):
    pass

try:
    dst_path = location.join(dst)
    if os.path.isfile(dst_path):
        yn = raw_input('the output file exists, enter y to confirm replacement:')
        if yn.lower() != 'y':
            raise MyException()
    clocks = _pickle.load(location.join(src), [])
    with open(dst_path, 'w') as file:
        for clock in clocks:
            if clock['repeat'] == None:
                s = 'WeeklyClock'
                clock['weekdays'] = '       '
                clock.pop('repeat')
            elif type(clock['repeat']) == str:
                s = 'WeeklyClock'
                clock['weekdays'] = clock.pop('repeat')
            else:
                s = 'PeriodClock'
                clock['period'] = clock.pop('repeat')
            file.write(s + '(' + dict.__repr__(clock) + ')')
            file.write('\n')
    print 'data convert finish.'
except MyException, e:
    print 'convert canceled.', e
finally:
    print 'press enter to exit'
    raw_input()

