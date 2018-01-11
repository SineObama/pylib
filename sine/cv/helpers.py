# coding=utf-8

import cv2 as _cv2
import numpy as _np
from sine.decorator import acceptMultiIterable as _acceptMultiIterable

@_acceptMultiIterable(_np.ndarray, {'index':'index'})
def show(img, winname='img', flags=_cv2.cv.CV_WINDOW_AUTOSIZE, x=100, y=100, mouseCallback=None, **kwargs):
    '''
    opencv image show

    @Parameter winname window's name
    @Parameter flags windows type, usually cv2.cv.CV_WINDOW_...
    @Parameter x/y windows position
    @Parameter mouseCallback call back function by mouse

    @Return key from waitKey()
    '''
    if img == None:
        print 'img is None'
        return
    if img.shape[0] == 0 or img.shape[1] == 0:
        print 'img.shape illegal'
        return

    index = kwargs.get('index', '')
    if len(index) > 0:
        winname += str(index)
    key = -1
    try:
        _cv2.namedWindow(winname, flags)
        _cv2.moveWindow(winname, x, y)
        _cv2.imshow(winname, img)
        if mouseCallback != None:
            _cv2.setMouseCallback(winname, mouseCallback)
        key = _cv2.waitKey(0)
    except Exception, e:
        print repr(e)
    _cv2.destroyWindow(winname)
    return key

def readAsShape(path, shape):
    img = _cv2.imread(path)
    gray = _cv2.cvtColor(img, _cv2.COLOR_BGR2GRAY)
    eight = _cv2.resize(gray, shape)
    return eight.astype(_np.int16)

def read_csv_with_label(path):
    import pandas as pd
    df = pd.read_csv(path)
    return _np.int16(df.ix[:,:1].values.flatten()), _np.int16(df.ix[:,1:].values)

def selectRegion(img):
    '''
    use left mouse button to select
    down the button for point 1
    up the button for point 2
    the region is the rectangle decided by the 2 points
    '''
    x1=[0];y1=[0];x2=[0];y2=[0]
    def mouseCallback(event, x, y, flags, *args):
        if (event == _cv2.EVENT_LBUTTONDOWN):
            print 'point1:', x, y
            x2[0] = x; y2[0] = y
        if (event == _cv2.EVENT_LBUTTONUP):
            print 'point2:', x, y
            x1[0] = x; y1[0] = y
            _cv2.destroyWindow('select')
    show(img, 'select', mouseCallback=mouseCallback)
    if (x2[0] < x1[0]):
        temp = x2[0]
        x2[0] = x1[0]
        x1[0] = temp
    if (y2[0] < y1[0]):
        temp = y2[0]
        y2[0] = y1[0]
        y1[0] = temp
    roiImg = img[y1[0]:y2[0],x1[0]:x2[0]]
    return roiImg
