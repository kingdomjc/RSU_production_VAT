#encoding:utf-8
"""

@author:zws
"""
from thread import start_new_thread
from threading import Thread

import time

from hhplt.deviceresource import TestResource, askForResource, TestResourceInitException
from hhplt.deviceresource.LonggangIOBoard import LonggangIOBoardDevice
from hhplt.parameters import PARAM
from hhplt.testengine.autoTrigger import AbstractAutoTrigger



#夹具动作异常时，抛出此
class ClapActionException(Exception):pass

class BoardIOController(TestResource):
    # 单板测试工位夹具动作控制板，单板/射频均从此类扩展
    STATE_TESTING = 1
    STATE_STOP = 2
    STATE_ERROR = 3

    def __init__(self,param):
        self.ioBoard = LonggangIOBoardDevice({"ioBoardCom":PARAM["ioBoardCom"],"impl":self})
        self.currentState = 0
        self.isBusy = False

    def initResource(self):
        self.ioBoard.initResource()
        try:
            self.stopTesting()
        except ClapActionException,e:
            raise TestResourceInitException(u"初始化夹具失败，请检查设置并重启软件")

    def waitFor(self,x,timeout = 3):
        for i in range(int(timeout/0.5)):
            if self.ioBoard[x]:return
            time.sleep(0.5)
        self.currentState = BoardFreqIOController.STATE_ERROR
        raise ClapActionException()

    def processInput(self):
        # 夹具自身动作
        try:
            if not self.isBusy:
                if self.ioBoard[self.X_START_BUTTON] :
                    start_new_thread(self.startTesting,())
                elif self.ioBoard[self.X_STOP_BUTTON]:
                    start_new_thread(self.stopTesting,())
        except Exception,e:
            import traceback
            print traceback.format_exc()

    def stopTesting(self):raise Exception("没有实现的IOController")
    def startTesting(self):raise Exception("没有实现的IOController")

class BoardDigitIOController(BoardIOController):
    Y_HPLAT = 1 #水平进出：1-推入，0-推出
    X_HPLAT_OUT = 4 #水平推出到位
    X_HPLAT_IN = 5 #水平推入到位

    Y_VCOVER = 0    #垂直下压：1-下压，0-上抬
    X_VCOVER_UP = 2 #上抬到位
    X_VCOVER_DOWN =  3  #下压到位

    Y_DEMOLISH_1 = 2 # 防拆 1-顶起，0-松下
    Y_DEMOLISH_2 = 3 #  1-顶起，0-松下
    Y_DEMOLISH_3 = 4 #  1-顶起，0-松下
    Y_DEMOLISH_4 = 5 #  1-顶起，0-松下
    Y_DEMOLISH_5 = 6 #  1-顶起，0-松下
    Y_DEMOLISH_6 = 7 #  1-顶起，0-松下

    Y_RESET_1 = 8   #复位，1-下压，0-弹起
    Y_RESET_2 = 9   #复位，1-下压，0-弹起
    Y_RESET_3 = 10   #复位，1-下压，0-弹起
    Y_RESET_4 = 11  #复位，1-下压，0-弹起
    Y_RESET_5 = 12   #复位，1-下压，0-弹起
    Y_RESET_6 = 13   #复位，1-下压，0-弹起

    X_START_BUTTON = 0
    X_STOP_BUTTON = 1

    def stopTesting(self):
        try:
            self.isBusy = True
            for i in (self.Y_DEMOLISH_1,self.Y_DEMOLISH_2,self.Y_DEMOLISH_3,self.Y_DEMOLISH_4,self.Y_DEMOLISH_5,self.Y_DEMOLISH_6):
                self.ioBoard[i] = False

            self.ioBoard[self.Y_VCOVER] = False
            self.waitFor(self.X_VCOVER_UP)
            self.ioBoard[self.Y_HPLAT] = False
            self.waitFor(self.X_HPLAT_OUT)
            self.currentState = BoardFreqIOController.STATE_STOP
        finally:
            self.isBusy = False

    def startTesting(self):
        try:
            self.isBusy = True
            self.ioBoard[self.Y_HPLAT] = True
            self.waitFor(self.X_HPLAT_IN)
            self.ioBoard[self.Y_VCOVER] = True
            self.waitFor(self.X_VCOVER_DOWN)
            self.currentState = BoardFreqIOController.STATE_TESTING
        finally:
            self.isBusy = False

    def ctrlDemolish(self,slot,value):
        # 控制防拆键，slot为卡槽号，value为TRUE表示顶上，FALSE表示松开
        self.ioBoard[
            {"1":self.Y_DEMOLISH_1,"2":self.Y_DEMOLISH_2,"3":self.Y_DEMOLISH_3,
             "4":self.Y_DEMOLISH_4,"5":self.Y_DEMOLISH_5,"6":self.Y_DEMOLISH_6}[slot]
        ] = value

    def triggerResetButton(self,slot):
        # 触发复位按键，下压弹起
        p = {"1":self.Y_RESET_1,"2":self.Y_RESET_2,"3":self.Y_RESET_3,
             "4":self.Y_RESET_4,"5":self.Y_RESET_5,"6":self.Y_RESET_6}[slot]
        self.ioBoard[p] = True
        self.ioBoard[p] = False

class BoardFreqIOController(BoardIOController):
    # 射频单板夹具动作控制板驱动
    Y_HPPLAT = 2 #水平板控制，0-推入，1-推出
    X_HPLAT_IN  = 2 #水平推入到位
    X_HPLAT_OUT = 3 #水平推出到位

    Y_INNER_COVER = 3  #里盖控制，0-上拉，1-下压
    X_INNER_COVER_UP = 4    #里盖上到位
    X_INNER_COVER_DOWN = 5  #里盖下到位

    Y_OUTER_COVER_FIXED = 1 #外盖控制，常1
    Y_OUTER_COVER = 0   #w外盖控制，0-抬起，1-下压
    X_OUTER_COVER_UP = 7    #外盖上到位
    X_OUTER_COVER_DOWN = 1  #外盖下到位

    X_START_BUTTON = 0  #开始按钮
    X_STOP_BUTTON = 6   #结束按钮

    def initResource(self):
        self.ioBoard.initResource()
        self.ioBoard[self.Y_OUTER_COVER_FIXED] = True
        try:
            self.stopTesting()
        except ClapActionException,e:
            raise TestResourceInitException(u"初始化夹具失败，请检查设置并重启软件")

    def startTesting(self):
        # 开始测试：平板水平推入，水平内到位后内盖下压，外盖下压，两个盖下到位后，开始测试
        try:
            self.isBusy = True
            self.ioBoard[self.Y_HPPLAT] = False
            self.waitFor(self.X_HPLAT_IN)
            self.ioBoard[self.Y_INNER_COVER] = True
            self.waitFor(self.X_INNER_COVER_DOWN)
            self.ioBoard[self.Y_OUTER_COVER] = True
            self.waitFor(self.X_OUTER_COVER_DOWN)
            self.currentState = BoardFreqIOController.STATE_TESTING
        finally:
            self.isBusy = False

    def stopTesting(self):
        # 结束测试：外盖上抬，外盖上到位后内盖上台，内盖上到位后，水平推出，水平推出到位后结束测试
        try:
            self.isBusy = True
            self.ioBoard[self.Y_OUTER_COVER] = False
            self.waitFor(self.X_OUTER_COVER_UP)
            self.ioBoard[self.Y_INNER_COVER] = False
            self.waitFor(self.X_INNER_COVER_UP)
            self.ioBoard[self.Y_HPPLAT] = True
            self.waitFor(self.X_HPLAT_OUT)
            self.currentState = BoardFreqIOController.STATE_STOP
        finally:
            self.isBusy = False



class BoardIOControllerAutoTrigger(AbstractAutoTrigger):
    # 自动触发器
    def _checkIfStart(self):
        return self.iodevice.currentState == BoardIOController.STATE_TESTING

    def _checkIfStop(self):
        return False


class BoardFreqIOControllerAutoTrigger(BoardIOControllerAutoTrigger):
    # 射频工位治具自动触发器
    def __init__(self):
        AbstractAutoTrigger.__init__(self)
        self.iodevice = askForResource("BoardFreqIOController", BoardFreqIOController)    #启动IO板卡


class BoardDigitIOControllerAutoTrigger(BoardIOControllerAutoTrigger):
    # 数字工位治具自动触发器
    def __init__(self):
        AbstractAutoTrigger.__init__(self)
        self.iodevice = askForResource("BoardDigitIOController", BoardDigitIOController)    #启动IO板卡



