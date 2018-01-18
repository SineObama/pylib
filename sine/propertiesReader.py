# coding=utf-8

def read(path):
    f = open(path, 'rb')
    kv = {}
    for line in f:
        line = line.replace('\r', '').replace('\n', '').strip()
        if line.startswith('#') or line == '':
            continue
        tokens = line.split('=', 1)
        kv[tokens[0].strip()] = tokens[1].strip() if len(tokens) == 2 else True
    f.close()
    return kv
