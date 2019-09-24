#encoding:utf-8
u'''这项测试又是虚拟测试项，用于调试'''


suiteName = u'''虚拟测试项2'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过


from hhplt.testengine.testutil import multipleTest
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.server import ServerBusiness
import time
from hhplt.parameters import PARAM
import hhplt.testengine.manul as manul



#测试函数体例：T_<序号>_方法名
#_A为自动完成测试，_M为人工测试；函数正常完成，返回值为输出数据（可空）；异常完成，抛出TestItemFailException异常，含输出（可选）
#函数的doc中，<测试名称>-<描述>

def finalFun(product):
    if "boardResult" in PARAM and PARAM["boardResult"]:
        manul.broadcastTestResult(product)
    
    from hhplt.testengine.localdata import writeToLocalData
    writeToLocalData(product)

def setupFun(product):
    manul.closeAsynMessage()

def T_01_initFactorySetting_A(product):
    u'''出厂信息写入-出厂信息写入（包括MAC地址，唤醒灵敏度参数）'''
    mac = "F400007C"
    product.setTestingProductIdCode(mac)
    time.sleep(1)

    
def T_02_testVerisonDownload_A(product):
    u'''测试版本下载-下载测试版本，自动判断是否下载成功'''
    time.sleep(1)
    product.addBindingCode(u"EPC出厂值",str(time.time()))
#    raise TestItemFailException(failWeight = 3,message = u'测试版本下载失败')

def __T_03_soundLight_M(product):
    u'''声光指示测试-指示灯显示正常，蜂鸣器响声正常。人工确认后才停止显示和响'''
    time.sleep(1)
    from hhplt.testengine.manul import manulCheck
    if manulCheck(u"声光指示测试", u"请确认这破玩意是正常亮了吗？"):
        return {"随便写的返回值":300}
    else:
        raise TestItemFailException(failWeight = 10,message = u'声光测试失败')
#        raise AbortTestException(message = u'服务端连接异常')

def T_03_soundLight_M(product):
    u'''声光指示测试-指示灯显示正常，蜂鸣器响声正常。人工确认后才停止显示和响'''
    return multipleTest(__T_03_soundLight_M,product,3)

    
def T_04_BatteryVoltage_A(product):
    u'''电池电路电压测试-返回电池电路电压值，后台根据配置判定'''
#    time.sleep(3)
    with ServerBusiness(testflow=True) as sb:
        pass
    
def T_05_MOCK_TEST_A(product):
    u'''模拟测试1-用于调试界面啥也不干'''
    time.sleep(1)
def T_06_MOCK_TEST_A(product):
    u'''模拟测试2-用于调试界面啥也不干'''
    time.sleep(1)
#def T_07_MOCK_TEST_A(product):
#    u'''模拟测试3-用于调试界面啥也不干'''
#    time.sleep(1)
#def T_08_MOCK_TEST_A(product):
#    u'''模拟测试4-用于调试界面啥也不干'''
#    time.sleep(1)
#def T_09_MOCK_TEST_A(product):
#    u'''模拟测试5-用于调试界面啥也不干'''
#    time.sleep(1)
#def T_10_MOCK_TEST_A(product):
#    u'''模拟测试6-用于调试界面啥也不干'''
#    time.sleep(1)
#def T_11_MOCK_TEST_A(product):
#    u'''模拟测试7-用于调试界面啥也不干'''
#    time.sleep(1)
#def T_12_MOCK_TEST_A(product):
#    u'''模拟测试8-用于调试界面啥也不干'''
#    time.sleep(1)
#def T_13_MOCK_TEST_A(product):
#    u'''模拟测试9-用于调试界面啥也不干'''
#    time.sleep(1)
    
    
    
    
    
    
    

    
    
    