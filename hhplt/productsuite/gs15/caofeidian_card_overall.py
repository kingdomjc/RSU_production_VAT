#encoding:utf-8
u'''GS15 UHF唐山曹妃甸港口通行卡整机测试，测试装配后的卡片功能及性能是否正常
自动写入顺序的EPC编号
将被测标签放在射频覆盖范围内。结束后请移走标签，放置下一张。'''

#from hhplt.testengine.manul import askForSomething


suiteName = u'''曹妃甸港口通行卡成品测试'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.productsuite.generaluhf import uhf_card_overall_with_serial_carving,uhf_card_board
from hhplt.parameters import PARAM
import time


autoTrigger = uhf_card_overall_with_serial_carving.autoTrigger 
setup = uhf_card_overall_with_serial_carving.setup
finalFun = uhf_card_overall_with_serial_carving.finalFun
rollback = uhf_card_overall_with_serial_carving.rollback

global epcGenerateContainer 
epcGenerateContainer = {"workbayId":0,"loginNumber":0,"serialNum":0}


def __getInitEpc():
    '''初始EPC值，保证不重复，依据2015-5-26魏博邮件中要求的编码规则，不出现字母逻辑如下：
        [1][YYYYMMDD][工位编号][登录顺序号][补齐其余位数字]
    '''    
    global epcGenerateContainer 
    if epcGenerateContainer["loginNumber"] == 0:
        epcGenerateContainer["loginNumber"] = PARAM["loginSerialNumber"] + 1
        PARAM["loginSerialNumber"] = epcGenerateContainer["loginNumber"]
        PARAM.dumpParameterToLocalFile()
        epcGenerateContainer["workbayId"] = int(PARAM["workbay"][-1:])
    epcGenerateContainer["serialNum"] = epcGenerateContainer["serialNum"] + 1
    serHex = "%d"%epcGenerateContainer["serialNum"]
    prefix = "1%s0000%.1d%d"%(
                           time.strftime('%Y%m%d',time.localtime(time.time())),
                           epcGenerateContainer["workbayId"]%10,
                           epcGenerateContainer["loginNumber"]%100)
    return prefix + (PARAM["gs15epcLength"]*4 - len(prefix) - len(serHex))*'0' + serHex
    

def T_01_inventoryTagAndTid_A(product):
    u'''清点标签并读取TID-测试标签可被清点到，并确保只有一个标签在测'''
    #print __getInitEpc()
    return uhf_card_overall_with_serial_carving.T_01_inventoryTagAndTid_A(product)

def T_02_testWriteEpc_A(product):
    u'''EPC区读写测试-测试EPC并根据卡面号写入出厂值'''
    initEpc = __getInitEpc()
    uhf_card_board.__writeReadwriteEpc(initEpc)
    product.addBindingCode(u"EPC出厂值",initEpc)
    return {u"EPC出厂值":initEpc}

def T_03_testWriteUser_A(product):
    u'''USER区读写测试-清零USER区'''
    return uhf_card_overall_with_serial_carving.T_03_testWriteUser_A(product)

def T_04_laserCarve_M(product):
    u'''镭雕卡面编号-自动镭雕卡面顺序编号'''
    return uhf_card_overall_with_serial_carving.T_04_laserCarve_M(product)
    
    
    
    