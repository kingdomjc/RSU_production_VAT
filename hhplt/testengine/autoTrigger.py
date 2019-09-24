#encoding:utf-8
'''
Created on 2014-10-21
自动开合触发器引擎
@author: user
'''

from threading import Thread,Event
import time

from hhplt.parameters import GLOBAL,SESSION,PARAM
from PyQt4.QtCore import SIGNAL

class AbstractAutoTrigger(Thread):
    '''自动开合触发引擎线程'''
    def __init__(self):
        Thread.__init__(self)
        self.runnable = False
        self.lock = Event()
        self.shouldPause = False
    
    def pause(self):
        self.shouldPause = True
    
    def resume(self):
        self.shouldPause = False
        self.lock.set()
        self.lock.clear()
    
    def start(self):
        self.runnable = True
        Thread.start(self)
    
    def run(self):
        while(self.runnable):
            time.sleep(0.01)
            if self.shouldPause:
                self.lock.wait()
            try:
                if self.runnable and self._checkIfStart():
                    self.started = True
                    GLOBAL["mainWnd"].emit(SIGNAL("TRIGGER_START_TESTING()"))
                if self.runnable and self._checkIfStop():
                    self.started = False
                    GLOBAL["mainWnd"].emit(SIGNAL("TRIGGER_STOP_TESTING()"))
            except Exception,e:
                print e

    def close(self):
        '''关闭自动触发线程'''
        self.runnable = False

    def _checkIfStart(self):
        pass
    
    def _checkIfStop(self):
        pass


class EmptyTrigger():
    def start(self):
        pass
    def close(self):
        pass



    
class AutoStartStopTrigger(AbstractAutoTrigger):
    '''自动触发器'''
    def _checkIfStart(self):
        testingProduct = SESSION["testingProduct"] if "testingProduct" in SESSION else None
        return testingProduct is None
    
    def _checkIfStop(self):
        testingProduct = SESSION["testingProduct"] if "testingProduct" in SESSION else None
        if testingProduct is not None \
            and testingProduct.testResult:
            time.sleep(1)   #在结束界面停留一会儿，让工人有时间看看界面
            return True
        return False

class AutoTriggerOnSmoothFinish(AbstractAutoTrigger):
    '''不设开始结束的触发器，与AutoStartStopTrigger的区别在于，即使测试失败，也不停留在结束页'''
    def _checkIfStart(self):
        testingProduct = SESSION["testingProduct"] if "testingProduct" in SESSION else None
        return testingProduct is None
    
    def _checkIfStop(self):
        testingProduct = SESSION["testingProduct"] if "testingProduct" in SESSION else None
        if testingProduct is not None and testingProduct.finishSmoothly:
            time.sleep(2)   #在结束界面停留一会儿，让工人有时间看看界面
            return True
        return False    


    
class SerialCtsTrigger(AbstractAutoTrigger):
    '''通过串口的CTS脚判定夹具开合'''#当前未采用，如果采用，config.json中应该有triggerCom的值
    def __init__(self):
        import serial
        AbstractAutoTrigger.__init__(self)
        portName = PARAM["triggerCom"]
        self.serialPort = serial.Serial(portName)
        self.nowState = None    #当前状态
        
        #CTS脚，夹具合上为False，夹具打开为True
    
    def start(self):
        if not self.serialPort.isOpen():
            self.serialPort.open()
            self.nowState = self.serialPort.getCTS()
        AbstractAutoTrigger.start(self)
    
    def _checkIfStart(self):
        cts = self.serialPort.getCTS()
        if self.nowState != cts and cts == False:
            self.nowState = cts
            time.sleep(0.1)
            return True
        return False
    
    def _checkIfStop(self):
        cts = self.serialPort.getCTS()
        if self.nowState != cts and cts == True:
            self.nowState = cts
            time.sleep(0.1)
            return True
        return False    
    
    
    