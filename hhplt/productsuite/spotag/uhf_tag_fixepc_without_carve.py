#encoding:utf-8
u'''
固定EPC区，不镭雕
向EPC区写入固定的内容，不进行镭雕。在首次运行时进行相关的参数设置。
'''

suiteName = u'''2-成品-固定EPC区，不镭雕'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.testengine.manul import askForSomething,showDashboardMessage
import uhf_tag_board
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.localdata import writeToLocalData
import time
from hhplt.parameters import PARAM,SESSION
import re

oldTid = None

autoTrigger = uhf_tag_board.autoTrigger
setup = uhf_tag_board.setup
finalFun = uhf_tag_board.finalFun
rollback = uhf_tag_board.rollback

def __checkHexAvailable(length,value):
    HEX_PTN = "^([0-9]|[A-F]){%d}$"
    return re.match(HEX_PTN%(length*4),value) is not None

def __paramSetting():
    '''基础参数设置：包含EPC长度、USER长度、EPC固定值'''
    PARAM["gs15epcLength"] = int(askForSomething(u"EPC长度设置",u"请输入EPC区长度，单位:字（WORD，1WORD = 2Byte = 16bit）",autoCommit=False,defaultValue=PARAM["gs15epcLength"]))
    PARAM["fixEpc"] = askForSomething(u"固定EPC内容",u"请输入要写入EPC区的固定内容，16进制表示",autoCommit=False,defaultValue=PARAM["fixEpc"]).upper()
    while not __checkHexAvailable(PARAM["gs15epcLength"],PARAM["fixEpc"]):
        PARAM["fixEpc"] = askForSomething(u"固定EPC内容",u"输入有误！\n请输入要写入EPC区的固定内容，16进制表示",autoCommit=False,defaultValue=PARAM["fixEpc"]).upper()
    PARAM["gs15userLength"] = int(askForSomething(u"USER区长度设置",u"请输入USER区长度，单位:字（WORD，1WORD = 2Byte = 16bit）",autoCommit=False,defaultValue=PARAM["gs15userLength"]))
    SESSION["configed"] = True
    
    
def __checkTid():
    '''设置TID写入EPC事宜'''
    PARAM["tidToEpc"] = askForSomething(u"TID写入EPC",u"如果需要将TID的某段写入EPC，请在此输入TID区的起始位置和长度及写入EPC的位置（单位：字节）\n\
                    例如：3,4,5表明取TID结果的3字节开始的4个字节，写入EPC区第5个字节开始的位置。\n如不需要，则输入0。",autoCommit=False,defaultValue=PARAM["tidToEpc"])


def T_01_paramSetting_M(product):
    u'''参数设置-首次运行进行参数设置'''
    if "configed" not in SESSION:
        __paramSetting()
        __checkTid()
        PARAM.dumpParameterToLocalFile()
    showDashboardMessage(u"固定写入EPC内容:\n%s\n不镭雕,USER区长度:%d字"%(PARAM["fixEpc"],PARAM["gs15userLength"]))
        
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
    toWriteEpc = PARAM["fixEpc"]
    if PARAM["tidToEpc"] != "0":
        tidStart,tidLen,epcStart = PARAM["tidToEpc"].split(",")
        tidStart,tidLen,epcStart = int(tidStart),int(tidLen),int(epcStart)
        tid = product.getTestingProductIdCode()
        toWriteEpc = toWriteEpc[:epcStart*2] + tid[tidStart*2:(tidStart+tidLen)*2] + toWriteEpc[(epcStart+tidLen)*2:]
    
    uhf_tag_board.__writeReadwriteEpc(toWriteEpc)
    product.addBindingCode(u"EPC出厂值",toWriteEpc)
    return {u"EPC出厂值":toWriteEpc}

def T_04_testWriteUser_A(product):
    u'''USER区读写测试-清零USER区'''
    uhf_tag_board.__writeReadwriteUser("0"*(PARAM["gs15userLength"]*4))


