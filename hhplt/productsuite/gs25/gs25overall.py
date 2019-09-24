#encoding:utf-8
u'''GS25发卡器生产测试，整机测试工位。请插好USB线及串口线，准备好OBU及高频卡，点击开始测试'''

suiteName = u'''GS25整机测试'''
version="1.0"
failWeightSum = 10


from gs25board import usbTestor
from hhplt.testengine.server import serverParam as SP,serialCode
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.deviceresource import GS25Testor
from hhplt.testengine.manul import askForSomething,manulCheck
from hhplt.testengine.server import ServerBusiness
import testCases
from hhplt.parameters import SESSION
from hhplt.testengine.testcase import uiLog,superUiLog
import re

uartTestor = testCases.TestGS25_UART()

def __checkBoardFinished(idCode):
    '''检查单板(数字、射频）工位已完成'''
    with ServerBusiness(testflow = True) as sb:
        status = sb.getProductTestStatus(productName="GS25" ,idCode = idCode)
        if status is None:
            raise AbortTestException(message=u"该产品尚未进行单板测试，整机测试终止")
        else:
            sn1 = u"GS25单板测试"
            if sn1 not in status["suiteStatus"] or status["suiteStatus"][sn1] != 'PASS':
                raise AbortTestException(message=u"该产品的单板测试项未进行或未通过，整机测试终止")

def setup(product):
    '''初始化函数'''
    try:
        usbTestor.setUp()
    except Exception,e:
        raise AbortTestException(u"初始化USB连接失败"+str(e))

def finalFun(product):
    usbTestor.tearDown()

def __checkBarCode(barCode):
    '''检查整机条码扫描'''
    if re.match("^[0-9]{16}$", barCode) == None:return False
    if not barCode.startswith(SP("gs25.overall.barcodePrefix","2950000001",str)):return False
    return True

def T_01_scanBarCode_M(product):
    u'''扫描整机条码-扫描整机条码'''
    barCode = askForSomething(u"扫描条码", u"请扫描整机条码",autoCommit=False)
    while not __checkBarCode(barCode):
        barCode = askForSomething(u"扫描条码", u"整机条码扫描错误，请重新扫描",autoCommit=False)
    product.setTestingSuiteBarCode(barCode)
    product.addBindingCode(u"整机条码",barCode)
    return {u"整机条码":barCode}

def T_02_readDeviceSn_A(product):
    u'''读取设备序列号-读取设备序列号，并检查单板是否通过测试'''
    try:
        deviceSn = testCases.GS25.readDeviceSn()[0]
        uiLog(u"设备序列号:"+deviceSn)
        if not SESSION["isMend"]:__checkBoardFinished(deviceSn)
        product.setTestingProductIdCode(deviceSn)
        return {u"设备序列号":deviceSn}
    except AbortTestException,e:
        raise e
    except Exception,e:
        raise AbortTestException(u"无法读取设备序列号"+str(e))


def T_03_uartTest_A(product):
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


def T_04_testBeep_M(product):
    u'''蜂鸣器测试-人工判定蜂鸣器是否响起'''
    global usbTestor
    usbTestor.setUp()
    usbTestor.test_Beep()
    mcr = manulCheck(u"蜂鸣器测试", u"请确认听到蜂鸣器的声音。")
    if not mcr:raise TestItemFailException(failWeight = 10,message = u'蜂鸣器人工检测不通过!')

def T_05_testLightRedLed_M(product):
    u"红色LED指示灯检测-人工判定红色指示灯是否正常亮起"
    global usbTestor
    usbTestor.setUp()
    usbTestor.test_LightRedLed()
    usbTestor.tearDown()
    mcr = manulCheck(u"指示灯测试", u"请确认红色指示灯亮起。")
    if not mcr:raise TestItemFailException(failWeight = 10,message = u'红色指示灯人工检测不通过!')

def T_06_testLightGreenLed_M(product):
    u"绿色LED指示灯检测-人工判定绿色指示灯是否正常亮起"
    global usbTestor
    usbTestor.setUp()
    usbTestor.test_LightGreenLed()
    usbTestor.tearDown()
    mcr = manulCheck(u"指示灯测试", u"请确认绿色指示灯亮起。")
    if not mcr:raise TestItemFailException(failWeight = 10,message = u'绿色指示灯人工检测不通过!')

def T_07_etcTradeWithoutPsam_A(product):
    u'''无PSAM卡交易测试-无PSAM卡交易测试'''
    global usbTestor    
    manulCheck(u"操作提示",u"请将OBU插【华虹卡】后放置在发卡器上，待OBU绿灯闪烁后确定","ok")
    try:
        usbTestor.setUp()
        usbTestor.test_EtcTradeWithoutPsam()
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'无PSAM卡交易测试失败!'+str(e))


def xT_04_etcTradeWithPsam_A(product):
    u'''有PSAM卡交易测试-有PSAM卡交易测试'''
    manulCheck(u"操作提示",u"请将OBU插【国标卡】后放置在发卡器上，待OBU绿灯闪烁后确定","ok")
    try:
        usbTestor.test_EtcTradeWithPsam()
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'有PSAM卡交易测试失败!'+str(e))

def T_08_cpuCardTest_A(product):
    u"CPU卡测试-读取CPU卡测试"
    global usbTestor   
    manulCheck(u"操作提示",u"请将CPU卡放置在发卡器上，然后点击确定","ok")
    try:
        usbTestor.setUp()
        usbTestor.test_CpuCard()
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'CPU卡测试失败!'+str(e))

def T_09_m1CardTest_A(product):
    u"M1卡测试-读取M1卡测试"
    global usbTestor   
    manulCheck(u"操作提示",u"请将M1卡放置在发卡器上，然后点击确定","ok")
    global usbTestor   
    try:
        usbTestor.setUp()
        usbTestor.test_M1Card()
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'M1卡测试失败!'+str(e))

def T_10_miReadCardID_A(product):
    u"复合卡ID读取测试-读取复合卡ID测试"
    global usbTestor  
    manulCheck(u"操作提示",u"请将复合卡放置在发卡器上，然后点击确定","ok")
    try:
        usbTestor.setUp()
        usbTestor.test_MIreadCardId()
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'MI卡ID读取测试失败!'+str(e))





