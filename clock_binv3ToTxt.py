# coding=utf-8

import sys
from sine.path import Path
location = Path(__file__).join('..').join('sine').join('app').join('MultiAlarmClock')
sys.path.append(location)

import json
import sine.myPickle as _pickle
from sine.app.MultiAlarmClock.entity import AlarmClock
import entity

src = raw_input('enter source data file with postfix binv3:')
if src == '':
    src ='clocks.binv3'
dst = raw_input('enter new json file name:')
if dst == '':
    dst ='clocks.txt'
y = raw_input('this will replace new file if exists, enter y to continue:')
if y == 'y' or y == 'Y':
    clocks = _pickle.load(location.join(src), [])
    with open(location.join(dst), 'w') as file:
        json.dump(clocks, file, default=AlarmClock.default, ensure_ascii=False) # 大概是理解为按原字节串直接写进去，就保留了原本的编码
    print 'data convert finish.'
    print 'press enter to continue'
    raw_input()
