# coding=utf-8
'''
全局数据。包括初始化。
'''

data = {}

# 加载配置并检查。对于缺少的配置赋予默认值并暂停警告
warning = False # 显示警告，等待回车继续（清屏）

def warn(*args):
    global warning
    s = ''
    if len(args) > 0:
        s = args[0]
        for i in args[1:]:
            s += ' ' + str(i)
    print s
    warning = True

def _init():
    import sine.propertiesReader as reader

    # 从文件读入全局配置，暂时保存为字符串
    _conf_filename = 'clock.conf'
    try:
        config = {}
        config = reader.readAsDict(_conf_filename)
    except Exception, e:
        warn('load config from file', _conf_filename, 'failed:' + repr(e))

    # 为缺失值填充默认配置(键, 默认值, 转换器)
    default_config = [
    ('warning_pause', True, bool),
    ('taskbar_flash', True, bool),
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
    ('datafile', 'clocks.binv3', None)]

    for (key, default, converter) in default_config:
        if not config.has_key(key):
            warn('missing config \'' + key + '\', will use default value \'' + str(default) + '\'')
            config[key] = default
        elif converter:
            try:
                config[key] = converter(config[key])
            except Exception, e:
                warn('parsing config \'' + key + '=' + str(config[key]) + '\' failed, will use default value \'' + str(default) + '\'. ' + repr(e))

    import player
    from exception import ClientException
    try:
        player.assertLegal(config['default_sound'])
    except ClientException, e:
        warn('default sound illeagal, will use default.', e)
        config['default_sound'] = 'default'

    data['config'] = config

    # 读入日期和时间格式配置
    _format_filename = 'time.conf'
    try:
        config = reader.readAsList(_format_filename)
        for i, (k, v) in enumerate(config):
            config[i] = (k, v.split(','))
    except Exception, e:
        warn('load time format from file', _format_filename, 'failed, will use default value.', repr(e))
        config = [(   '%M'   ,        ['minute', 'second', 'microsecond']),
                  ('%H:'     ,['hour', 'minute', 'second', 'microsecond']),
                  (     ':%S',                  ['second', 'microsecond']),
                  ('%H:%M'   ,['hour', 'minute', 'second', 'microsecond']),
                  (  ':%M:%S',        ['minute', 'second', 'microsecond']),
                  ('%H:%M:%S',['hour', 'minute', 'second', 'microsecond'])]
    data['timeFormats'] = config

    _format_filename = 'date.conf'
    try:
        config = reader.readAsList(_format_filename)
        for i, (k, v) in enumerate(config):
            config[i] = (k, v.split(','))
    except Exception, e:
        warn('load date format from file', _format_filename, 'failed, will use default value.', repr(e))
        config = [(     '/%d',                 ['day']),
                  (   '%m/%d',        ['month', 'day']),
                  ('%y/%m/%d',['year', 'month', 'day'])]
    data['dateFormats'] = config

_init()
