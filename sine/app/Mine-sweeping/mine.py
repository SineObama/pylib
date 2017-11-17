
# coding: utf-8

# In[ ]:


import sys
sys.path.append('D:\Users\Git\pylib')
from Tkinter import *
from sine.helpers import substitute
move = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


# In[ ]:

# settings
button_width = 2
width = 10
height = 10
mines = 10
ch = {'mine':'*', 'flag':'F', 'unknown':'?', 'restart':'R', 'win':'O'}
enable_unknown = True
color = {'explored':'#FFFFFF', 'mine':'red'}


# In[ ]:

class MineMap:
    '''
    properties:
    explored: 
    around: number of mines in 8 block surround, -1 for this block is mine
    state: 0 normal, 1 mark, 2 unknown (as classical)
    '''
    def __init__(self, width=10, height=10, mines=10):
        '''
        @param mines will be adjust that at lease 1 place is not mine
        '''
        self.width = width
        self.height = height
        if mines >= width * height:
            mines = width * height - 1
        self.mines = mines
        self.started = False
        return
    def __start(self, (x0, y0)):
        m = range(self.width * self.height)
        substitute(m)
        while (m[x0*self.height-self.height+y0-1]<self.mines):
            substitute(m)
        d = {}
        for x in range(1, self.width + 1):
            for y in range(1, self.height + 1):
                d[(x, y)] = {'explored':False}
                d[(x, y)]['around'] = -1 if m[x*self.height-self.height+y-1] < self.mines else 0
                d[(x, y)]['state'] = 0
        for x in range(1, self.width + 1):
            for y in range(1, self.height + 1):
                if (d[(x, y)]['around'] == -1):
                    for (x1, y1) in move:
                        x2 = x + x1
                        y2 = y + y1
                        if (x2 > 0 and x2 <= self.width and y2 > 0 and y2 <= self.height and d[(x2, y2)]['around'] >= 0):
                            d[(x2, y2)]['around'] += 1
        self.dict = d
        return
    def __getitem__(self, (x, y)):
        '''
        x ~ [1, width]
        y ~ [1, height]
        return the #mine around, or -1 if this is mine
        '''
        if (x < 1 or x > self.width):
            return
        if (y < 1 or y > self.height):
            return
        if (not self.started):
            self.__start((x, y))
            self.started = True
        return self.dict[(x, y)]
    def show(self, mine='.', blank=' '):
        for y in range(1, self.height + 1):
            s = ''
            for x in range(1, self.width + 1):
                if self.dict[(x, y)]['around'] == -1:
                    s += mine
                else:
                    around = self.dict[(x, y)]['around']
                    s += str(around) if around > 0 else blank
            print s
        return


# In[ ]:

m = MineMap(width, height, mines)
unexlpores = width * height - mines
stopped = False

def stop():
    global stopped
    stopped = True
    return

def win():
    restart['text'] = ch['win']
    return

def runing(f):
    '''
    decorator: 必须在游戏运行时（未结束）
    '''
    global stopped
    def func(*args, **kwargs):
        if not stopped:
            f(*args, **kwargs)
    return func

def explore(d, x, y):
    # 重复判断累赘？
    if (x < 1 or x > m.width):
        return
    if (y < 1 or y > m.height):
        return
    if m[(x, y)]['explored'] or m[(x, y)]['state'] == 1: # never explore flag
        return
    m[(x, y)]['explored'] = True
    m[(x, y)]['state'] = 0
    button = m[(x, y)]['button']
    button['state'] = DISABLED
    button['bg'] = color['explored']
    around = m[(x, y)]['around']
    d[(x, y)] = around
    global unexlpores
    unexlpores -= 1
    if around == 0:
        button['text'] = ''
        for (x1, y1) in move:
            explore(d, x + x1, y + y1)
    else:
        button['text'] = around
    return

@runing
def onLeftClick(x, y):
    if m[(x, y)]['explored'] or m[(x, y)]['state'] == 1:
        return
    print 'left', x, y
    n = m[(x, y)]['around']
    if n == -1:
        button = m[(x, y)]['button']
        button['state'] = DISABLED
        button['text'] = ch['mine']
        button['bg'] = color['mine']
        stop()
        return {((x, y), -1)}
    d = {}
    explore(d, x, y)
    if unexlpores <= 0:
        win()
    return d

@runing
def onRightClick(x, y):
    if m[(x, y)]['explored']:
        return
    print 'right', x, y
    block = m[(x, y)]
    block['state'] = (block['state'] + 1) % (3 if enable_unknown else 2)
    if block['state'] == 0:
        block['button']['text'] = ''
    elif block['state'] == 1:
        block['button']['text'] = ch['flag']
    else:
        block['button']['text'] = ch['unknown']
    return

def generate(f, *args):
    def func(*unused, **unused2):
        f(*args)
    return func


# In[ ]:

root = Tk()
restart = Button(root, text=ch['restart'], width=button_width)
restart.pack(side="top")
for x in range(1, width + 1):
    frm = Frame()
    for y in range(1, height + 1):
        b = Button(frm, text='', width=button_width, command=generate(onLeftClick, x, y), bd=3)
        b.pack(side="top")
        b.bind('<Button-3>', generate(onRightClick, x, y))
        m[(x, y)]['button'] = b
    frm.pack(side='left')
root.mainloop()


# In[ ]:



