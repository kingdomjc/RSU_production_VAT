#encoding:utf-8
u""" 集成CPC交易
在发卡器上完成入口交易、标识路径、检验路径、出口交易等测试
在无外场RSU标识的条件下，可选用此测试流程"""
import time

import CpcEntryTest as ENTRY
import CpcRouteInspectExitTest as EXIT
from hhplt.parameters import PARAM
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.testutil import multipleTestCase
from hhplt.deviceresource import askForResource, retrieveAllResource

suiteName = u"CPC集成出入口及路径标识测试"
version = "1.0"
failWeightSum = 10

def setup(product):
    ENTRY.setup(product)

def finalFun(product):
    retrieveAllResource()

def rollback(product):
    pass


T_01_inventoryAndGetSys_A = ENTRY.T_01_inventoryAndGetSys_A

T_02_entryTrade_A = ENTRY.T_02_entryTrade_A

T_03_clearRoute_A = ENTRY.T_03_clearRoute_A

T_04_assertCpcOpened_A = ENTRY.T_04_assertCpcOpened_A

@multipleTestCase(times=3)
def T_05_routeSign_A(product):
    u"路径标识-模拟路径标识信息"
    rsu = ENTRY.__getRsu()
    rsu.HFCloseRF()
    time.sleep(2)
    testRouteInfo = rsu.integrateCpcSignRoute(PARAM["psamSlotId"],product.getTestingProductIdCode())
    uiLog(u"测试模拟路径：%s"%testRouteInfo)
    product.param["testRouteInfo"] = testRouteInfo


def T_06_inspectRoute_A(product):
    u"检查路径标识-检查路径标识是否成功"
    ENTRY.__getRsu().cpcHfActive()
    ret = EXIT.T_02_inspectRoute_A(product)
    if product.param["testRouteInfo"] not in ret[u"路径信息"]:
        raise TestItemFailException(failWeight = 10,message = u'路径标识检查错误')

T_07_exitTrade_A = EXIT.T_03_exitTrade_A

T_08_ensureCpcClosed_A = EXIT.T_04_ensureCpcClosed_A




