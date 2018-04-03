# coding=utf-8
'''自定义线程对象，方便停止线程和重复启动。'''

import threading as _threading

class StoppableThread(_threading.Thread):
    """Thread class with a stop() method. 
    The thread process itself has to take a parameter of type threading.Event (default name is 'stop_event', can be specified), 
    and check regularly by stop_event.is_set() to stop itself.
    The event object will be added to @parameter kwargs."""

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None, event_name='stop_event'):
        '''keep the same as threading.Thread.__init__'''
        self._stop_event = _threading.Event()
        if kwargs == None:
            kwargs = {}
        kwargs[event_name] = self._stop_event
        super(StoppableThread, self).__init__(group, target, name, args, kwargs, verbose)
        return

    def stop(self):
        '''set the event.'''
        self._stop_event.set()
        return

    def stopped(self):
        '''whether the event is set'''
        return self._stop_event.is_set()

class ReStartableThread(object):
    """方便同一个函数多次作为线程启动。参数同StoppableThread。
    默认为守护线程。停止后会重新初始化，需要重新设置属性。"""
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._thread = StoppableThread(*self._args, **self._kwargs)
        self._thread.setDaemon(True)
        return

    def start(self):
        '''若线程存活或已停止，停止并重新初始化。'''
        if self._thread.is_alive() or self._thread.stopped():
            self.stop()
        self._thread.start()
        return

    def stop(self):
        '''停止线程并重新初始化（创建新对象）。'''
        if not self._thread.stopped():
            self._thread.stop()
        self._thread = StoppableThread(*self._args, **self._kwargs)
        self._thread.setDaemon(True)
        return

    def __getattr__(self, name):
        return self._thread.__getattribute__(name)
