#encoding:utf-8
'''
Created on 2016-11-8
检卡治具IO控制器
@author: zws
'''


from hhplt.deviceresource import TestResource,TestResourceInitException,askForResource
from hhplt.deviceresource.LongGang88IODevice import Longgang8I8OBoardDevice
from hhplt.parameters import GLOBAL,SESSION,PARAM
from hhplt.testengine.autoTrigger import AbstractAutoTrigger
from threading import Thread
import time

X_START_BUTTON = 0
X_STOP_BUTTON = 1
Y_PLATEN = 0
Y_LIGHT = {"1":1,"2":2,"3":3,"4":4,"5":5,"6":6}

class VersionDownloadIOController(TestResource,Thread):
    "GS11自动线批量版本下载治具IO控制器"
    def __init__(self,param):
        self.ioBoard =  Longgang8I8OBoardDevice({"ioBoardCom": PARAM["ioBoardCom"]})
        Thread.__init__(self)
    
    def initResource(self):
        self.ioBoard.initResource()
        self.start()
    
    def closeClap(self):
        '''夹具合上逻辑'''
        self.ioBoard[Y_PLATEN] = True
    
    def openClap(self):
        '''夹具打开逻辑'''
        self.ioBoard[Y_PLATEN] = False
    
    def clearAllLight(self):
        "关闭所有的指示灯"
        for lt in Y_LIGHT.values():
            self.ioBoard[lt] = False
    
    def showLight(self,slot):
        "点亮指示灯，入参是槽位号(str类型的)"
        self.ioBoard[Y_LIGHT[slot]] = True
    
    def run(self):
        #用于控制夹具自己的动作
        while True:
            time.sleep(1)
            try:
                #检查按下停止按钮
                if not self.ioBoard[X_STOP_BUTTON]:
                    self.openClap()
            except Exception,e:
                print e
            
class VersionDownloadIOControllerAutoTrigger(AbstractAutoTrigger):
    "版本下载治具自动触发器"
    def __init__(self):
        AbstractAutoTrigger.__init__(self)
        self.iodevice = askForResource("VersionDownloadIOController", VersionDownloadIOController)    #启动IO板卡
    
    def _checkIfStart(self):
        return self.iodevice.ioBoard[X_START_BUTTON]
    
    def _checkIfStop(self):
        return self.iodevice.ioBoard[X_START_BUTTON]
    
    
    
    
    
    
    
    
    