
# coding: gbk

# In[ ]:

# 计算妖灵簿“翻滚吧宝藏”的收益与选择（“见好就收”或者“免费继续”）
# 假设max_count个位置出现谛听概率独立且为p，而出现x个谛听的收益是profit[x]
# 总共的开局次数为start，免费继续次数为5
p = 1.0/3
max_count = 5
profit = [1, 2, 3, 10, 45, 165]
start = 7
keep = 5


# In[ ]:

# 预计算若干转出若干谛听的概率
def c(n, m):
    '''组合'''
    if m > n:
        raise ArithmeticError
    if m > n / 2:
        return c(n, n - m)
    result = 1
    for i in range(n - m + 1, n + 1):
        result *= i
    for i in range(2, m + 1):
        result /= i
    return result
def app(x, y):
    '''随机x个，出现y个谛听的概率'''
    if y > x:
        raise ArithmeticError
    result = c(x, y)
    for i in range(y):
        result *= p
    for i in range(x - y):
        result *= 1 - p
    return result
appear = {}
for x in range(1, max_count + 1):
    for y in range(0, x + 1):
        appear[(x, y)] = app(x, y)


# In[ ]:

# 输入量化收益或者使用默认值
print ('分别输入出现0-%d个谛听的量化收益，以空格分离（直接回车使用默认值）' % (max_count))
while True:
    string = raw_input()
    try:
        if len(string) == 0:
            print '使用默认值：', profit
        else:
            strings = string.split()
            if len(strings) != max_count + 1:
                raise Exception('必须输入%d个数字，以空格分离' % (max_count + 1))
            new = []
            for s in strings:
                new.append(int(s))
            profit = new
    except Exception, e:
        print e
    else:
        break


# In[ ]:

dic = {}
def func(cur, start, keep):
    '''计算当前出现cur个谛听，开局次数还剩start，继续次数还剩keep时的收益和选择
    使用递归方式计算，以字典保存结果用于可能的重复利用'''
    if dic.has_key((cur, start, keep)):
        return dic[(cur, start, keep)]
    # 计算“见好就收”
    result1 = profit[cur]
    if start > 0:
        for i in range(0, max_count + 1):
            result1 += appear[(max_count, i)] * func(i, start - 1, keep)[1]
    # 计算“继续”
    result2 = 0
    if cur < max_count and keep > 0:
        for i in range(0, max_count - cur + 1):
            result2 += appear[(max_count - cur, i)] * func(cur + i, start, keep - 1)[1]
    if result1 > result2:
        rtn = (0, result1)
    else:
        rtn = (1, result2)
    dic[(cur, start, keep)] = rtn
    return rtn


# In[ ]:

# 计算并输出总体期望
e = 0
for i in range(0, max_count + 1):
    e += appear[(max_count, i)] * func(i, start - 1, keep)[1]
print '总期望', e


# In[ ]:

print '以默认的%d次开局，%d次继续开始' % (start, keep)
print '每次输入谛听数，并按照指示结束或继续；或者输入3个数字（当前谛听数、开局次数、继续次数，用空格分离）设置进度；输入q退出'
start -= 1
cur = 0
end = False
while True:
    try:
        string = raw_input()
        if string == 'q':
            break
        strings = string.split()
        
        ok = False
        if len(strings) == 1:
            if end:
                raise Exception('次数已用完，不可继续。请退出或者设置进度')
            cur = int(strings[0])
            ok = True
        if len(strings) == 3:
            c = int(strings[0])
            s = int(strings[1])
            k = int(strings[2])
            if c < 0 or c > max_count:
                raise Exception('谛听数超出范围')
            if s < 0:
                raise Exception('开局次数必须非负')
            if k < 0:
                raise Exception('继续次数必须非负')
            cur = c; start = s; keep = k
            ok = True
        if not ok:
            raise Exception('只能输入1个或3个数字')
            
        print '当前状态', (cur, start, keep)
        if start == 0 and (cur == max_count or keep == 0):
            print '已不可继续'
            end = True
        result = func(cur, start, keep)
        if result[0] == 0:
            print '请结束。剩余期望', result[1]
            start -= 1
        else:
            print '请继续。剩余期望', result[1]
            keep -= 1
    except Exception, e:
        print e

