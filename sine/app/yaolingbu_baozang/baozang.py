
# coding: gbk

# In[ ]:

# �������鲾�������ɱ��ء���������ѡ�񣨡����þ��ա����ߡ���Ѽ�������
# ����max_count��λ�ó����������ʶ�����Ϊp��������x��������������profit[x]
# �ܹ��Ŀ��ִ���Ϊstart����Ѽ�������Ϊ5
p = 1.0/3
max_count = 5
profit = [1, 2, 3, 10, 45, 165]
start = 7
keep = 5


# In[ ]:

# Ԥ��������ת�����������ĸ���
def c(n, m):
    '''���'''
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
    '''���x��������y�������ĸ���'''
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

# ���������������ʹ��Ĭ��ֵ
print ('�ֱ��������0-%d���������������棬�Կո���루ֱ�ӻس�ʹ��Ĭ��ֵ��' % (max_count))
while True:
    string = raw_input()
    try:
        if len(string) == 0:
            print 'ʹ��Ĭ��ֵ��', profit
        else:
            strings = string.split()
            if len(strings) != max_count + 1:
                raise Exception('��������%d�����֣��Կո����' % (max_count + 1))
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
    '''���㵱ǰ����cur�����������ִ�����ʣstart������������ʣkeepʱ�������ѡ��
    ʹ�õݹ鷽ʽ���㣬���ֵ䱣�������ڿ��ܵ��ظ�����'''
    if dic.has_key((cur, start, keep)):
        return dic[(cur, start, keep)]
    # ���㡰���þ��ա�
    result1 = profit[cur]
    if start > 0:
        for i in range(0, max_count + 1):
            result1 += appear[(max_count, i)] * func(i, start - 1, keep)[1]
    # ���㡰������
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

# ���㲢�����������
e = 0
for i in range(0, max_count + 1):
    e += appear[(max_count, i)] * func(i, start - 1, keep)[1]
print '������', e


# In[ ]:

print '��Ĭ�ϵ�%d�ο��֣�%d�μ�����ʼ' % (start, keep)
print 'ÿ��������������������ָʾ�������������������3�����֣���ǰ�����������ִ����������������ÿո���룩���ý��ȣ�����q�˳�'
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
                raise Exception('���������꣬���ɼ��������˳��������ý���')
            cur = int(strings[0])
            ok = True
        if len(strings) == 3:
            c = int(strings[0])
            s = int(strings[1])
            k = int(strings[2])
            if c < 0 or c > max_count:
                raise Exception('������������Χ')
            if s < 0:
                raise Exception('���ִ�������Ǹ�')
            if k < 0:
                raise Exception('������������Ǹ�')
            cur = c; start = s; keep = k
            ok = True
        if not ok:
            raise Exception('ֻ������1����3������')
            
        print '��ǰ״̬', (cur, start, keep)
        if start == 0 and (cur == max_count or keep == 0):
            print '�Ѳ��ɼ���'
            end = True
        result = func(cur, start, keep)
        if result[0] == 0:
            print '�������ʣ������', result[1]
            start -= 1
        else:
            print '�������ʣ������', result[1]
            keep -= 1
    except Exception, e:
        print e

