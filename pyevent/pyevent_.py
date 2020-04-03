import Queue
import threading
import copy
import time

class EventManager(object):
    def __init__(self):

        self.__eventQueue = Queue.Queue()
        self.__active = False
        self.__thread = threading.Thread(target=self.__run)
        self.__thread.setDaemon(True)
        self.__handlers = {}

    def __run(self):
        while self.__active is True:
            try:
                event = self.__eventQueue.get(block=True, timeout=1)
                self.__eventProcess(event)
            except:
                time.sleep(0.001)

    def __eventProcess(self, event):
        if event.name in self.__handlers:
            for handler in self.__handlers[event.name]:
                handler(*event.para)

    def start(self):
        self.__active = True
        self.__thread.start()

    def stop(self):
        self.__active = False
        # self.__thread.join()

    def eventAddHandler(self, name, handler):
        try:
            handlerList = self.__handlers[name]
        except KeyError:
            handlerList = []

        self.__handlers[name] = handlerList
        if handler not in handlerList:
            handlerList.append(handler)

    def eventRemoveHandler(self, name, handler):
        try:
            handlerList = self.__handlers[name]
        except KeyError:
            pass

        self.__handlers[name] = handlerList
        if handler in handlerList:
            handlerList.remove(handler)

    def sendEvent(self, event):
        self.__eventQueue.put(event)

class Event(object):
    def __init__(self, manager, name, para=None):
        self.manager = manager
        self.name = name
        self.para = para

    def connectHandler(self,handler):
        self.manager.eventAddHandler(self.name,handler)

    def disconnectHandler(self,handler):
        self.manager.eventRemoveHandler(self.name,handler)

    def emit(self,para=None):
        self.para = para
        newEvent = self.NewEvent(self.name,self.para)
        self.manager.sendEvent(newEvent)

    class NewEvent(object):
        """docstring for NewEvent"""
        def __init__(self, name, para):
            self.name = name
            self.para = para
