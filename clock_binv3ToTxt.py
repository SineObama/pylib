# coding=utf-8

# 导入原来的路径，用于对应上使用pickle反序列化所需要的实体类entity.AlarmClock
import sys
import os
from sine.path import Path
location = Path(__file__).join('..').join('sine').join('app').join('MultiAlarmClock')
sys.path.append(location)

import json
import sine.myPickle as _pickle
import entity

src = raw_input('enter source data file with postfix binv3:')
if src == '':
    src ='clocks.binv3'
dst = raw_input('enter new json file name:')
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
        json.dump(clocks, file, default=entity.AlarmClock.default, ensure_ascii=False)
    print 'data convert finish.'
except MyException, e:
    print 'convert canceled.', e
except Exception, e:
    import traceback
    traceback.print_exc()
finally:
    print 'press enter to exit'
    raw_input()

