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
from hhplt.testengine.manul import showDashboardMessage
import time


class CheckerIOController(TestResource):
    "检卡器治具IO控制器"
    Y_TEST_OK = 0
    Y_TEST_NG = 1
    Y_TEST_READY = 2
    
    X_START_TEST = 0
    X_MACHINE_ERROR = 1
    X_COLLECTION_FULL = 2
    X_NG_FULL = 3
    X_FEED_EMPTY = 4
    
    def __init__(self,param):
        self.ioBoard =  Longgang8I8OBoardDevice({"ioBoardCom": PARAM["ioBoardCom"]})
    
    def initResource(self):
        self.ioBoard.initResource()
        self.notifyReady()
    
    def isMachineError(self):
        if self.ioBoard[CheckerIOController.X_MACHINE_ERROR]:
            showDashboardMessage(u"<font color=red>治具机构异常</font>")
            return True
        elif self.ioBoard[CheckerIOController.X_COLLECTION_FULL]:
            showDashboardMessage(u"<font color=red>收料仓满杯</font>")
            return True
        elif self.ioBoard[CheckerIOController.X_NG_FULL]:
            showDashboardMessage(u"<font color=red>NG料仓满杯</font>")
            return True
        elif self.ioBoard[CheckerIOController.X_FEED_EMPTY]:
            showDashboardMessage(u"<font color=red>送料仓空杯</font>")
            return True
        showDashboardMessage(u"<font color=green>正常测试</font>")
        return False
    
    def shouldStartTest(self):
        return self.ioBoard[CheckerIOController.X_START_TEST]

    def notifyTestSuiteError(self):
        self.ioBoard[CheckerIOController.Y_TEST_READY] = False
        self.ioBoard[CheckerIOController.Y_TEST_OK] = False
        self.ioBoard[CheckerIOController.Y_TEST_NG] = False

    def notifyReady(self):
        self.ioBoard[CheckerIOController.Y_TEST_READY] = True
        self.ioBoard[CheckerIOController.Y_TEST_OK] = False
        self.ioBoard[CheckerIOController.Y_TEST_NG] = False
    
    def notifyTestOK(self):
        self.ioBoard[CheckerIOController.Y_TEST_OK] = True

    def notifyTestNG(self):
        self.ioBoard[CheckerIOController.Y_TEST_NG] = True

    
    
class CheckerAutoTrigger(AbstractAutoTrigger):
    def __init__(self):
        AbstractAutoTrigger.__init__(self)
        self.board = askForResource("CheckerIOController", CheckerIOController)    #启动IO板卡
    
    def _checkIfStart(self):
        return (not self.board.isMachineError()) and self.board.shouldStartTest()
    
    def _checkIfStop(self):
        return self.board.isMachineError() or self.board.shouldStartTest()
    
    
    
    
    
    
    
    
    
    
    
    
    
    