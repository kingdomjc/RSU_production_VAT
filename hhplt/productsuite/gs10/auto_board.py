#encoding:utf-8
u'''自动单板工位测试项，包括数字和射频'''


suiteName = u'''自动单板工位测试项'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.testengine.testcase import uiLog
from hhplt.testengine.server import serialCode,serverParam as SP
from hhplt.productsuite.gs10.board_digital import __checkBarCode,__toBytesarray,__askForPlateDeviceCom,__initFactorySetting
from hhplt.productsuite.gs10 import board_digital,board_rf_conduct
from hhplt.testengine.manul import manulCheck,askForSomething,autoCloseAsynMessage
from hhplt.parameters import SESSION
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.deviceresource import askForResource,GS10IOBoardDevice
import os,time

from hhplt.testengine.testutil import multipleTest

#开关量板夹具开合触发器
autoTrigger = GS10IOBoardDevice.IOBoardAutoTrigger

def __getIoBoard():
    return askForResource("GS10IOBoardDevice", GS10IOBoardDevice.GS10IOBoardDevice,)    #启动IO板卡

def setup(product):
    '''检查工装板电流，如果范围不对，终止测试'''
    SESSION["autoTrigger"].pause()
    iob = __getIoBoard()
    try:
        iob.releaseDemolishButton()
        board_digital.setup(product)
    except AbortTestException,e:
        iob.openClap()
        raise e
        

def finalFun(product):
    '''自动弹开夹具，输出结果信号，并给OBU下电'''
    board_digital.finalFun(product)
    iob = __getIoBoard()
    if product.testResult:
        iob.notifySuccess()
    else:
        iob.notifyFail()
    iob.openClap()
    SESSION["autoTrigger"].resume()
    
def rollback(product):
    board_digital.rollback(product)

def T_01_testVersionDownload_A(product):
    u'''测试版本下载-下载测试版本'''
    board_digital.T_01_testVersionDownload_A(product)

def T_02_initFactorySetting_A(product):
    u'''出厂信息写入-写入MAC地址，唤醒灵敏度参数等，通过BSL方式写入并自动判断信息一致'''
    barCode = askForSomething(u"扫描条码", u"请扫描单板条码")
    while not __checkBarCode(barCode):
        barCode = askForSomething(u"扫描条码", u"条码扫描错误，请重新扫描")
    __initFactorySetting(product,barCode)

def T_03_rs232Test_A(product):
    u'''RS232测试-自动判断RS232应答返回是否正确'''
    return board_digital.T_03_rs232Test_A(product)

def T_04_esam_A(product):
    u'''ESAM测试-判断地区分散码是否正确'''
    return board_digital.T_08_esam_A(product)

def T_05_transmittingPower_A(product):
    u'''发射功率测试-判断发射功率'''
    return multipleTest(board_rf_conduct.T_04_transmittingPower_A,product,3)

def T_06_receiveSensitivity_A(product):
    u'''接收灵敏度测试-判断接收灵敏度是否满足标准'''
    return multipleTest(board_rf_conduct.T_03_receiveSensitivity_A,product,3)

def T_07_reset_A(product):
    u'''复位测试-单板上电后返回数据，系统自动判断是否正确'''
    sc = __askForPlateDeviceCom()
    iob = __getIoBoard()
    sc.asynSend("TestReset")
    iob.triggerResetButton()
    sc.asynReceiveAndAssert("PowerOnSuccess")
    time.sleep(0.5)

def T_08_capacityVoltage_A(product):
    u'''电容电路电压测试-根据电容电路电压值判断是否满足要求'''
    return board_digital.T_05_capacityVoltage_A(product)

def T_09_solarVoltage_A(product):
    u'''太阳能电路电压测试-判断太阳能电路电压是否满足要求'''
    return board_digital.T_06_solarVoltage_A(product)

def T_10_batteryVoltage_A(product):
    u'''电池电路电压测试-判断电池电路电压是否满足要求'''
    return board_digital.T_07_batteryVoltage_A(product)

def T_11_testHFChip_A(product):
    u'''测试高频芯片-测试高频芯片是否正常'''
    return board_digital.T_09_testHFChip_A(product)

def T_12_redLight_M(product):
    u'''红色LED灯测试-人工判断指示红色灯显示、蜂鸣器响声是否正常'''
    sc = __askForPlateDeviceCom()
    sc.assertSynComm(request ='TestLedLight',response = 'TestLedLightOK')
    sc.assertSynComm(request ='TestRedLedPara 1000',response = 'TestRedLedParaOK')
    mcr = manulCheck(u"声光指示测试", u"请确认红色指示灯正常亮起，蜂鸣器响声正常。")
    if not mcr:
        raise TestItemFailException(failWeight = 10,message = u'红色LED指示测试人工判断不通过！')

def T_13_greenLight_M(product):
    u'''绿色LED灯检测-人工判定绿LED灯是否正常亮起'''
    sc = __askForPlateDeviceCom()
    sc.assertSynComm(request ='TestGreenLedPara 1000',response = 'TestGreenLedParaOK')
    mcr = manulCheck(u"声光指示测试", u"请确认绿色指示灯正常亮起，蜂鸣器响声正常。")
    if not mcr:
        raise TestItemFailException(failWeight = 10,message = u'绿色LED指示测试人工判断不通过！')
    
    

def T_15_oled_M(product):
    u'''OLED屏幕测试-人工判断OLED屏幕是否全白'''
    sc = __askForPlateDeviceCom()
    sc.asynSend('TestOLED')
    if not manulCheck(u"OLED屏幕测试", u"请确认屏幕全白。"):
        raise TestItemFailException(failWeight = 10,message = u'OLED屏幕测试人工判断不通过！')
    sc.asynReceiveAndAssert('TestOLEDOK')
    
def T_16_displayDirKey_A(product):
    u'''显示方向控制键测试-屏幕显示倒转，检查是否通过'''
    sc = __askForPlateDeviceCom()
    #sc.assertSynComm(request ='CloseLcdDisp',response = 'CloseLcdDispOK')
    iob = __getIoBoard()
    time.sleep(1)
    iob.triggerDisplayConvertButton()
    time.sleep(1)
    sc.assertSynComm(request ='TestDirection',response = 'TestDirectionOK')
    time.sleep(1)
    sc.assertSynComm(request ='ReadButtonStatus',response = 'ButtonisRelease')

def T_17_testSensiSwitch_M(product):
    u'''灵敏度条件开关测试-测试灵敏度调节开关拨动并确保其出厂在L位置'''
    sc = __askForPlateDeviceCom()
     
    r = sc.assertAndGetNumberParam(request ='TestSensiSwitch',response = 'TestSensiSwitch')
    failException = TestItemFailException(failWeight = 10,message = u'灵敏度开关测试不通过')
    if r == 0:
        autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"请将灵敏度开关拨至另一侧",
                             lambda:sc.assertAndGetNumberParam(request ='TestSensiSwitch',response = 'TestSensiSwitch') == 1
                            ,failException)
        autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"测试成功，请将灵敏度开关拨回原来的位置",
                             lambda:sc.assertAndGetNumberParam(request ='TestSensiSwitch',response = 'TestSensiSwitch') == 0
                            ,failException)
    else:
        autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"请将灵敏度开关拨至另一侧",
                             lambda:sc.assertAndGetNumberParam(request ='TestSensiSwitch',response = 'TestSensiSwitch') == 0
                            ,failException)

def T_18_readRfCard_A(product):
    u'''读高频卡测试-读高频卡测试'''
    return board_rf_conduct.T_01_readRfCard_A(product)
    
def T_19_wakeupSensitivity_A(product):
    u'''唤醒灵敏度测试-判断高低灵敏度是否满足标准'''
    return board_rf_conduct.T_02_wakeupSensitivity_A(product)

#def T_18_disturbOn14k_A(product):
#    u'''5.8G芯片上电14k干扰测试-上电时发送14k，检查干扰是否造成混乱'''
#    sc = __askForPlateDeviceCom()
#    iob = __getIoBoard()
#    time.sleep(0.5)
#    iob.pressDemolishButton()
#    sc.asynSend('EtSend14k 3000')
#    time.sleep(1)
#    iob.releaseDemolishButton()
#    time.sleep(1)
#    res = sc.asynReceive()
#    uiLog(u"串口接收:%s"%(res))
#    time.sleep(1)
#    sc.clearSerialBuffer()
#    target_power = -35    
#    sc.bslDevice.calibra_target_power(target_power)
#    if not sc.bslDevice.test_if_obu_wakeup():
#        raise TestItemFailException(failWeight = 10,message = u'5.8G芯片14k干扰测试不通过!')

def T_20_staticCurrent_A(product):
    u'''静态电流测试-判断静态电流值是否在正常范围内'''
    return board_rf_conduct.T_05_staticCurrent_A(product)
    
def T_21_deepStaticCurrent_A(product):
    u'''深度静态电流测试-判断深度静态电流值是否在正常范围内'''
    iob = __getIoBoard()
    sc = __askForPlateDeviceCom()
    iob.pressDemolishButton()
    sc.assertSynComm(request ='CloseObuUart',response = 'CloseObuUartOK')
    time.sleep(2)
    try:
        v = sc.testDeepStaticCurrent()
        resultMap = {u"深度静态电流":v}
        if v < SP('gs10.deepStaticCurrent.low',0) or v > SP('gs10.deepStaticCurrent.high',3):
            raise TestItemFailException(failWeight = 10,message = u'深度静态电流测试不通过',output=resultMap)
        return resultMap
    except TestItemFailException,e:
        raise e
    except:
        raise TestItemFailException(failWeight = 10,message = u'深度静态电流测试失败')
    finally:
        sc.assertSynComm(request ='OpenObuUart',response = 'OpenObuUartOK')
        iob.releaseDemolishButton()
    







