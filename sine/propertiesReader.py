# coding=utf-8

def readAsDict(path):
    '''读取为str类型的字典，value可为空，不为None'''
    with open(path, 'rb') as f:
        kv = {}
        for line in f:
            line = line.replace('\r', '').replace('\n', '').strip()
            if line.startswith('#') or line == '':
                continue
            tokens = line.split('=', 1)
            kv[tokens[0].strip()] = tokens[1].strip() if len(tokens) == 2 else ''
    return kv

def readAsList(path):
    '''根据顺序的需求，读取为str类型的双元组列表，第二个值可为空，不为None'''
    with open(path, 'rb') as f:
        l = []
        for line in f:
            line = line.replace('\r', '').replace('\n', '').strip()
            if line.startswith('#') or line == '':
                continue
            tokens = line.split('=', 1)
            l.append((tokens[0].strip(), tokens[1].strip() if len(tokens) == 2 else ''))
    return l
