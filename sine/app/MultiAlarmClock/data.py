# coding=utf-8
'''
全局数据。
'''

class _HashableDict(dict):
	def __init__(self, *args, **kw):
		super(_HashableDict, self).__init__(*args, **kw)
		self._object_for_hash = object()
	def __hash__(self):
		return hash(self._object_for_hash)

data = _HashableDict()
data['clocks'] = []

# 加载配置文件
conf_filename = 'clock.conf'
try:
    f = open(conf_filename, 'rb')
    config = {}
    for line in f:
        line = line.replace('\r', '').replace('\n', '')
        if line.startswith('#') or line == '':
            continue
        tokens = line.split('=', 1)
        if len(tokens) == 2:
            config[tokens[0]] = tokens[1]
        else:
            config[tokens[0]] = True
    f.close()
except Exception, e:
    print e
    print 'load from file', conf_filename, 'failed'
    sys.exit(1)

# 补充默认配置
stop = False
def fillOrConvert(key, default, converter=None):
	global stop
	if not config.has_key(key):
		print 'missing config key \'' + key + '\', will use default value \'' + str(default) + '\''
		stop = True
		config[key] = default
	elif converter:
		try:
			config[key] = converter(config[key])
		except Exception, e:
			print e
			print 'parsing config \'' + key + '=' + str(config[key]) + '\' failed, will use default value \'' + str(default) + '\''
			stop = True
fillOrConvert('alarm_last', 30, int)
fillOrConvert('alarm_interval', 300, int)
fillOrConvert('format', '%Y-%m-%d %H:%M:%S %%warn %%3idx %%3state %%msg')
fillOrConvert('warn', '!!!')
fillOrConvert('state.ON', 'ON')
fillOrConvert('state.OFF', 'OFF')
fillOrConvert('datafile', 'clocks.binv2')

data['config'] = config

if stop:
	print 'press enter to continue'
	raw_input()
