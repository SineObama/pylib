# coding=utf-8
'''
全局数据。包括配置的读取和验证。
'''

import os.path as spath
import shutil

data = {}

# 加载配置并检查。对于缺少的配置赋予默认值并暂停警告

def _init():
    def boolConverter(s):
        '''对空或者0开头的字符串视为False，其余视为True'''
        if s == '' or s.startswith('0'):
            return False
        return True

    import sine.propertiesReader as reader
    from sine.path import Path
    from initUtil import warn

    location = Path(__file__).join('..')
    data['location'] = location

    # 从文件读入全局配置，暂时保存为字符串
    conf_filename = 'clock.conf'
    allMiss = False
    config = {}
    try:
        useDefault(location, conf_filename)
        config = reader.readAsDict(conf_filename)
    except Exception, e:
        warn('load config from file', conf_filename, 'failed, will use default value.', e)
        allMiss = True

    # 为缺失值填充默认配置(键, 默认值, 转换器)
    default_config = [
    ('warning_pause', True, boolConverter),
    ('taskbar_flash', True, boolConverter),
    ('screen_flash_mode', '0111101111', None),
    ('alarm_last', 30, int),
    ('alarm_interval', 300, int),
    ('default_remindAhead', 60, int),
    ('default_sound', 'default', None),
    ('format', '%Y-%m-%d %H:%M:%S %%warn %%3idx %%3state %%msg', None),
    ('flash_format', '%Y-%m-%d %H:%M:%S %%msg', None),
    ('warn', '!!!', None),
    ('state.ON', 'ON', None),
    ('state.OFF', 'OFF', None),
    ('datafile', 'clocks.txt', None)]

    if allMiss:
        for (key, default, converter) in default_config:
            config[key] = default
    else:
        for (key, default, converter) in default_config:
            if not config.has_key(key):
                warn('missing config \'' + key + '\', will use default value \'' + str(default) + '\'.')
                config[key] = default
            elif converter:
                try:
                    config[key] = converter(config[key])
                except Exception, e:
                    warn('parsing config \'' + key + '=' + str(config[key]) + '\' failed, will use default value \'' + str(default) + '\'.', e)
                    config[key] = default

    data['config'] = config

    # 读入日期和时间格式配置
    format_filename = 'time.conf'
    try:
        useDefault(location, format_filename)
        config = reader.readAsList(format_filename)
        for i, (k, v) in enumerate(config):
            config[i] = (k, v.split(','))
    except Exception, e:
        warn('load time format from file', format_filename, 'failed, will use default value.', e)
        config = [(   '%M'   ,        ['minute', 'second', 'microsecond']),
                  ('%H:'     ,['hour', 'minute', 'second', 'microsecond']),
                  (     ':%S',                  ['second', 'microsecond']),
                  ('%H:%M'   ,['hour', 'minute', 'second', 'microsecond']),
                  (  ':%M:%S',        ['minute', 'second', 'microsecond']),
                  ('%H:%M:%S',['hour', 'minute', 'second', 'microsecond'])]
    data['timeFormats'] = config

    format_filename = 'date.conf'
    try:
        useDefault(location, format_filename)
        config = reader.readAsList(format_filename)
        for i, (k, v) in enumerate(config):
            config[i] = (k, v.split(','))
    except Exception, e:
        warn('load date format from file', format_filename, 'failed, will use default value.', e)
        config = [(     '/%d',                 ['day']),
                  (   '%m/%d',        ['month', 'day']),
                  ('%y/%m/%d',['year', 'month', 'day'])]
    data['dateFormats'] = config

def useDefault(location, filename):
    '''配置文件不存在时尝试从默认文件复制一份'''
    suffix = '.default'
    filepath = filename
    if not spath.isfile(filepath):
        defaultpath = location.join(filename + suffix)
        if spath.isfile(defaultpath):
            shutil.copyfile(defaultpath, filepath)

_init()
