#encoding:utf-8
u"""CPC入口开卡测试
进行入口写卡并开卡
"""
import time

from hhplt.deviceresource import askForResource
from hhplt.parameters import PARAM
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.manul import manulCheck
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.testutil import multipleTestCase

suiteName = u"沣雷CPC入场交易与开卡"
version = "1.0"
failWeightSum = 10
g_model = None
from CpcTraderIssuerExt import CpcTraderIssuerExt

def __getRsu():
    return askForResource(g_model.__name__,g_model)

def setup(product,model=CpcTraderIssuerExt):
    global g_model
    g_model = model
    rsu = __getRsu()
    psamSlotId = PARAM["psamSlotId"]
    rsu.activePasm(psamSlotId)
    rsu.selectPsamDf01(psamSlotId)

def finalFun(product):
    pass

def rollback(product):
    pass

@multipleTestCase(times=5)
def T_01_inventoryAndGetSys_A(product):
    u"卡片唤醒-唤醒卡片并读取CPC-ID等系统信息"
    rsu = __getRsu()
    rsu.cpcHfActive()
    cpcSysInfo = rsu.cpcHFReadSysInfo()
    cpcId = cpcSysInfo["cpcId"]
    mac = rsu.cpcReadMac()
    uiLog(u"读取到MAC:%s，当前（临时）CPCID:%s"%(mac,cpcId))
    product.setTestingProductIdCode(mac)
    product.param["cpcId"] = cpcId
    return cpcSysInfo

def T_02_entryTrade_A(product):
    u"入口交易-写入口信息并开卡"
    rsu = __getRsu()
    psamSlotId = PARAM["psamSlotId"]
    cpcId = product.param["cpcId"]
    rsu.deliverKey(psamSlotId,cpcId)
    rsu.cpcHFSelectDf01()
    rand = rsu.cpcHFGetRand()
    cpc_mac = rsu.psamGenerateMac(psamSlotId,rand)
    rsu.cpcHFexternalAuth(cpc_mac)
    rsu.cpcHFWriteEntryInfo("01")

def T_03_clearRoute_A(product):
    u"清除路径信息-清除路径信息"
    rsu = __getRsu()
    psamSlot = PARAM["psamSlotId"]
    cpcId = product.param["cpcId"]
    #rsu.activePasm(psamSlot)
    #rsu.selectPsamDf01(psamSlot)
    rsu.deliverKey(psamSlot,cpcId)
    rsu.cpcHFSelectDf01()
    rand = rsu.cpcHFGetRand()
    cpc_mac = rsu.psamGenerateMac(psamSlot,rand)
    rsu.cpcHFexternalAuth(cpc_mac)
    rsu.cpcHFClearRouteInfo(1)

def T_04_assertCpcOpened_A(product):
    u"验证卡片打开-验证入场信息写入并已开卡"
    # manulCheck(u"操作提示",u"请挪走标签再挪回来",check="ok")
    rsu = __getRsu()
    rsu.HFCloseRF()
    time.sleep(4)
    try:
        rsu.cpcHfActive()
    except TestItemFailException,e:
        time.sleep(4)
        rsu.cpcHfActive()
    state = rsu.cpcHFReadBaseInfo()
    if state["RfpowerFlag"] != 1:
        raise TestItemFailException(failWeight = 10,message = u'卡片未上电，请检查并复测')
    if state["powerRatio"] < PARAM["powerLimit"]:
        raise TestItemFailException(failWeight = 10,message = u'卡片电量不足',output=state)
    return state





