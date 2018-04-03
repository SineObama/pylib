# coding=utf-8
'''
输入字符串的转化方法。
以判定为前提。（比如认定接下来出现的是一个时间）
流程上，从上一步剩余字符串开始转化，成功则返回转化后剩余字符串。
'''

import datetime
from exception import ParseException, NoStringException
from data import data

def _tryReplace(ref, s, formats):
    '''
    从formats中选择第一个合适的格式，把字符串s转化为datetime格式，再把指定字段替换到ref中，并返回。
    '''
    target = None
    for fm in formats:
        try:
            target = datetime.datetime.strptime(s, fm[0])
        except Exception, e:
            continue
        break
    if not target:
        return None
    d = {}
    for field in fm[1]:
        d[field] = target.__getattribute__(field)
    return ref.replace(**d)

zero = datetime.datetime.min.replace(year=1900) # 用于计算时长类数据
def parseString(s):
    s = s.strip()
    if len(s) == 0:
        raise NoStringException()
    s = s.split(None, 1)
    return s[0], (s[1] if len(s) > 1 else '')
def parseTime(s, reference):
    s = s.strip()
    if len(s) == 0:
        raise ParseException('no string to parse as time')
    s = s.split(None, 1)
    target = _tryReplace(reference, s[0], data['timeFormats'])
    if not target:
        raise ParseException('can not parse as time: ' + s[0])
    return target, (s[1] if len(s) > 1 else '')
def parseDateAndTime(s, reference):
    '''尝试以time转换，不行就以date time转换'''
    s = s.strip()
    if len(s) == 0:
        raise NoStringException()
    try:
        target, s = parseTime(s, reference)
    except ParseException as e:
        s = s.split(None, 1)
        if len(s) < 2:
            raise ParseException('can not parse as time (no date): ' + s[0])
        target = _tryReplace(reference, s[0], data['dateFormats'])
        if not target:
            raise ParseException('can not parse as date or time: ' + s[0])
        target, s = parseTime(s[1], target)
    return target, s
def parseDateTime(s, now):
    '''考虑带‘-’的倒计时模式'''
    s = s.strip()
    if s.startswith('-'):
        target, remain = parseDateAndTime(s[1:], zero)
        return target - zero + now, remain
    else:
        return parseDateAndTime(s, now)
def parseInt(s, default=None):
    '''转化一个int。无字符串时使用default值，无值时异常。'''
    s = s.strip()
    if len(s) == 0:
        if default == None:
            raise NoStringException()
        else:
            return default, ''
    s = s.split(None, 1)
    try:
        index = int(s[0])
    except ValueError as e:
        raise ParseException('can not parse as integer: ' + s[0])
    return index, (s[1] if len(s) > 1 else '')
def parseAllToIndex(s):
    s = s.split()
    indexs = []
    try:
        for i in s:
            indexs.append(int(i))
    except ValueError as e:
        raise ParseException('can not parse as int: ' + i)
    return indexs

__all__ = ['zero', 'parseString', 'parseTime', 'parseDateAndTime', 'parseDateTime', 'parseInt', 'parseAllToIndex']
