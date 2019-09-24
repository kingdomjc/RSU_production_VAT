#encoding:utf-8
u"""CPC缺失补充
根据镭雕工位反馈的CPCID-SN-MAC表，及目标CPCID范围，补充缺失的卡片
"""
import time

from hhplt.deviceresource import askForResource, retrieveAllResource
from hhplt.parameters import PARAM
from hhplt.productsuite.CPC.CpcMissingDbHelper import CpcMissingDbHelper
from hhplt.productsuite.CPC.macutil import transCpcIdToMac
from hhplt.productsuite.CPC.main_cpc_update import cpc_update_startup
from hhplt.testengine.exceptions import AbortTestException, TestItemFailException
from hhplt.testengine.manul import askForSomething
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.testutil import multipleTestCase

suiteName = u"CPC缺失补充"
version = "1.0"
failWeightSum = 10


from CpcTraderIssuer import CpcTraderIssuer

def __getRsu():
    return askForResource("CpcIssuer",CpcTraderIssuer)

missingDbHelper = None

def setup(product):
    pass

def finalFun(product):
    retrieveAllResource()
    if product.testResult:
        missingDbHelper.saveComplementRecord(product.getTestingProductIdCode(),product.param["targetMac"])


def rollback(product):
    cpcId = product.getTestingProductIdCode()
    missingDbHelper.rollbackCpcId(cpcId)
    uiLog(u"%s未成功补充，回收待下次使用"%cpcId)


def T_01_fetchMissingCpc_A(product):
    u"查找一个缺失的CPC-根据范围查找一个缺失的CPC"
    global missingDbHelper
    if missingDbHelper is None:
       missingDbHelper = CpcMissingDbHelper((PARAM["startCpcId"],PARAM["endCpcId"]))
       missingDbHelper.connToDb()
    try:
        cpcId = missingDbHelper.fetchAMissingCpcId()
        cpcId = askForSomething(u"即将补充",u"系统检测到目前缺失CPCID，并即将补写之",defaultValue=cpcId,autoCommit=False)
        uiLog(u"即将补充:%s"%cpcId)
        product.setTestingProductIdCode(cpcId)
    except StopIteration,e:
        raise AbortTestException(u"已全部补充完成")


def T_02_writeCpcId_A(product):
    u"改写CPCID-改写CPCID"
    all_zero = "00000000000000000000000000000000"
    new_cpcid = product.getTestingProductIdCode()
    try:
        cpc_update_startup(all_zero, 0, PARAM["issuerId"], new_cpcid)  # update cpc_id and keys
    except StandardError,e:
        raise TestItemFailException(10,message=u"写CPCID失败:%s"%str(e))
    except Exception,e:
        import traceback
        print traceback.format_exc()
        raise TestItemFailException(10,message=u"写CPCID失败:%s"%str(e))


@multipleTestCase(times=3)
def T_03_inventoryAndGetSys_A(product):
    u"卡片唤醒并验证CPCID-唤醒卡片并读取系统信息，验证CPCID改写成功"
    rsu = __getRsu()
    rsu.cpcHfActive()
    cpcSysInfo = rsu.cpcHFReadSysInfo()
    cpcId = cpcSysInfo["cpcId"]
    if cpcId != product.getTestingProductIdCode():
        raise TestItemFailException(10,message=u"写CPCID校验不成功:当前CPCID:%s"%cpcId)

    targetMac = transCpcIdToMac(cpcId)
    product.param["targetMac"] = targetMac
    uiLog(u"CPCID:%s"%cpcId)
    return cpcSysInfo


def T_04_entryTrade_A(product):
    u"入口交易-写入口信息并开卡"
    rsu = __getRsu()

    psamSlotId = PARAM["psamSlotId"]
    rsu.activePasm(psamSlotId)
    rsu.selectPsamDf01(psamSlotId)

    cpcId = product.getTestingProductIdCode()
    rsu.deliverKey(psamSlotId,cpcId)
    rsu.cpcHFSelectDf01()
    rand = rsu.cpcHFGetRand()
    cpc_mac = rsu.psamGenerateMac(psamSlotId,rand)
    rsu.cpcHFexternalAuth(cpc_mac)
    rsu.cpcHFWriteEntryInfo("01")

def T_05_closeHF_A(product):
    u"切换高频到5.8G-关闭高频并尝试5.8G唤醒"
    rsu = __getRsu()
    rsu.HFCloseRF()
    time.sleep(2)
    bst_res_map = rsu.cpc_bst_aid1(1)
    if type(bst_res_map) == dict:
        product.param["currentMac"] = bst_res_map["mac"].upper()
    else:
        raise TestItemFailException(10,message=u"5.8G唤醒失败")

def T_06_checkUpdateMac_A(product):
    u"检查并更新MAC-检查MAC地址是否正确，如不正确，则更新它"
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

@multipleTestCase(times=3)
def T_07_exitTrade_A(product):
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




