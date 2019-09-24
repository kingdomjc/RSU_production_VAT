#encoding:utf-8
'''
Created on 2014-11-13
GS10工装测试开关量IO板
工控板采用的具体型号由参数控制
@author: user
'''
from hhplt.deviceresource import TestResource,TestResourceInitException,askForResource
from hhplt.testengine.autoTrigger import AbstractAutoTrigger
from hhplt.parameters import GLOBAL,SESSION,PARAM
import time
from PyQt4.QtCore import SIGNAL
from XinyuIOBoard import XinyuIOBoardDevice
from LonggangIOBoard import LonggangIOBoardDevice
import thread

START_STOP_TRIGGER_INPUT = 1    #夹具开合(最终状态)输入X-1
NORMAL_BUTTON_INPUT = 2 #正常确认输入口X-2
ABNORMAL_BUTTON_INPUT = 3   #异常确认输入口X-3
START_BUTTON_INPUT = 4  #夹具合上按钮按下输入 X-4
STOP_BUTTON_INPUT = 5   #夹具打开按钮按下输入X-5
BEEP_SENSER = 7 #蜂鸣器检查
LED_LIGHT_SENSER = 8    #红绿LED灯亮起检测
LCD_SCREEN_SENSER = 9    #LCD屏幕全白检测
CLAP_CLOSE_NEXT_STEP_OK = 10  #夹具合上的第2个步骤就位状态 X10（对重庆线单板测试，是两级开合，首先水平就位，再垂直下压
CLAP_OPEN_FIRST_STEP_OK = 11    #夹具打开的第一个步骤就位X11（垂直打开到位）

RESULT_BUTTON_OUTPUT = 1#正面复位按键   Y-1
DEMOLISH_BUTTON_OUTPUT = 2#背面防拆按键    Y-2
DISPLAY_CONVERT_BUTTON_OUTPUT = 3#屏幕倒置按键    Y-3
CLAMP_OPEN_CLOSE_OUTPUT = 4 #夹具开合，合上的第一个动作（打开时反过来）  Y-4
FINISH_WITH_SUCCESS_OUTPUT = 5   #测试正常通过此输出信号，Y-5
FINISH_WITH_FAIL_OUTPUT = 6 #测试异常通过此输出信号，Y-6

SENSI_SWITCH_OUTPUT = 7#灵敏度拨动开关   Y-7
CLAP_CLOSE_FINAL_STEP_OUTPUT = 8    #夹具合上的最终动作输出    Y-8

SOUND_LIGHT_DETECT = 9#声光检测装置   Y-9    不用

class GS10IOBoardDevice(TestResource):
    '''开关量IO板设备'''
    def __init__(self,initParam):
        if PARAM["ioBoardType"] == "xinyu":
            self.ioBoard =  XinyuIOBoardDevice({"ioBoardCom": PARAM["ioBoardCom"],"impl":self})
        elif PARAM["ioBoardType"] == "longgang":
            self.ioBoard =  LonggangIOBoardDevice({"ioBoardCom": PARAM["ioBoardCom"],"impl":self})
            
        self.buttonTriggerStartTime = 0 #按钮触发开始时间，在时间窗口内，不再响应
            
    def initResource(self):
        self.ioBoard.initResource()
    
    def retrive(self):
        self.ioBoard.retrive()

    def processInput(self):
        '''处理输入'''
        now = time.time()
        if now - self.buttonTriggerStartTime > 1 and \
            (self.__checkInputTrigger() or self.__checkStartStopButton()):
            self.buttonTriggerStartTime = now
    
    def __checkStartStopButton(self):
        '''检查夹具开始按键按下的动作，按下后，触发夹具合上；结束按键按下，触发夹具弹开'''
        if self.ioBoard.inputResult[START_BUTTON_INPUT] == False:
            thread.start_new_thread(self.closeClap,())
            return True
        elif self.ioBoard.inputResult[STOP_BUTTON_INPUT] == False:
            thread.start_new_thread(self.openClap,())
            return True
        return False
        #以下是原来的逻辑，感觉用不着这样，就去掉了
#        if self.ioBoard.inputResult[START_BUTTON_INPUT] == False and self.ioBoard.inputResult[START_STOP_TRIGGER_INPUT] == True:
#            self.closeClap()
#        elif self.ioBoard.inputResult[STOP_BUTTON_INPUT] == False and self.ioBoard.inputResult[START_STOP_TRIGGER_INPUT] == False:
#            self.openClap()
    
    def __checkInputTrigger(self):
        '''检查输入触发情况'''
        if self.ioBoard.inputResult[NORMAL_BUTTON_INPUT] == False:
            GLOBAL["mainWnd"].emit(SIGNAL("MANUL_CHECK_TRIGGER(QString)"),"NORMAL")
            return True
        if self.ioBoard.inputResult[ABNORMAL_BUTTON_INPUT] == False:
            GLOBAL["mainWnd"].emit(SIGNAL("MANUL_CHECK_TRIGGER(QString)"),"ABNORMAL")
            return True
        return False
    
    def checkClampState(self):
        '''检查夹具开合输入信号，夹具合上为False，夹具打开为True，初始True'''
        return self.ioBoard.inputResult[START_STOP_TRIGGER_INPUT]
    
    def checkLedLightState(self):
        '''检查LED灯是否亮起，如果亮起，返回True'''
        return self.ioBoard.inputResult[LED_LIGHT_SENSER] == False
    
    def checkLcdScreenState(self):
        '''检查LCD屏幕是否全白，如果亮起，返回True'''
        return self.ioBoard.inputResult[LCD_SCREEN_SENSER] == False
    
    def checkBeepState(self):
        '''检查蜂鸣器是否响起，如果响起，返回True'''
        return self.ioBoard.inputResult[BEEP_SENSER] == False
    
    def triggerResetButton(self):
        '''触发复位键'''
        self.ioBoard.triggerInPulse(RESULT_BUTTON_OUTPUT)
        
    def pressDemolishButton(self):
        '''按下防拆按钮-下电了'''
        self.ioBoard.outputSinglePort(DEMOLISH_BUTTON_OUTPUT,False)
        
    def releaseDemolishButton(self):
        '''释放防拆按钮-正常上电了'''
        self.ioBoard.outputSinglePort(DEMOLISH_BUTTON_OUTPUT,True)
        
    def triggerDisplayConvertButton(self):
        '''触发屏幕倒置键'''
        self.ioBoard.triggerInPulse(DISPLAY_CONVERT_BUTTON_OUTPUT,width=1)

    def openClap(self):
        '''打开夹具-测试终止'''
        #两级动作的情况
        if PARAM["openCloseStep"] ==2 :
            self.ioBoard.outputSinglePort(CLAP_CLOSE_FINAL_STEP_OUTPUT,False)
            for i in range(6):
                time.sleep(0.5)
                if self.ioBoard.inputResult[CLAP_OPEN_FIRST_STEP_OK] == False:
                    self.ioBoard.outputSinglePort(CLAMP_OPEN_CLOSE_OUTPUT,False)
                    break
        else:
            self.ioBoard.outputSinglePort(CLAMP_OPEN_CLOSE_OUTPUT,False)
    
    def closeClap(self):
        '''合上夹具-测试开始'''
        self.ioBoard.outputSinglePort(CLAMP_OPEN_CLOSE_OUTPUT,True)
        
##        两级动作的情况
#        if PARAM["openCloseStep"] == 2:
#            for i in range(6):
#                time.sleep(0.5)
#                if self.ioBoard.inputResult[CLAP_CLOSE_FIRIST_STEP_OK] == False:
#                    self.ioBoard.outputSinglePort(CLAP_CLOSE_FINAL_STEP_OUTPUT,True)
#                    break
        
        self.ioBoard.outputSinglePort(FINISH_WITH_SUCCESS_OUTPUT,False)
        self.ioBoard.outputSinglePort(FINISH_WITH_FAIL_OUTPUT,False)
    
    def closeClapAdvance(self):
        '''进一步合上夹具'''
        self.ioBoard.outputSinglePort(CLAP_CLOSE_FINAL_STEP_OUTPUT, True)
       
    def checkCloseClapSecondaryStepOK(self):
        '''夹具第二步合上到位'''
        return self.ioBoard.inputResult[CLAP_CLOSE_NEXT_STEP_OK] == False 
    
    def notifySuccess(self):
        '''输出测试成功的信号'''
        #暂时先给一个脉冲出去，后续根据情况可能有变化
        self.ioBoard.outputSinglePort(FINISH_WITH_SUCCESS_OUTPUT,True)
        
    def notifyFail(self):
        '''输出测试失败的信号'''
        self.ioBoard.outputSinglePort(FINISH_WITH_FAIL_OUTPUT,True)
    
    def sensiSwitchToLeft(self):
        '''灵敏度开关拨到左边'''
        self.ioBoard.outputSinglePort(SENSI_SWITCH_OUTPUT,False)
    
    def sensiSwitchToRight(self):
        '''灵敏度开关拨到右边'''
        self.ioBoard.outputSinglePort(SENSI_SWITCH_OUTPUT,True)
        
    def startSoundLightDetech(self):
        '''开始声光检测装置，暂时不用'''
        self.ioBoard.outputSinglePort(SOUND_LIGHT_DETECT,True)
        
    def stopSoundLightDetech(self):
        '''结束声光检测装置，暂时不用'''
        self.ioBoard.outputSinglePort(SOUND_LIGHT_DETECT,False)
        
class IOBoardAutoTrigger(AbstractAutoTrigger):
    '''开关量板触发的夹具开合信号'''
    def __init__(self):
        AbstractAutoTrigger.__init__(self)
        self.board = askForResource("GS10IOBoardDevice", GS10IOBoardDevice)    #启动IO板卡
    
    def _checkIfStart(self):
        return self.board.checkClampState() == False 
    
    def _checkIfStop(self):
        if self.board.checkClampState() == True :
            time.sleep(1)
            return True
        return False
    
    
    
    
    
