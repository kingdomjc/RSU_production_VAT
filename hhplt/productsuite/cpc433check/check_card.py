#encoding:utf-8
u'''433卡检卡'''


suiteName = u'''高速433卡自动检卡'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.parameters import SESSION,PARAM
from hhplt.testengine.testcase import uiLog,superUiLog
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.deviceresource import askForResource
from CheckerIOController import *
from ctypes import *
import os
from hhplt.testengine.testutil import multipleTestCase

from GS25Device import GS25Device
from GS25.GS25 import GS25Exception

autoTrigger = CheckerAutoTrigger

def __getIO():
    return askForResource("CheckerIOController", CheckerIOController)

def __getGs25():
    return askForResource("gs25",GS25Device,issueCom=PARAM["issueCom"]).gs25

def setup(product):
    SESSION["autoTrigger"].pause()
    
def finalFun(product):
    try:
        if not product.finishSmoothly:  #测试异常终止
            __getIO().notifyTestSuiteError()
        else:
            if product.testResult:#测试通过
                __getIO().notifyTestOK()
            else:
                __getIO().notifyTestNG()
        time.sleep(1)
        __getIO().notifyReady()
    finally:
        SESSION["autoTrigger"].resume()

@multipleTestCase(times=2)
def T_01_findCard_A(product):
    u"寻卡-寻卡读取CPC ID"
    try:
        cardId = __getGs25().MIreadCardId()
        product.setTestingProductIdCode(cardId)
        return {u"卡ID":cardId}
    except GS25Exception,e:
        raise TestItemFailException(failWeight=10, message=u"寻卡失败:"+str(e))

@multipleTestCase(times=2)
def T_02_testPower_A(product):
    u"测试卡电量-读取卡电量，并判断是否大于下限"
    try:
        ret = __getGs25().MIShowCardStatus(product.getTestingProductIdCode())
        pow_value = ret["power"]
        res = {u"卡电量":pow_value}
        if pow_value < PARAM["powLow"]:
            raise TestItemFailException(failWeight=10, message=u"获取电量值异常，值：%.2f"%pow_value,output=res)
        return res
    except GS25Exception,e:
        raise TestItemFailException(failWeight=10, message=u"卡状态获取失败:"+str(e))

def T_03_psamValid_A(product):
    u"PSAM密钥认证（暂时不测）-PSAM密钥认证"
    pass

@multipleTestCase(times=2)
def T_04_testEnterWake_A(product):
    u"测试入口模式-测试CPC卡能够正常进入入口模式"
    try:
        ret = __getGs25().MISetEnterMode(product.getTestingProductIdCode())
        if ret["status"] != 0 :
            raise TestItemFailException(failWeight=10, message=u"进入入口模式失败")
        ret = __getGs25().MIShowCardStatus(product.getTestingProductIdCode())
        if ret["mode"] != "onRoad":
            raise TestItemFailException(failWeight=10, message=u"进入入口模式失败")
    except GS25Exception,e:
        raise TestItemFailException(failWeight=10, message=u"进入入口模式失败:"+str(e))

@multipleTestCase(times=2)
def T_05_testEnteredData_A(product):
    u"查询入口卡信息-查询入口时卡信息并验证"
    try:
        ret = __getGs25().MIGetCardData(product.getTestingProductIdCode())
        print ret
        if len(ret["route"]) != 0 or    \
            ret["crypto"] != product.getTestingProductIdCode()*2 :
            TestItemFailException(failWeight=10, message=u"入口卡数据错误,路径数量:%d，值:%s"%(len(ret["route"]),ret["crypto"]))
    except GS25Exception,e:
        raise TestItemFailException(failWeight=10, message=u"查询入口卡信息失败:"+str(e))
    
def T_06_entryPathQuery_A(product):
    u"入口路径查询测试（暂时不测）-写入路口路径，测试查询"
    pass
  
@multipleTestCase(times=2)  
def T_07_testExitMode_A(product):
    u"测试出口模式-测试CPC卡能够正常进入出口模式"
    try:
        ret = __getGs25().MISetExitMode(product.getTestingProductIdCode())
        if ret["status"] != 0:
            raise TestItemFailException(failWeight=10, message=u"进入出口模式失败")
        ret = __getGs25().MIShowCardStatus(product.getTestingProductIdCode())
        if ret["mode"] != "sleep":
            raise TestItemFailException(failWeight=10, message=u"进入出口模式失败")
    except GS25Exception,e:
        raise TestItemFailException(failWeight=10, message=u"进入出口模式失败:"+str(e))






