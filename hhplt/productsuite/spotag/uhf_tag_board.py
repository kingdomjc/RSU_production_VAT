#encoding:utf-8
u'''通用单板（半成品）测试程序。
仅根据配置文件中的EPC和USER区长度，进行随机读写测试，仅测试标签的读写性能，不进行任何定制化的初始化'''


suiteName = u'''1-通用单板（半成品）测试'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.deviceresource import askForResource,GS15ReaderDevice
from hhplt.testengine.server import serverParam as SP
from hhplt.testengine.server import ServerBusiness
from hhplt.parameters import SESSION,PARAM
from hhplt.testengine.manul import manulCheck,askForSomething,autoCloseAsynMessage
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.AsynServerTaskContainer import asynServerTaskContainer
from hhplt.parameters import PARAM
import time
from hhplt.testengine.localdata import writeToLocalData



autoTrigger = GS15ReaderDevice.TagInventoryTrigger

epcSerialNumber = 0  

LOCAL_DUPLICATE_TID_SET = set()   #本地TID重复的记录

USER_TEST_STR = None
EPC_TEST_STR = None


def __getUSER_TEST_STR():
    global USER_TEST_STR
    if USER_TEST_STR is not None:
        return USER_TEST_STR
    userLength = PARAM["gs15userLength"]
    
    userCache = []
    for i in range(userLength):
        userCache.append(str(i%10)*4)
    USER_TEST_STR = "".join(userCache)
    return USER_TEST_STR

def __getEPC_TEST_STR():
    global EPC_TEST_STR
    if EPC_TEST_STR is not None:
        return EPC_TEST_STR
    epcLength = PARAM["gs15epcLength"]
    epcCache = []
    for i in range(epcLength-1):
        epcCache.append(str(i%10)*4)
    EPC_TEST_STR = "".join(epcCache)
    return EPC_TEST_STR

def __getReader():
    return askForResource("GS15ReaderDevice")


def __writeToLocalData(product):
    '''记录到本地文件'''
    if PARAM["localDataDirectory"] != '':
        writeToLocalData(product, PARAM["localDataDirectory"])   


def setup(product):
    SESSION["autoTrigger"].pause()

def finalFun(product):
    __writeToLocalData(product)
    SESSION["autoTrigger"].resume()

def rollback(product):
    SESSION["autoTrigger"].nowTid = ""

def _checkSingltonAndGetEpc():
    '''检查天线下正在检测的标签是一个'''
    reader = __getReader()
    ir = reader.inventory()
    if len(ir) == 0:
        autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"没有发现标签，请放一个标签",
                     lambda:len(reader.inventory()) == 1)
    elif len(ir) > 1:
        autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"天线下多于1个标签，请拿走多余的标签",
                     lambda:len(reader.inventory()) == 1)        
    if len(reader.nowEpc) != 1:
        raise AbortTestException(message=u"天线下标签不是1个，测试终止")
    epc = reader.nowEpc[0]
    return epc
    
oldTid = None

def T_01_inventoryTagAndTid_A(product):
    u'''清点标签并读取TID-测试标签可被清点到，并确保只有一个标签在测'''
    reader = __getReader()
    epc = _checkSingltonAndGetEpc()
    
    uiLog(u'标签清点结果:'+epc)

    global oldTid
    tid = reader.readTid()
    if tid == oldTid:
        time.sleep(0.5)
        tid = reader.readTid()
        oldTid = tid
        
    if tid == '':
        uiLog(u'TID读取失败')
        raise TestItemFailException(failWeight = 10,message = u'读取标签TID失败',output={"EPC":epc})  
    else:
        uiLog(u'读取到标签TID：'+tid)
        product.setTestingProductIdCode(tid)
        SESSION["autoTrigger"].nowTid = tid
    return {"EPC":epc,"TID":tid}

def __writeReadwriteEpc(forTestEpcStr):
    reader = __getReader()
    if reader.writeToEpc(forTestEpcStr) is not True:
        uiLog(u'EPC写入测试失败')
        raise AbortTestException(message = u'EPC写入测试失败')
    nowEpc = reader.inventory()
    if len(nowEpc) != 1 or nowEpc[0] != forTestEpcStr:
        uiLog(u'EPC写入后读取校验失败')
        raise AbortTestException(message = u'EPC写入后读取校验失败')
    SESSION["autoTrigger"].nowEpc = nowEpc[0]

def __writeReadwriteUser(forTestUserStr):
    reader = __getReader()
    if reader.writeToUser(forTestUserStr) is not True:
        uiLog(u'USER写入测试失败')
        raise TestItemFailException(failWeight = 10,message = u'USER写入测试失败')
    uiLog(u'USER写入成功，进行读校验')
    nowUser = reader.readWholeUser()
    if nowUser != forTestUserStr:
        uiLog(u'USER写入后读取校验失败')
        raise TestItemFailException(failWeight = 10,message = u'USER写入后读取校验失败')
    
def T_02_testWriteEpc_A(product):
    u'''EPC区读写测试-测试EPC区读写'''
    global epcSerialNumber
    epcSerialNumber = epcSerialNumber + 1
    if epcSerialNumber > 9990:
        epcSerialNumber = 0;
    __writeReadwriteEpc(__getEPC_TEST_STR() + "%.4d"%epcSerialNumber)

def T_03_testWriteUser_A(product):
    u'''USER区读写测试-测试USER区读写'''
    __writeReadwriteUser(__getUSER_TEST_STR())
    uiLog(u'校验正确，USER写入测试成功。')
