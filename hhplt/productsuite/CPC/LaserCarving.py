#encoding:utf-8
u"""镭雕
读取CPC ID并镭雕到卡面
"""
import time

from hhplt.deviceresource import DaHengLaserCarvingMachine
from hhplt.deviceresource import askForResource
from hhplt.parameters import PARAM
from DuplicateCheckDbHelper import generateDBH
from hhplt.productsuite.CPC.macutil import transCpcIdToMac
from hhplt.testengine.autoTrigger import AutoStartStopTrigger
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.manul import manulCheck, autoCloseAsynMessage,showDashboardMessage
from hhplt.testengine.testutil import multipleTestCase

suiteName = u"CPC卡镭雕"
version = "1.0"
failWeightSum = 10

from CpcTraderIssuer import CpcTraderIssuer

autoTrigger =  AutoStartStopTrigger

DBH = None

def __getRsu():
    return askForResource("CpcIssuer",CpcTraderIssuer)

def __getLaserCaving():
    #获得镭雕机资源
    return askForResource("DHLaserCarvingMachine",DaHengLaserCarvingMachine.DHLaserCarvingMachine)


def setup(product):
    global DBH
    if DBH is None:DBH = generateDBH()

def finalFun(product):
    global lastCpcId
    if product.testResult:
        DBH.recordCpc(product.getTestingProductIdCode(),product.param["sn"],product.param["mac"])
        lastCpcId = product.getTestingProductIdCode()
    showDashboardMessage(u"刚刚读到的CPCID:\n%s"%product.getTestingProductIdCode())

def rollback(product):
    pass


lastCpcId = None


@multipleTestCase(times=30)
def T_01_inventoryAndGetSys_A(product):
    u"卡片唤醒-唤醒卡片并读取CPC-ID等系统信息"
    rsu = __getRsu()
    rsu.cpcHfActive()
    cpcSysInfo = rsu.cpcHFReadSysInfo()
    # cpcSysInfo = {"cpcId":"1233456"}
    cpcId = cpcSysInfo["cpcId"]
    if cpcId == lastCpcId:raise TestItemFailException(10,message=u"等待放置新标签")


    product.setTestingProductIdCode(cpcId)
    product.param["mac"] = transCpcIdToMac(cpcId)
    return cpcSysInfo


def T_02_readSn_A(product):
    u"读取SN-射频方式读取卡片SN"
    rsu = __getRsu()
    sn = rsu.cpcReadSn()

    # sn = "1111111"
    product.param["sn"] = sn
    return {"SN":sn}


def T_03_duplicateCheck_A(product):
    u"CPCID重复检测-检查即将镭雕的CPC卡片是否重复"
    cpcId = product.getTestingProductIdCode()

    if not(PARAM["startCpcId"] <= cpcId <= PARAM["endCpcId"]):
        raise TestItemFailException(failWeight = 10,message = u'CPCID超过范围，不可镭雕',output={"cpcId":cpcId})

    cpc = DBH.getCpcId(cpcId)
    if cpc is None:return
    raise TestItemFailException(failWeight = 10,message = u'CPCID重复',output={"cpcId":cpcId})
    # if not manulCheck(u"CPC重复",u"CPCID为%s的卡片已于%s镭雕过，疑似重复。请确认是否继续镭雕"%\
    #            (cpcId,time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(cpc["carveTime"])/1000))),check="confirm"):
    #     raise TestItemFailException(failWeight = 10,message = u'CPCID重复',output={"cpcId":cpcId})

def _T_04_carving_A(product):
    u"卡面镭雕-将CPC ID镭雕到卡面"
    carvingCode = product.getTestingProductIdCode()
    __getLaserCaving().toCarveCode(carvingCode)
    try:
        autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"当前镭雕号:%s,请踩下踏板进行镭雕"%carvingCode,
                                 lambda:__getLaserCaving().carved()
                                ,TestItemFailException(failWeight = 10,message = u'镭雕机未响应'))
    except TestItemFailException,e:
        __getLaserCaving().clearCarveCode()
        raise e




