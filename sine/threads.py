# coding=utf-8

import threading as _threading

class StoppableThread(_threading.Thread):
    """Thread class with a stop() method. 
    The thread process itself has to take a @parameter stop_event (provided by this class), 
    and check regularly by stop_event.is_set()."""

    def __init__(self, target, *args, **kwargs):
        self._stop_event = _threading.Event()
        def _call(*args, **kwargs):
            kwargs['stop_event'] = self._stop_event
            return target(*args, **kwargs)
        super(StoppableThread, self).__init__(target=_call, *args, **kwargs)
        return

    def stop(self):
        self._stop_event.set()
        if self.is_alive():
            self.join(2)
            if self.is_alive():
                print 'thread can not exit!'
        return

    def stopped(self):
        return self._stop_event.is_set()

class ReStartableThread(object):
    """docstring for ReStartableThread"""
    def __init__(self, target):
        super(ReStartableThread, self).__init__()
        self.target = target
        self.thread = None
        return

    def getThread(self):
        return self.thread

    def start(self):
        self.stop()
        self.thread = StoppableThread(self.target)
        self.thread.setDaemon(True)
        self.thread.start()
        return

    def stopped(self):
        return self.thread == None or self.thread.stopped()

    def stop(self):
        if not self.stopped():
            self.thread.stop()
        return
