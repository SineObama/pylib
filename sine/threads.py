# coding=utf-8
'''自定义线程对象，方便停止线程和重复启动。'''

import threading as _threading
import inspect as _inspect

class StoppableThread(_threading.Thread):
    """Thread like threading.Thread with a stop() method.
    A threading.Event will be a attribute and passed to the target function via @parameter kwargs, with default name 'stop_event'.
    The thread itself has to check the event regularly by i.e. stop_event.is_set()."""

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None, event_name='stop_event'):
        '''keep the same as threading.Thread.__init__'''
        if target != None:
            spec = _inspect.getargspec(target)
            if spec.keywords == None:
                for i in spec.args:
                    if i == event_name:
                        break
                else:
                    raise ValueError('target function has neight **kwargs or argument \'' + event_name + '\'')
        self._stop_event = _threading.Event()
        self.__setattr__(event_name, self._stop_event)
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
        '''若线程存活或未设置停止（未更新线程对象），停止并重新初始化。'''
        if self._thread.is_alive() or not self._thread.stopped():
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
