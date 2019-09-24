#encoding:utf-8
u'''GS25发卡器生产测试，单板测试工位。请插好USB线及串口线，点击开始测试'''

suiteName = u'''GS25单板测试'''
version="1.0"
failWeightSum = 10

from hhplt.testengine.server import serverParam as SP,serialCode
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.deviceresource import GS25Testor
from hhplt.testengine.manul import askForSomething,manulCheck
from hhplt.testengine.testcase import uiLog,superUiLog
import testCases
from hhplt.parameters import SESSION
import re

uartTestor = testCases.TestGS25_UART()
usbTestor = testCases.TestGS25_USB()

def setup(product):
    '''初始化函数'''
    
def finalFun(product):
    '''结束函数'''
    global uartTestor,usbTestor
    #uartTestor.tearDown()
    #usbTestor.tearDown()

def __checkBarCode(barCode):
    '''检查单板条码扫描'''
    if re.match("^[0-9]{16}$", barCode) == None:return False
    if not barCode.startswith(SP("gs25.board.barcodePrefix","2950002001",str)):return False
    return True
    
def T_01_scanBarCode_M(product):
    u'''扫描单板条码-扫描单板条码'''
    barCode = askForSomething(u"扫描条码", u"请扫描单板条码",autoCommit=False)
    while not __checkBarCode(barCode):
        barCode = askForSomething(u"扫描条码", u"单板条码扫描错误，请重新扫描",autoCommit=False)
    product.setTestingSuiteBarCode(barCode)
    product.addBindingCode(u"单板条码",barCode)
    return {u"单板条码":barCode}

def T_02_uartTest_A(product):
    u'''UART串口测试-自动测试UART串口通信是否正常'''
    global uartTestor
    try:    #UART资源只使用一次，然后就关掉了。
        uartTestor.setUp()
        uartTestor.test_ReadInfo()        
    except GS25Testor.GS25Exception as e:
        print e
        raise TestItemFailException(failWeight = 10,message=u"UART通信失败")
    finally:
        uartTestor.tearDown()

def T_03_usbReadInfo_A(product):
    u'''读取设备信息测试-自动测试读取设备信息'''
    global usbTestor
    try:
        usbTestor.setUp()
        usbTestor.test_ReadInfo()
    except GS25Testor.GS25Exception:
        raise TestItemFailException(failWeight = 10,message=u"USB通信失败")
    finally:
        usbTestor.tearDown()
  
def T_04_initDeviceId_A(product):
    u'''分配设备标识-分配唯一的设备标识并写入设备'''
    global usbTestor
    try:
        usbTestor.setUp()
        oriDeviceSn = testCases.GS25.readDeviceSn()[0]
        deviceSn = None
        if oriDeviceSn == "ffffffffff":
            if SESSION["testor"] == u"单机":
                deviceSn = "0000000001"
                uiLog(u"因单机运行而无法分配设备序列号，写入测试值:"+deviceSn)
            else:
                deviceSn = serialCode("gs25DeviceSn")#分配新标识
            usbTestor.test_writeDeviceSn(deviceSn)
        else:
            uiLog(u"存在原序列号:"+oriDeviceSn)
            deviceSn = oriDeviceSn
        product.setTestingProductIdCode(deviceSn)
        return {u"设备序列号":deviceSn}
    except Exception,e:
        print e
        raise TestItemFailException(failWeight = 10,message=u"USB通信失败 "+str(e))
    finally:
        usbTestor.tearDown()
    
def T_05_testBeep_M(product):
    u'''蜂鸣器测试-人工判定蜂鸣器是否响起'''
    global usbTestor
    usbTestor.setUp()
    usbTestor.test_Beep()
    mcr = manulCheck(u"蜂鸣器测试", u"请确认听到蜂鸣器的声音。")
    if not mcr:raise TestItemFailException(failWeight = 10,message = u'蜂鸣器人工检测不通过!')

def T_06_testLightRedLed_M(product):
    u"红色LED指示灯检测-人工判定红色指示灯是否正常亮起"
    global usbTestor
    usbTestor.setUp()
    usbTestor.test_LightRedLed()
    usbTestor.tearDown()
    mcr = manulCheck(u"指示灯测试", u"请确认红色指示灯亮起。")
    if not mcr:raise TestItemFailException(failWeight = 10,message = u'红色指示灯人工检测不通过!')

def T_07_testLightGreenLed_M(product):
    u"绿色LED指示灯检测-人工判定绿色指示灯是否正常亮起"
    global usbTestor
    usbTestor.setUp()
    usbTestor.test_LightGreenLed()
    usbTestor.tearDown()
    mcr = manulCheck(u"指示灯测试", u"请确认绿色指示灯亮起。")
    if not mcr:raise TestItemFailException(failWeight = 10,message = u'绿色指示灯人工检测不通过!')

def T_08_testPsam1_A(product):
    u"PSAM卡槽1检测-自动判定PSAM卡槽1功能正常"
    global usbTestor
    try:
        usbTestor.setUp()
        usbTestor.test_Psam_1()
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'PSAM卡槽1检测不通过!'+str(e))
    finally:
        usbTestor.tearDown()

def T_09_testPsam2_A(product):
    u"PSAM卡槽2检测-自动判定PSAM卡槽2功能正常"
    global usbTestor
    try:
        usbTestor.setUp()
        usbTestor.test_Psam_2()
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'PSAM卡槽2检测不通过!'+str(e))
    finally:
        usbTestor.tearDown()

def T_10_testPsam3_A(product):
    u"PSAM卡槽3检测-自动判定PSAM卡槽3功能正常"
    global usbTestor
    try:
        usbTestor.setUp()
        usbTestor.test_Psam_3()
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'PSAM卡槽3检测不通过!'+str(e))
    finally:
        usbTestor.tearDown()

def T_11_testPsam4_A(product):
    u"PSAM卡槽4检测-自动判定PSAM卡槽4功能正常"
    global usbTestor
    try:
        usbTestor.setUp()
        usbTestor.test_Psam_4()
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'PSAM卡槽4检测不通过!'+str(e))
    finally:
        usbTestor.tearDown()

def T_12_testIcc_A(product):
    u"PSAM卡槽0(ICC卡)检测-自动判定ICC读取功能正常"
    global usbTestor
    try:
        usbTestor.setUp()
        usbTestor.test_icc()
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'ICC卡槽检测不通过!'+str(e))
    finally:
        usbTestor.tearDown()

def T_13_etcTradeWithoutPsam_A(product):
    u'''无PSAM卡交易测试-无PSAM卡交易测试'''
    manulCheck(u"操作提示",u"请将OBU插【华虹卡】后放置在发卡器上，待OBU绿灯闪烁后确定","ok")
    global usbTestor
    try:
        usbTestor.setUp()
        usbTestor.test_EtcTradeWithoutPsam()
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'无PSAM卡交易测试失败!'+str(e))
    finally:
        usbTestor.tearDown()


def xT_04_etcTradeWithPsam_A(product):
    u'''有PSAM卡交易测试-有PSAM卡交易测试'''
    manulCheck(u"操作提示",u"请将OBU插【国标卡】后放置在发卡器上，待OBU绿灯闪烁后确定","ok")
    try:
        usbTestor.test_EtcTradeWithPsam()
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'有PSAM卡交易测试失败!'+str(e))

def T_14_cpuCardTest_A(product):
    u"CPU卡测试-读取CPU卡测试"
    manulCheck(u"操作提示",u"请将CPU卡放置在发卡器上，然后点击确定","ok")
    global usbTestor
    try:
        usbTestor.setUp()
        usbTestor.test_CpuCard()
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'CPU卡测试失败!'+str(e))
    finally:
        usbTestor.tearDown()

def T_15_m1CardTest_A(product):
    u"M1卡测试-读取M1卡测试"
    manulCheck(u"操作提示",u"请将M1卡放置在发卡器上，然后点击确定","ok")
    global usbTestor
    try:
        usbTestor.setUp()
        usbTestor.test_M1Card()
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'M1卡测试失败!'+str(e))
    finally:
        usbTestor.tearDown()

def T_16_miReadCardID_A(product):
    u"复合卡ID读取测试-读取复合卡ID测试"
    manulCheck(u"操作提示",u"请将复合卡放置在发卡器上，然后点击确定","ok")
    global usbTestor
    try:
        usbTestor.setUp()
        usbTestor.test_MIreadCardId()
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'MI卡ID读取测试失败!'+str(e))
    finally:
        usbTestor.tearDown()


