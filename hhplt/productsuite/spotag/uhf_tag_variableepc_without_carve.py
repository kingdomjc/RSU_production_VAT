#encoding:utf-8
u'''
变化EPC区，不镭雕
每次写入变化的EPC区，不进行镭雕。在首次运行时进行相关的参数设置。
'''

suiteName = u'''4-成品-变化EPC区，不镭雕'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.testengine.manul import askForSomething,showDashboardMessage
import uhf_tag_board,uhf_tag_fixepc_without_carve
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.localdata import writeToLocalData
import time
from hhplt.parameters import PARAM,SESSION
import re

autoTrigger = uhf_tag_board.autoTrigger
setup = uhf_tag_board.setup
finalFun = uhf_tag_board.finalFun
rollback = uhf_tag_board.rollback

oldTid = None

def rollback(product):
    '''回滚函数'''
    #增加一个逻辑，若操作不成功，则次数不累加，重新写此前累积的东西
    SESSION["nowTimes"] -= 1
    uhf_tag_board.rollback(product)


def __paramSetting():
    '''参数设置，在固定EPC、不镭雕的设置基础上，增加关于可变EPC的设置'''
    SESSION["nowTimes"] = 0 #当前这个EPC已经写入了几次了
    PARAM["variableEpcStart"] = askForSomething(u"可变EPC起始设置",u"请输入起始EPC编码(16进制表示)\n\
            系统将在此前设置的固定EPC基础上，将变化内容写入末尾\n\
            例如: 固定EPC为112233440000000000000000，可变内容为3005，则最终写入的值为: 112233440000000000003005，并递增     \
            ",autoCommit=False,defaultValue=PARAM["variableEpcStart"])
    PARAM["carryType"] = int(askForSomething(u"可变EPC进制选择",u"请写入EPC的可变内容的进制：\"10\"表示10进制，\"16\"表示16进制",autoCommit=False,defaultValue=PARAM["carryType"]))
    PARAM["repeatTimes"] = int(askForSomething(u"同EPC写入次数",u"同一EPC重复多少标签？例如4表示，待同一个EPC写够4个标签后，再进位到下一个EPC",autoCommit=False,defaultValue=PARAM["repeatTimes"]))
    SESSION["nowVariableEpc"] = PARAM["variableEpcStart"]   #开始起始EPC

def __nextEpc():
    '''获得下一个需要写入的EPC值'''
    SESSION["nowTimes"] += 1
    ve = SESSION["nowVariableEpc"]
    vl = len(ve)
    if SESSION["nowTimes"] > PARAM["repeatTimes"]:
        SESSION["nowTimes"] = 1
        nextInt = int(ve,PARAM["carryType"])
        nextInt+=1
        if PARAM["carryType"] == 10:
            SESSION["nowVariableEpc"] = ("%."+str(vl)+"d")%nextInt
        elif PARAM["carryType"] == 16:
            SESSION["nowVariableEpc"] = ("%."+str(vl)+"X")%nextInt
        else:
            del SESSION["configed"]
            raise AbortTestException(message=u"进制选择错误，请选择16进制或10进制")
    
    return PARAM["fixEpc"][:-vl] + SESSION["nowVariableEpc"]

def T_01_paramSetting_M(product):
    u'''参数设置-首次运行进行参数设置'''
    if "configed" not in SESSION:
        SESSION["nowTimes"] = 0 #当前这个EPC已经写入了几次了
        uhf_tag_fixepc_without_carve.__paramSetting()
        __paramSetting()
        PARAM.dumpParameterToLocalFile()
    SESSION["toWriteEpc"] = __nextEpc()
    showDashboardMessage(u"即将写入EPC内容:%s\n第%d次/共%d次，不镭雕。\nUSER区长度:%d字"%  \
                         (SESSION["toWriteEpc"],SESSION["nowTimes"],PARAM["repeatTimes"],PARAM["gs15userLength"]))
        
def T_02_inventoryTagAndTid_A(product):
    u'''清点标签并读取TID-测试标签可被清点到，并确保只有一个标签在测'''
    reader = uhf_tag_board.__getReader()
    epc = uhf_tag_board._checkSingltonAndGetEpc()
    tid = reader.readTid()
    if tid == '':
        raise TestItemFailException(failWeight = 10,message = u'读取标签TID失败',output={"EPC":epc})  
    global oldTid
    if tid == oldTid:
        time.sleep(0.5)
        tid = reader.readTid()
        oldTid = tid
    SESSION["autoTrigger"].nowTid = tid
    product.setTestingProductIdCode(tid)
    return {"EPC":epc,"TID":tid}

def T_03_testWriteEpc_A(product):
    u'''EPC区读写测试-测试EPC写入出厂值'''
    uhf_tag_board.__writeReadwriteEpc(SESSION["toWriteEpc"])
    product.addBindingCode(u"EPC出厂值",SESSION["toWriteEpc"])
    return {u"EPC出厂值":SESSION["toWriteEpc"]}

def T_04_testWriteUser_A(product):
    u'''USER区读写测试-清零USER区'''
    uhf_tag_board.__writeReadwriteUser("0"*(PARAM["gs15userLength"]*4))


