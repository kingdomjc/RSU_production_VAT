#encoding:utf-8
u'''GS15 UHF卡整机通用测试，测试装配后的卡片功能及性能是否正常
将被测标签放在射频覆盖范围内，测试通过后进行顺序镭雕。'''

suiteName = u'''顺序镭雕的超高频卡成品测试'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

import uhf_card_overall,uhf_card_board
from hhplt.deviceresource import askForResource,DaHengLaserCarvingMachine
from hhplt.parameters import PARAM,SESSION
from hhplt.testengine.manul import autoCloseAsynMessage
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.testcase import uiLog
import re

autoTrigger = uhf_card_overall.autoTrigger
setup = uhf_card_overall.setup
finalFun = uhf_card_overall.finalFun
rollback = uhf_card_overall.rollback

T_01_inventoryTagAndTid_A = uhf_card_overall.T_01_inventoryTagAndTid_A
T_02_testWriteEpc_A = uhf_card_overall.T_02_testWriteEpc_A
T_03_testWriteUser_A = uhf_card_overall.T_03_testWriteUser_A

def __getLaserCaving():
    '''获得镭雕机资源'''
    return askForResource("DHLaserCarvingMachine",DaHengLaserCarvingMachine.DHLaserCarvingMachine)

def __carveTest(carvingCode,product):
    '''镭雕测试项'''
    __getLaserCaving().toCarveCode(carvingCode)
    try:
        autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"当前镭雕号:%s,请踩下踏板进行镭雕"%carvingCode,
                                 lambda:__getLaserCaving().carved()
                                ,TestItemFailException(failWeight = 10,message = u'镭雕机未响应'))
    except TestItemFailException,e:
        __getLaserCaving().clearCarveCode()
        raise e
    product.addBindingCode(u"卡面编码",carvingCode)
    if PARAM["carveCodeToEpcOffset"] == -1:
        return {u"卡面编码":carvingCode}
    else:
        uiLog(u"EPC的%d符号开始写入卡面编码：%s"%(PARAM["carveCodeToEpcOffset"],carvingCode))
        nowEpc = SESSION["autoTrigger"].nowEpc
        newEpc = nowEpc[:PARAM["carveCodeToEpcOffset"]] + carvingCode + nowEpc[PARAM["carveCodeToEpcOffset"]+len(carvingCode):]
        uiLog(u'尝试写入EPC：'+newEpc)
        uhf_card_board.__writeReadwriteEpc(newEpc)
        return {u"卡面编码":carvingCode,u"EPC出厂值":newEpc}
    
def __getNextCarvingCode(carvingCode):
    head = re.split("\d",carvingCode,1)[0]
    if head == '':
        nextSerialCode = str(int(carvingCode) + 1)
    else:
        carvingNumber = carvingCode[carvingCode.find(head)+len(head):]
        nextSerialCode = str(int(carvingNumber) + 1)

    return head + "0"*(len(carvingCode)-len(nextSerialCode) - len(head))+ nextSerialCode

def T_04_laserCarve_M(product):
    u'''镭雕卡面编号-自动镭雕卡面顺序编号'''
    carvingCode = PARAM["carvingCode"]
#    print carvingCode
    rs = __carveTest(carvingCode,product)
#    rs = None
    PARAM["carvingCode"] = __getNextCarvingCode(carvingCode)
    PARAM.dumpParameterToLocalFile()
    return rs
    
    
