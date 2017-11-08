
# coding: utf-8

# In[1]:


import sys
sys.path.append('D:\Users\Git\pylib')
from Tkinter import *
from sine.helpers import substitute
move = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


# In[2]:

# settings
button_width = 2
width = 10
height = 10
mines = 10
mine = '*'
pressed_color = '#FFFFFF'
mine_color = 'red'


# In[3]:

class MineMap:
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
                d[(x, y)] = {'stepped':False}
                d[(x, y)]['around'] = -1 if m[x*self.height-self.height+y-1] < self.mines else 0
        for x in range(1, self.width + 1):
            for y in range(1, self.height + 1):
                if (d[(x, y)]['around'] == -1):
                    for (x1, y1) in move:
                        x2 = x + x1
                        y2 = y + y1
                        if (x2 > 0 and x2 <= self.width and y2 > 0 and y2 <= self.height and d[(x2, y2)]['around'] >= 0):
                            d[(x2, y2)]['around'] += 1
        self.dict = d
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


# In[4]:

m = MineMap(width, height, mines)
stopped = False
def once(d, x, y):
    # 重复判断累赘？
    if (x < 1 or x > m.width):
        return
    if (y < 1 or y > m.height):
        return
    if m[(x, y)]['stepped']:
        return
    m[(x, y)]['stepped'] = True
    button = m[(x, y)]['button']
    button['state'] = DISABLED
    button['bg'] = pressed_color
    around = m[(x, y)]['around']
    d[(x, y)] = around
    if around == 0:
        for (x1, y1) in move:
            once(d, x + x1, y + y1)
    else:
        button['text'] = around
def press(x, y):
    global stopped
    if stopped:
        return {}
    print x, y
    n = m[(x, y)]['around']
    if n == -1:
        button = m[(x, y)]['button']
        button['state'] = DISABLED
        button['text'] = mine
        button['bg'] = mine_color
        stopped = True
        return {((x, y), -1)}
    d = {}
    once(d, x, y)
    return d
def generate(x, y):
    def func():
        press(x, y)
    return func


# In[5]:

root = Tk()
b = Button(root, text='R', width=button_width)
b.pack(side="top")
for x in range(1, width + 1):
    frm = Frame()
    for y in range(1, height + 1):
        b = Button(frm, text='', width=button_width, command=generate(x, y), bd=3)
        b.pack(side="top")
        m[(x, y)]['button'] = b
    frm.pack(side='left')
root.mainloop()


# In[ ]:



