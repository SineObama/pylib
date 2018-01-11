# coding=utf-8

def cls():
    import os
    os.system('cls')
    return

def substitute(array):
    import random
    for i in range(1, len(array)):
        j = random.randint(0, i)
        temp = array[i]
        array[i] = array[j]
        array[j] = temp
    return array

def diff(y1, y2):
    '''
    比较两个一维数组不一样的元素个数
    返回（不一样的个数，总数）
    '''
    count = 0
    total = y1.size
    for i in range(total):
        if (y1[i] != y2[i]):
            count += 1
    return count, total

# just for thread safe print
def info(*args):
    '''
    输出消息到控制台，带时间戳
    参数类似关键字print
    '''
    import sys
    import datetime
    string = ''
    for i in args:
        string += (str(i) + ' ')
    sys.stdout.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f ') + string + '\n')
