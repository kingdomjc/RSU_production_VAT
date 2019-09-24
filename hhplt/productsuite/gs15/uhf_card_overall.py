#encoding:utf-8
u'''GS15 UHF卡整机通用测试，测试装配后的卡片功能及性能是否正常
将被测标签放在射频覆盖范围内，结束后更换标签继续测试。'''

suiteName = u'''超高频卡整机测试'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

import uhf_card_board
from hhplt.testengine.manul import askForSomething
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.localdata import writeToLocalData
import re
import time
from hhplt.parameters import PARAM,SESSION


BAR_CODE_REGX = "^32082[0-9]{7}$"


autoTrigger = uhf_card_board.autoTrigger 
oldTid = None


def __writeToLocalData(product):
    '''记录到本地文件'''
    if PARAM["localDataDirectory"] != '':
        writeToLocalData(product, PARAM["localDataDirectory"])   

def setup(product):
    SESSION["autoTrigger"].pause()

def finalFun(product):
    SESSION["autoTrigger"].resume()
    __writeToLocalData(product)

def rollback(product):
    SESSION["autoTrigger"].nowTid = ""

def __T_01_scanBarCode_M(product):
    u'''扫描条码-扫描环保卡上面印刷的条码'''
    barCode = askForSomething(u"扫描条码", u"请扫描卡片表面的条码",autoCommit=False)
    while re.match(BAR_CODE_REGX, barCode) is None:
        barCode = askForSomething(u"扫描条码", u"条码扫描错误，请重新扫描",autoCommit = False)
    product.addBindingCode(u"条码",barCode)
    product.setTestingSuiteBarCode(barCode)
    return {u"条码":barCode}

def T_02_inventoryTagAndTid_A(product):
    u'''清点标签并读取TID-测试标签可被清点到，并确保只有一个标签在测'''
    reader = uhf_card_board.__getReader()
    epc = uhf_card_board._checkSingltonAndGetEpc()
    tid = reader.readTid()
    if tid == '':
        raise TestItemFailException(failWeight = 10,message = u'读取标签TID失败',output={"EPC":epc})  
    global oldTid
    if tid == oldTid:
        time.sleep(0.5)
        tid = reader.readTid()
        oldTid = tid
    SESSION["autoTrigger"].nowTid = tid
    product.setTestingProductIdCode(tid)
    return {"EPC":epc,"TID":tid}

def T_03_testWriteEpc_A(product):
    u'''EPC区读写测试-测试EPC写入出厂值'''
    uhf_card_board.__writeReadwriteEpc(PARAM["gs15initEpc"])
    return {u"EPC出厂值":PARAM["gs15initEpc"]}

def T_04_testWriteUser_A(product):
    u'''USER区读写测试-清零USER区'''
    uhf_card_board.__writeReadwriteUser("0"*(PARAM["gs15userLength"]*4))
