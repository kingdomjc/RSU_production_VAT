#encoding:utf-8
u'''
固定EPC区，进行镭雕TID
向EPC区写入固定内容，并进行镭雕镭雕内容为TID
'''

suiteName = u'''7-成品-固定EPC区，镭雕TID'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

import uhf_tag_board,uhf_tag_fixepc_without_carve
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.localdata import writeToLocalData
import time
from hhplt.parameters import PARAM,SESSION
import re
from hhplt.deviceresource import askForResource,DaHengLaserCarvingMachine
from hhplt.testengine.manul import askForSomething,showDashboardMessage,autoCloseAsynMessage
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException


autoTrigger = uhf_tag_board.autoTrigger
setup = uhf_tag_board.setup
finalFun = uhf_tag_board.finalFun

oldTid = None

def rollback(product):
    uhf_tag_board.rollback(product)


def __paramSetting():
    '''参数设置，在普通固定EPC基础上，设置镭雕序列'''
    PARAM["carvingTidStart"] = int(askForSomething(u"设置镭雕",u"设置镭雕起始TID位数(从0开始，包含）",autoCommit=False,defaultValue=PARAM["carvingTidStart"]))
    PARAM["carvingTidEnd"] = int(askForSomething(u"设置镭雕",u"设置镭雕终止TID位数（不包含）",autoCommit=False,defaultValue=PARAM["carvingTidEnd"]))

def T_01_paramSetting_M(product):
    u'''参数设置-首次运行进行参数设置'''
    if "configed" not in SESSION:
        uhf_tag_fixepc_without_carve.__paramSetting()
#        uhf_tag_fixepc_without_carve.__checkTid()
        __paramSetting()
        PARAM.dumpParameterToLocalFile()
    showDashboardMessage(u"即将写入EPC内容:%s\n\
                                                即将镭雕的内容:TID,%d-%d位。\nUSER区长度:%d字"%  \
                         (PARAM["fixEpc"],PARAM["carvingTidStart"],PARAM["carvingTidEnd"],PARAM["gs15userLength"]))

T_02_inventoryTagAndTid_A = uhf_tag_fixepc_without_carve.T_02_inventoryTagAndTid_A
T_03_testWriteEpc_A = uhf_tag_fixepc_without_carve.T_03_testWriteEpc_A
T_04_testWriteUser_A = uhf_tag_fixepc_without_carve.T_04_testWriteUser_A

def __getLaserCaving():
    '''获得镭雕机资源'''
    return askForResource("DHLaserCarvingMachine",DaHengLaserCarvingMachine.DHLaserCarvingMachine)

def T_05_laserCarve_M(product):
    u'''镭雕卡面编号-TID号镭雕到卡面'''
    carvingCode = product.getTestingProductIdCode()[PARAM["carvingTidStart"]:PARAM["carvingTidEnd"]]
    __getLaserCaving().toCarveCode(carvingCode)
    try:
        autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"当前镭雕号:%s,请踩下踏板进行镭雕"%carvingCode,
                                 lambda:__getLaserCaving().carved()
                                ,TestItemFailException(failWeight = 10,message = u'镭雕机未响应'))
    except TestItemFailException,e:
        __getLaserCaving().clearCarveCode()
        raise e
    product.addBindingCode(u"卡面镭雕编码",carvingCode)
    return {u"卡面镭雕编码":carvingCode}

