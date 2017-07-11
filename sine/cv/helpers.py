# coding=utf-8

import cv2 as __cv2
import numpy as __np
from sine.decorator import acceptMultiIterable as __acceptMultiIterable

@__acceptMultiIterable(__np.ndarray, {'index':'postfix'})
def show(img, title='img', **kwargs):
    '''
    opencv show image
    '''
    title += str(kwargs.get('postfix', ''))
    __cv2.imshow(title, img)
    __cv2.waitKey(0)
    __cv2.destroyWindow(title)

def readAsShape(path, shape):
    img = __cv2.imread(path)
    gray = __cv2.cvtColor(img, __cv2.COLOR_BGR2GRAY)
    eight = __cv2.resize(gray, shape)
    return eight.astype(__np.int16)

def read_csv_with_label(path):
    import pandas as pd
    import numpy as __np
    df = pd.read_csv(path)
    return __np.int16(df.ix[:,:1].values.flatten()), __np.int16(df.ix[:,1:].values)
