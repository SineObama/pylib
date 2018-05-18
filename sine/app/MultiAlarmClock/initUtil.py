# coding=utf-8
'''
用于初始化异常时的输出和程序暂停。
'''

_warning = False # 显示警告，等待回车继续（清屏）

def warn(*args):
    '''输入，并标记有警告'''
    global _warning
    s = ''
    if len(args) > 0:
        s = args[0]
        for i in args[1:]:
            s += ' ' + str(i)
    print s
    _warning = True

def warning_pause():
    '''有警告时暂定，等待任意输入'''
    if _warning:
        print '\npress enter to continue'
        raw_input()
