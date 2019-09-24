#encoding:utf-8
u"""
模块: 海尔智能货架，高频阅读器板测试
"""
from thread import start_new_thread

import time

from hhplt.deviceresource import askForResource
from hhplt.parameters import PARAM
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.localdb import writeProductToLocalDb
from hhplt.testengine.manul import askForSomething, manulCheck
from hhplt.testengine.server import serverParam as SP
from hhplt.testengine.testcase import uiLog

suiteName = u"阅读器板测试"
version = "1.0"
failWeightSum = 10



from rd201Driver import RD201Driver
from analyzerDeviceForHrReader import SpectrumAnalyzerForHrReader

def __getReader():
    # RD201驱动
    return askForResource("RD201", RD201Driver, readerCom = PARAM["RD201SerialPort"])

def __getSpecAnlzr():
    # 获得频谱仪，用于读功率
    return askForResource("SpectrumAnalyzerForHrReader", SpectrumAnalyzerForHrReader,
                          spectrumAnalyzerIp = PARAM["spectrumAnalyzerIp"],
                          spectrumAnalyzerPort = PARAM["spectrumAnalyzerPort"])

def setup(product):
    pass

def finalFun(product):
    writeProductToLocalDb(product,"hfReaderBoard.db")

def T_01_scanBare_M(product):
    u"扫码条码-扫描单板条码"
    barCode = askForSomething(u"扫描条码", u"请扫描单板条码",autoCommit=False)
    while len(barCode) != 10:
        barCode = askForSomething(u"扫描条码", u"条码扫描错误，请重新扫描",autoCommit = False)
    product.setTestingSuiteBarCode(barCode)
    product.setTestingProductIdCode(barCode)
    product.addBindingCode(u"单板条码",barCode)
    return {u"单板条码":barCode}


def T_03_inventory_A(product):
    u"清点测试-检测是否可能完整清点所有数量的标签"
    manulCheck(u"操作提示",u"请确认阅读器单板串口、电源、天线连接完好，点击OK开始测试","ok")
    rd201 = __getReader()

    continueCount = 0
    for i in range(1,11):
        count = len(rd201.inventoryTags())
        if count >= PARAM["RD201TargetTagCount"]:
            continueCount += 1
        else:
            continueCount = 0
        uiLog(u"第%d次清点到标签数量:%d"%(i,count))
        if continueCount >= PARAM["continuesTagCount"]:
            return {u"测试清点数量":count}
    raise TestItemFailException(failWeight = 10,message = u'读取标签数量测试不通过，数量不够',output={u"测试清点数量":count})

def __asynInven(rd201):
    while rd201.setting:
        rd201.inventoryTags()  #不用管它是否读到标签，目的是开天线

def T_02_powerTest_A(product):
    u"功率测试-测试功率值是否达标，并记录功率值"
    manulCheck(u"操作提示",u"请将阅读器天线接口连接到频谱仪上，点击OK开始测试","ok")
    sa = __getSpecAnlzr()
    sa.resetForRead()
    rd201 = __getReader()
    rd201.setting = True
    start_new_thread(__asynInven,(rd201,))
    time.sleep(0.5)
    power = sa.readPowerValue()
    rd201.setting = False
    res = {u"阅读器发射功率":power}
    product.addBindingCode(u"发射功率",power)
    if not( SP("hr.reader.power.low",34) <= power <= SP("hr.reader.power.high",35)):
        raise TestItemFailException(failWeight = 10,message = u'发射功率值不合格',output=res)

    sa.setForIdleRead()
    time.sleep(0.5)
    idlePower = sa.readPowerValue()
    uiLog(u"空闲时功率:%f"%idlePower)
    if idlePower > 0:
        raise TestItemFailException(failWeight = 10,message = u'空闲状态依然有功率值:%f'%idlePower,output=res)
    
    return res










