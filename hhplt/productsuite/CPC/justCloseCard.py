#encoding:utf-8
""" 自动关卡
"""
import time

from hhplt.deviceresource import askForResource
from hhplt.parameters import PARAM
from hhplt.testengine.autoTrigger import AutoStartStopTrigger
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.manul import manulCheck
from hhplt.testengine.testutil import multipleTestCase

suiteName = u"CPC关卡"
version = "1.0"
failWeightSum = 10

autoTrigger =  AutoStartStopTrigger

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

@multipleTestCase(times=30)
def T_01_inventoryAndGetSys_A(product):
    u"关卡-高频唤醒并直接关卡"
    rsu = __getRsu()
    rsu.cpcHfActive()
    cpcSysInfo = rsu.cpcHFReadSysInfo()
    cpcId = cpcSysInfo["cpcId"]
    product.setTestingProductIdCode(cpcId)
    psamSlotId = PARAM["psamSlotId"]
    cpcId = product.getTestingProductIdCode()
    rsu.deliverKey(psamSlotId,cpcId)
    rsu.cpcHFSelectDf01()
    rand = rsu.cpcHFGetRand()
    cpc_mac = rsu.psamGenerateMac(psamSlotId,rand)
    rsu.cpcHFexternalAuth(cpc_mac)
    rsu.cpcHFWriteEntryInfo("02")

