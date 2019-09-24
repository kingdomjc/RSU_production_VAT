#encoding:utf-8
'''
Created on 2015-9-2
GS11 工装IO板

@author: user
'''

from hhplt.deviceresource import TestResource,TestResourceInitException,askForResource
from hhplt.deviceresource import AbortTestException
from hhplt.testengine.autoTrigger import AbstractAutoTrigger
from hhplt.parameters import GLOBAL,SESSION,PARAM
import time
from PyQt4.QtCore import SIGNAL
from LonggangIOBoard import LonggangIOBoardDevice
import thread
from hhplt.testengine.manul import showAsynMessage

#输出口连接端子线序
OUTER_COVER_OUTPUT = 0  #外罩开关，True为合上，False为抬起
CARD_INJECT_RESET_OUTPUT = 1    #插卡复位（脉冲）
DEMOLISH_BUTTON_OUTPUT = 2 #防拆
INNER_PLATEN_OUTPUT = 3 #内部压板（上下）,True为下压，False为上抬
INNER_DRAWER_OUTPUT = 4 #内部进出仓（水平）True为外弹，False是进仓
LIGHTING_OUTPUT = 6 #补光灯
#以下5个口用于切换NULINK和普通串口
UART_TX_OUTPUT = 8
UART_RX_OUTPUT = 9
SWD_DATA_OUTPUT = 10
SWD_CLK_OUTPUT = 11
SWD_RST_OUTPUT = 12


#输入口连接端子线序
START_BUTTON_INPUT = 0   #两个开始键
BEEP_SENSER_INPUT = 2   #蜂鸣器检测
INNER_PLATEN_TOP_INPLACE = 3    #内压板（垂直）上到位
INNER_PLATEN_BOTTOM_INPLACE = 4 #内压板（垂直）下到位
INNER_DRAWER_INNER_INPLACE = 5   #内仓（水平）进仓到位
INNER_DRAWER_OUT_INPLACE = 6    #内仓（水平）出仓到位
LED_LIGHT_SENSER = 7    #光传感器（板上灯亮表示没光，板上灯暗表示有光）
OUTER_COVER_BOTTOM_INPLACE = 9  #外罩下到位
OUTER_COVER_TOP_INPLACE = 10    #外罩上到位
CLAMP_WORKING_STATE = 11    #夹具使能状态，正常情况该脚不导通

class GS11IOBoardDevice(TestResource):
    '''开关量IO板设备'''
    def __init__(self,initParam):
        self.ioBoard =  LonggangIOBoardDevice({"ioBoardCom": PARAM["ioBoardCom"],"impl":self})
        self.buttonTriggerStartTime = 0 #按钮触发开始时间，在时间窗口内，不再响应
        self.clampState = False
            
    def initResource(self):
        self.ioBoard.initResource()
        try:
            self.openClap()
        except Exception,e:
            raise TestResourceInitException(e.message)
    
    def retrive(self):
        self.ioBoard.retrive()

    def processInput(self):
        '''处理输入'''
        now = time.time()
        if now - self.buttonTriggerStartTime > 1 and self.__checkStartStopButton():
            self.buttonTriggerStartTime = now
            if self.ioBoard.inputResult[CLAMP_WORKING_STATE] == False:
                #夹具整体不开通，界面提示之
                showAsynMessage(u"错误",u"夹具罩已失效，请合上开关")
            
    def checkClampState(self):
        '''夹具状态，返回True表示夹具合上就位，可以开始测试，返回False表示夹具打开就位，可以上下料'''
        return self.clampState

    def __checkStartStopButton(self):
        '''检查夹具开始按键按下的动作，按下后，触发夹具合上；结束按键按下，触发夹具弹开'''
        if self.ioBoard.inputResult[START_BUTTON_INPUT] == False:
            thread.start_new_thread(self.closeClap,())
        elif self.ioBoard.inputResult[CLAMP_WORKING_STATE] == False:
            thread.start_new_thread(self.openClap,())
        return False
    
    def __waitForInputState(self,address,assertState = False,timeout=10):
        '''等待输入状态，超时未到输入状态，则抛出异常'''
        timeCount = 0.0
        time.sleep(0.3)
        while self.ioBoard.inputResult[address] != assertState:
            time.sleep(0.3)
            timeCount += 0.3
            if timeCount > timeout:
                showAsynMessage(u"错误",u"夹具动作错误，请检查设备连接")
                raise Exception(u"夹具动作错误，请检查设备连接")
        time.sleep(0.2)
        
    def closeClap(self):
        '''夹具合上逻辑'''
        #先检查一下，如果夹具已经合上，就别折腾了
        if self.ioBoard.inputResult[OUTER_COVER_BOTTOM_INPLACE] == False:return
        self.openLighting()
        self.ioBoard.outputSinglePort(INNER_DRAWER_OUTPUT,False)
        self.__waitForInputState(INNER_DRAWER_INNER_INPLACE)
        #水平托盘到位后，延时0.5秒，以确保到位
        time.sleep(0.5)
        self.ioBoard.outputMultiPort([INNER_PLATEN_OUTPUT,OUTER_COVER_OUTPUT],True)
        self.__waitForInputState(INNER_PLATEN_BOTTOM_INPLACE)
        self.__waitForInputState(OUTER_COVER_BOTTOM_INPLACE)
        self.clampState = True
        
    def openClap(self):
        '''夹具打开逻辑'''
        self.ioBoard.outputMultiPort([INNER_PLATEN_OUTPUT,OUTER_COVER_OUTPUT],False)
        self.__waitForInputState(INNER_PLATEN_TOP_INPLACE)
        self.__waitForInputState(OUTER_COVER_TOP_INPLACE)
        self.ioBoard.outputSinglePort(INNER_DRAWER_OUTPUT,True)
        self.__waitForInputState(INNER_DRAWER_INNER_INPLACE,True)   #只要有出来的意思就行
        self.clampState = False

    def pressDemolishButton(self):
        '''按下防拆按钮-下电了'''
        self.ioBoard.outputSinglePort(DEMOLISH_BUTTON_OUTPUT,False)
        
    def releaseDemolishButton(self):
        '''释放防拆按钮-正常上电了'''
        self.ioBoard.outputSinglePort(DEMOLISH_BUTTON_OUTPUT,True)

    def triggerResetButton(self):
        '''触发复位键'''
        self.ioBoard.triggerInPulse(CARD_INJECT_RESET_OUTPUT)

    def openLighting(self):
        '''打开补光灯'''
        self.ioBoard.outputSinglePort(LIGHTING_OUTPUT,True)
        
    def closeLighting(self):
        '''关闭补光灯'''
        self.ioBoard.outputSinglePort(LIGHTING_OUTPUT,False)
        
    def checkBeepState(self):
        '''检查蜂鸣器状态'''
        return self.ioBoard.inputResult[BEEP_SENSER_INPUT] == False
        
    def checkLedLightState(self):
        '''检查LED红绿灯光状态'''
        return self.ioBoard.inputResult[LED_LIGHT_SENSER] == True
    
    def switchToNuLink(self):
        '''切换至NuLink模式'''
        self.ioBoard.outputMultiPort([UART_TX_OUTPUT,UART_RX_OUTPUT,SWD_DATA_OUTPUT,SWD_CLK_OUTPUT,SWD_RST_OUTPUT], True)
        time.sleep(1)
    
    def switchToNormalSerial(self):
        '''切换至普通串口模式'''
        self.ioBoard.outputMultiPort([UART_TX_OUTPUT,UART_RX_OUTPUT,SWD_DATA_OUTPUT,SWD_CLK_OUTPUT,SWD_RST_OUTPUT], False)
        time.sleep(1)
        
    def output(self,address,output):
        '''普通输出'''
        self.ioBoard.outputSinglePort(address, output)
        
class IOBoardAutoTrigger(AbstractAutoTrigger):
    '''开关量板触发的夹具开合信号'''
    def __init__(self):
        AbstractAutoTrigger.__init__(self)
        self.board = askForResource("GS11IOBoardDevice", GS11IOBoardDevice)    #启动IO板卡
    
    def _checkIfStart(self):
        return self.board.checkClampState() == True 
    
    def _checkIfStop(self):
        if self.board.checkClampState() == False :
            time.sleep(1)
            return True
        return False
    
    
    
    
    
