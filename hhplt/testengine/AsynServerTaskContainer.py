#encoding:utf-8
'''
Created on 2014-12-15
异步服务任务容器
需要异步调用的服务端逻辑，通过此容器进行，不卡主主线程
@author: user
'''


import time
from threading import Thread,RLock,Event
from hhplt.testengine.server import ServerBusiness
from hhplt.testengine.exceptions import AbortTestException
from hhplt.testengine.testcase import uiLog
from PyQt4.QtCore import SIGNAL
from hhplt.parameters import GLOBAL
import winsound

abortReport = set() #需要停止的报告的productId列表

def errorBeep():
    '''异常的蜂鸣提示'''
    for i in range(3):
        winsound.Beep(3000 - i * 100, 100)


class AsynServerTaskContainer(Thread):
    
    def __init__(self):
        Thread.__init__(self)
        self.taskQueue = []
        self.lock = RLock()
        self.event = Event()
        
        
    def __submitTask(self,task):
        self.lock.acquire()
        self.taskQueue.insert(0, task)
        self.lock.release()
        self.event.set()
    
    def __popOneTask(self):
        self.lock.acquire()
        if len(self.taskQueue) == 0:
            task = None
        else:
            task = self.taskQueue.pop()
        self.lock.release()
        if task is None:
            self.event.clear()
            self.event.wait()
            return self.__popOneTask()
        else:
            return task
            
    def submitTask(self,idCode,procFun):
        '''提交一个异步任务'''
        class Task:
            def __call__(self):
                try:
                    procFun()
                except AbortTestException,e:
                    global abortReport
                    abortReport.add(idCode)
                    uiLog(e.message)
                    GLOBAL["mainWnd"].emit(SIGNAL("CRITICAL_MESSAGE(QString)"),e.message)
                    errorBeep()
        self.__submitTask(Task())
        
    def submitReportUpload(self,idCode,report):
        '''提交上报报告'''
        class Task:
            def __call__(self):
                global abortReport
                if idCode in abortReport:
                    abortReport.remove(idCode)
                    uiLog(u"产品:%s测试结果丢弃，测试失败"%idCode)
                else:
                    with ServerBusiness() as sb:
                        sb.uploadTestReport(report)
                        uiLog(u'产品%s测试结果已保存'%idCode)
        self.__submitTask(Task())
        
    def run(self):
        while True:
            try:
                time.sleep(0.1)
                task = self.__popOneTask()
                if task is not None:
                    task()
            except:
                pass
    
    
asynServerTaskContainer = AsynServerTaskContainer()
asynServerTaskContainer.start()




