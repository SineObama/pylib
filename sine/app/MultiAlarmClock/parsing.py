# coding=utf-8

import datetime
from exception import ParseException

# format to read and corresponding fields to be replaced
tformats = [  '%M',
          '%H:',
               ':%S',
          '%H:%M',
            ':%M:%S',
          '%H:%M:%S']
tfieldss = [     ['minute', 'second', 'microsecond'],
         ['hour', 'minute', 'second', 'microsecond'],
                           ['second', 'microsecond'],
         ['hour', 'minute', 'second', 'microsecond'],
                 ['minute', 'second', 'microsecond'],
         ['hour', 'minute', 'second', 'microsecond']]
dformats = [   '-%d',
             '%m-%d',
          '%y-%m-%d']
dfieldss = [              ['day'],
                 ['month', 'day'],
         ['year', 'month', 'day']]

def tryReplace(now, s, formats, fieldss):
    target = None
    for i, fm in enumerate(formats):
        try:
            target = datetime.datetime.strptime(s, fm)
        except Exception, e:
            continue
        break
    if not target:
        return None
    d = {}
    for field in fieldss[i]:
        exec('d[field] = target.' + field)
    return now.replace(**d)

# refactor by parsing step by step, and catching Exception
# parse return the parsed object and the remain string
zero = datetime.datetime.min.replace(year=1900) # 用于计算时长类数据
def parseString(s):
    '''length check should be outside for further info'''
    if len(s) == 0:
        raise ParseException('no string to parse')
    s = s.split(' ', 1)
    return s[0], (s[1] if len(s) > 1 else '')
def parseTime(s, reference):
    s = s.split(' ', 1)
    target = tryReplace(reference, s[0], tformats, tfieldss)
    if not target:
        raise ParseException('can not parse as time: ' + s[0])
    return target, (s[1] if len(s) > 1 else '')
def parseDateAndTime(s, reference): # (date) time
    try:
        target, s = parseTime(s, reference)
    except ParseException as e:
        s = s.split(' ', 1)
        if len(s) < 2:
            raise ParseException('can not parse as time (no date): ' + s[0])
        target = tryReplace(reference, s[0], dformats, dfieldss)
        if not target:
            raise ParseException('can not parse as date or time: ' + s[0])
        target, s = parseTime(s[1], target)
    return target, s
def parseDateTimeByOrder(order, s, now):
    if order.endswith('d'):
        target, remain = parseTime(s, zero)
        return target - zero + now, remain
    else:
        return parseDateAndTime(s, now)
def parseIndexWithDefaultZero(s):
    if len(s) == 0:
        return 0, ''
    s = s.split(' ', 1)
    try:
        index = int(s[0])
    except ValueError as e:
        raise ParseException('can not parse as int: ' + s[0])
    return index, (s[1] if len(s) > 1 else '')
def parseAllToIndex(s):
    '''return [] when empty'''
    if len(s) == 0:
        return []
    s = s.split()
    indexs = []
    try:
        for i in s:
            indexs.append(int(i))
    except ValueError as e:
        raise ParseException('can not parse as int: ' + i)
    return indexs

__all__ = ['zero', 'parseString', 'parseTime', 'parseDateAndTime', 'parseDateTimeByOrder', 'parseIndexWithDefaultZero', 'parseAllToIndex']
