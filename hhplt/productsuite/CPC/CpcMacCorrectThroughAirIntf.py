#encoding:utf-8
u"""空口确认修改MAC """



import time

from hhplt.deviceresource import askForResource
from hhplt.parameters import PARAM
from hhplt.productsuite.CPC.macutil import transCpcIdToMac
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.manul import manulCheck
from hhplt.testengine.testcase import uiLog

suiteName = u"CPC空口MAC修正"
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
    targetMac = transCpcIdToMac(cpcId)
    product.param["targetMac"] = targetMac
    product.setTestingProductIdCode(cpcId)
    uiLog(u"CPCID:%s"%cpcId)
    return cpcSysInfo

def T_02_entryTrade_A(product):
    u"入口交易-写入口信息并开卡"
    rsu = __getRsu()
    psamSlotId = PARAM["psamSlotId"]
    cpcId = product.getTestingProductIdCode()
    rsu.deliverKey(psamSlotId,cpcId)
    rsu.cpcHFSelectDf01()
    rand = rsu.cpcHFGetRand()
    cpc_mac = rsu.psamGenerateMac(psamSlotId,rand)
    rsu.cpcHFexternalAuth(cpc_mac)
    rsu.cpcHFWriteEntryInfo("01")

def T_03_closeHF_A(product):
    u"切换高频到5.8G-关闭高频并尝试5.8G唤醒"
    rsu = __getRsu()
    rsu.HFCloseRF()
    time.sleep(2)
    bst_res_map = rsu.cpc_bst_aid1(1)
    if type(bst_res_map) == dict:
        product.param["currentMac"] = bst_res_map["mac"].upper()
    else:
        raise TestItemFailException(10,message=u"5.8G唤醒失败")

def T_04_checkUpdateMac_A(product):
    u"检并更新MAC-检查MAC地址是否正确，如不正确，则更新它"
    rsu = __getRsu()
    try:
        if product.param["currentMac"] != product.param["targetMac"]:
            uiLog(u"原MAC:%s,目标更新MAC:%s"%(product.param["currentMac"] , product.param["targetMac"]))
            rsu.updateMacThroughAI(product.param["targetMac"])
            rsu.cpc_bst_aid1(1,targetMac = product.param["targetMac"])
        else:
            uiLog(u"原MAC:%s,正确"%(product.param["currentMac"]))
    finally:
        rsu.endAppProc()

def T_05_exitTrade_A(product):
    u"出口交易-写出口信息并关卡"
    rsu = __getRsu()
    rsu.cpcHfActive()
    psamSlotId = PARAM["psamSlotId"]
    cpcId = product.getTestingProductIdCode()
    rsu.deliverKey(psamSlotId,cpcId)
    rsu.cpcHFSelectDf01()
    rand = rsu.cpcHFGetRand()
    cpc_mac = rsu.psamGenerateMac(psamSlotId,rand)
    rsu.cpcHFexternalAuth(cpc_mac)
    rsu.cpcHFWriteEntryInfo("02")

