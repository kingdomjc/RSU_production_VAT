#encoding:utf-8
u"""CPC标识路径检验及出口关卡

"""
import time

from hhplt.deviceresource import askForResource
from hhplt.parameters import PARAM
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.manul import manulCheck

suiteName = u"CPC路径验证及关卡"
version = "1.0"
failWeightSum = 10

from CpcTraderIssuer import CpcTraderIssuer

def __getRsu():
    return askForResource("CpcIssuer",CpcTraderIssuer)

def setup(product):
    rsu = __getRsu()
    psamSlotId = PARAM["psamSlotId"]
    rsu.activePasm(psamSlotId)
    rsu.selectPsamDf01(psamSlotId)

def finalFun(product):
    pass

def rollback(product):
    pass

def T_01_inventoryAndGetSys_A(product):
    u"卡片唤醒-唤醒卡片并读取CPC-ID等系统信息"
    rsu = __getRsu()
    rsu.cpcHfActive()
    cpcSysInfo = rsu.cpcHFReadSysInfo()
    cpcId = cpcSysInfo["cpcId"]
    product.setTestingProductIdCode(cpcId)
    return cpcSysInfo

def T_02_inspectRoute_A(product):
    u"路径检查-检查外场RSU测试是否成功标识路径"
    rsu = __getRsu()
    rsu.cpcHFSelectDf01()
    routeData = rsu.cpcHFReadRouteInfo(1)
    return {u"路径信息":routeData }

def T_03_exitTrade_A(product):
    u"出口交易-写出口信息并关卡"
    rsu = __getRsu()
    psamSlotId = PARAM["psamSlotId"]
    cpcId = product.getTestingProductIdCode()
    rsu.deliverKey(psamSlotId,cpcId)
    rsu.cpcHFSelectDf01()
    rand = rsu.cpcHFGetRand()
    cpc_mac = rsu.psamGenerateMac(psamSlotId,rand)
    rsu.cpcHFexternalAuth(cpc_mac)
    rsu.cpcHFWriteEntryInfo("02")

def T_04_ensureCpcClosed_A(product):
    u"验证卡片关闭-验证卡片正常关闭"
    #manulCheck(u"操作提示",u"请挪走标签再挪回来",check="ok")
    rsu = __getRsu()
    rsu.HFCloseRF()
    time.sleep(2.5)
    try:
        rsu.cpcHfActive()
    except TestItemFailException,e:
        time.sleep(0.5)
        rsu.cpcHfActive()
    state = rsu.cpcHFReadBaseInfo()
    if state["RfpowerFlag"] != 0:
        raise TestItemFailException(failWeight = 10,message = u'卡片未断电，请检查并复测')
    if state["powerRatio"] < PARAM["powerLimit"]:
        raise TestItemFailException(failWeight = 10,message = u'卡片电量不足',output=state)

    return state
