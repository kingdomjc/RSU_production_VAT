#encoding:utf-8
u"""整机MAC更新
 用于整机状态下，通过空口对MAC进行更新"""

import time
from hhplt.deviceresource import askForResource
from hhplt.parameters import PARAM
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.server import serialCode
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.testutil import multipleTestCase

suiteName = u"整机MAC更新"
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

@multipleTestCase(times=5)
def T_01_inventoryAndGetSys_A(product):
    u"卡片唤醒-唤醒卡片并读取CPC-ID等系统信息,并验证MAC"
    rsu = __getRsu()
    rsu.cpcHfActive()
    cpcSysInfo = rsu.cpcHFReadSysInfo()
    cpcId = cpcSysInfo["cpcId"]
    mac = rsu.cpcReadMac()
    uiLog(u"读取到MAC:%s，当前（临时）CPCID:%s"%(mac,cpcId))

    if mac.upper().startswith(PARAM["macPrefix"]):  #MAC前缀正确，不需要补写MAC
        product.param["retest"] = True
        product.setTestingProductIdCode(mac)
        product.param["targetMac"] = mac
    else:
        product.param["retest"] = False
        product.param["targetMac"] = serialCode("cpc.mac")
        uiLog(u"分配新MAC:%s" % product.param["targetMac"])

    product.param["cpcId"] = cpcId
    return cpcSysInfo

def T_02_updateMacInEsam_A(product):
    u"更新ESAM中的MAC-射频方式更新MCU中的MAC"
    rsu = __getRsu()
    rsu.cpcUpdateMacInEsam(product.param["targetMac"])
    # 写好后读出来，对比
    mac = rsu.cpcReadMac()
    if mac.upper() != product.param["targetMac"].upper():
        raise TestItemFailException(failWeight=10,message=u"写入ESAM中的MAC与实际不符")
    product.setTestingProductIdCode(mac)
    return {"mac":mac}

def T_03_entryTrade_A(product):
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

def T_04_closeHF_A(product):
    u"切换高频到5.8G-关闭高频并尝试5.8G唤醒"
    rsu = __getRsu()
    rsu.HFCloseRF()
    time.sleep(2)
    bst_res_map = rsu.cpc_bst_aid1(1)
    if type(bst_res_map) == dict:
        product.param["currentMac"] = bst_res_map["mac"].upper()
    else:
        raise TestItemFailException(10,message=u"5.8G唤醒失败")

def T_05_checkUpdateMac_A(product):
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

def T_06_exitTrade_A(product):
    u"出口交易-写出口信息并关卡"
    rsu = __getRsu()
    rsu.cpcHfActive()
    psamSlotId = PARAM["psamSlotId"]
    cpcId = product.param["cpcId"]
    rsu.deliverKey(psamSlotId,cpcId)
    rsu.cpcHFSelectDf01()
    rand = rsu.cpcHFGetRand()
    cpc_mac = rsu.psamGenerateMac(psamSlotId,rand)
    rsu.cpcHFexternalAuth(cpc_mac)
    rsu.cpcHFWriteEntryInfo("02")

