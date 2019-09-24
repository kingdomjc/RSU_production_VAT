#encoding:utf-8
u'''
变化EPC，镭雕
每次写入变化的EPC区，并进行镭雕。
'''

suiteName = u'''5-成品-变化EPC区，镭雕'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过


import uhf_tag_board,uhf_tag_variableepc_without_carve,uhf_tag_fixepc_with_carve,uhf_tag_fixepc_without_carve
from hhplt.testengine.manul import askForSomething,showDashboardMessage
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.localdata import writeToLocalData
import time
from hhplt.parameters import PARAM,SESSION
import re

autoTrigger = uhf_tag_board.autoTrigger
setup = uhf_tag_board.setup
rollback = uhf_tag_board.rollback

oldTid = None

def rollback(product):
    '''回滚函数'''
    #增加一个逻辑，若操作不成功，则次数不累加，重新写此前累积的东西
    uhf_tag_variableepc_without_carve.rollback(product)
    uhf_tag_fixepc_with_carve.rollback(product)

def finalFun(product):
    #由于两层叠加次数，因此总次数会多出一倍，这里减一下
    uhf_tag_board.finalFun(product)
    

def T_01_paramSetting_M(product):
    u'''参数设置-首次运行进行参数设置'''
    if "configed" not in SESSION:
        uhf_tag_fixepc_without_carve.__paramSetting()
        uhf_tag_fixepc_with_carve.__paramSetting()
        uhf_tag_variableepc_without_carve.__paramSetting()
        PARAM.dumpParameterToLocalFile()
    SESSION["toWriteEpc"] = uhf_tag_variableepc_without_carve.__nextEpc()
    uhf_tag_fixepc_with_carve.__getNextCarvingCode()
    showDashboardMessage(u"即将写入EPC内容:%s\n    \
                    即将镭雕的内容:%s,第%d次/共%d次\n\
                    USER区长度:%d字"%  \
                         (SESSION["toWriteEpc"],
                          SESSION["nowVariableCarve"],
                          SESSION["nowTimes"],PARAM["repeatTimes"],
                          PARAM["gs15userLength"]))

T_02_inventoryTagAndTid_A = uhf_tag_variableepc_without_carve.T_02_inventoryTagAndTid_A
T_03_testWriteEpc_A = uhf_tag_variableepc_without_carve.T_03_testWriteEpc_A
T_04_testWriteUser_A = uhf_tag_variableepc_without_carve.T_04_testWriteUser_A
T_05_laserCarve_M = uhf_tag_fixepc_with_carve.T_05_laserCarve_M


