#encoding:utf-8
u'''
固定EPC区，进行镭雕
向EPC区写入固定内容，并进行镭雕
'''

suiteName = u'''3-成品-固定EPC区，镭雕'''
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
    SESSION["nowCarveTimes"] -= 1
    uhf_tag_board.rollback(product)


def __paramSetting():
    '''参数设置，在普通固定EPC基础上，设置镭雕序列'''
    PARAM["carvingCode"] = askForSomething(u"镭雕内容",u"请输入起始镭雕内容",autoCommit=False,defaultValue=PARAM["carvingCode"])
    PARAM["carveCarryType"] = int(askForSomething(u"镭雕进制选择",u"请写入镭雕内容的进制：\"10\"表示10进制，\"16\"表示16进制",autoCommit=False,defaultValue=PARAM["carveCarryType"]))
    PARAM["repeatTimes"] = int(askForSomething(u"同号码镭雕次数",u"同一镭雕号码重复多少标签？例如4表示，待该编码镭雕够4个标签后，再进位到下一个编码",autoCommit=False,defaultValue=PARAM["repeatTimes"]))
    SESSION["nowVariableCarve"] = PARAM["carvingCode"]   #开始起始镭雕号码
    SESSION["nowCarveTimes"] = 0 #当前已经镭雕了几次了
    

def T_01_paramSetting_M(product):
    u'''参数设置-首次运行进行参数设置'''
    if "configed" not in SESSION:
        uhf_tag_fixepc_without_carve.__paramSetting()
        uhf_tag_fixepc_without_carve.__checkTid()
        __paramSetting()
        PARAM.dumpParameterToLocalFile()

    __getNextCarvingCode()
    showDashboardMessage(u"即将写入EPC内容:%s\n\
                                                即将镭雕的内容:%s,第%d次/共%d次。\nUSER区长度:%d字"%  \
                         (PARAM["fixEpc"],SESSION["nowVariableCarve"],SESSION["nowCarveTimes"],PARAM["repeatTimes"],PARAM["gs15userLength"]))

T_02_inventoryTagAndTid_A = uhf_tag_fixepc_without_carve.T_02_inventoryTagAndTid_A
T_03_testWriteEpc_A = uhf_tag_fixepc_without_carve.T_03_testWriteEpc_A
T_04_testWriteUser_A = uhf_tag_fixepc_without_carve.T_04_testWriteUser_A

def __getLaserCaving():
    '''获得镭雕机资源'''
    return askForResource("DHLaserCarvingMachine",DaHengLaserCarvingMachine.DHLaserCarvingMachine)

def __getNextCarvingCode():
    SESSION["nowCarveTimes"] += 1
    ve = SESSION["nowVariableCarve"]
    vl = len(ve)
    if SESSION["nowCarveTimes"] > PARAM["repeatTimes"]:
        SESSION["nowCarveTimes"] = 1
        nextInt = int(ve,PARAM["carveCarryType"])
        nextInt+=1
        if PARAM["carveCarryType"] == 10:
            SESSION["nowVariableCarve"] = ("%."+str(vl)+"d")%nextInt
        elif PARAM["carveCarryType"] == 16:
            SESSION["nowVariableCarve"] = ("%."+str(vl)+"X")%nextInt
        else:
            del SESSION["configed"]
            raise AbortTestException(message=u"进制选择错误，请选择16进制或10进制")
    return SESSION["nowVariableCarve"]
    
def T_05_laserCarve_M(product):
    u'''镭雕卡面编号-自动镭雕卡面顺序编号'''
    carvingCode = SESSION["nowVariableCarve"]
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

