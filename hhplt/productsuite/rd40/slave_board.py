#encoding:utf-8
u"从设备单板测试"

suiteName = u'''从设备单板测试'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过


from hhplt.testengine.manul import askForSomething,manulCheck
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.productsuite.rd40.RD40MSTestcase.Reader24G import Reader24G,Reader24G_Exception
from hhplt.testengine.server import serverParam as SP,serialCode
from hhplt.parameters import SESSION,PARAM
from hhplt.testengine.testcase import uiLog,superUiLog

from hhplt.testengine.testutil import WrappedPyUnitTestCase

import binascii,socket,struct,time

from master_board import reader24GTestcase,TC,CURRENT_TESTING_READER

def setup(product): 
    global CURRENT_TESTING_READER
    try:
        CURRENT_TESTING_READER.open(0,SP("rd40.defaultClientIp","192.168.0.10",str),SP("rd40.defaultClientPort",5000,int))
    except Exception,e:
        raise AbortTestException(failWeight = 10,message = u'打开设备网口失败')

def finalFun(product):
    global CURRENT_TESTING_READER
    CURRENT_TESTING_READER.close()


def T_01_scanBarCode_M(product):
    u"扫描条码-扫描从设备条码"
    barCode = askForSomething(u"扫描条码", u"请扫描单板条码",autoCommit=False)
    product.setTestingSuiteBarCode(barCode)
    product.setTestingProductIdCode(barCode)
    return {u"主单板条码":barCode}

@reader24GTestcase
def T_02_setAddr_A(product):
    u"设置地址及方向-设置从设备地址及方向"
    global CURRENT_TESTING_READER
    CURRENT_TESTING_READER.setSlaveAddr(2, 2)
    sd = SP("rd40.slave.slaveDirection",1,int)
    CURRENT_TESTING_READER.setSlaveDirection(2, 0)
    return {u"显示方向":sd}

@reader24GTestcase
def T_03_testSendPower_A(product):
    u"发射功率测试-从设备发射功率测试"
    global CURRENT_TESTING_READER,TC
    l,h = {},{}
    l[1],h[1], l[2],h[2], l[3],h[3], l[4],h[4], l[5],h[5] = \
        (int(x) for x in SP("rd40.slave.powerLevelLimit","65,70,68,73,72,77,77,82,84,90",str).split(","))
    result = {}
    for level in range(1,6):
        ret = CURRENT_TESTING_READER.testSendPower(2, 1, level)
        TC.assertGreaterEqual(ret, l[level],u"级别%d功率超过下限，功率值:%d,下限:%d"%(level,ret,l[level]))
        TC.assertLessEqual(ret, h[level],u"级别%d功率超过上限，功率值:%d,上限:%d"%(level,ret,h[level]))
        result[u"%d级功率值"%level] = ret
    return result

@reader24GTestcase
def T_04_testRecvSensi_A(product):
    u"接收功率测试-测试接收功率"
    global CURRENT_TESTING_READER,TC
    recvSensiLevel = SP("rd40.slave.recvSensiLevel",970,int)
    CURRENT_TESTING_READER.enterRecvSensi(2,1)
    time.sleep(7)
    ret = CURRENT_TESTING_READER.getRecvSensiResult(2,1)
    TC.assertGreaterEqual(ret,recvSensiLevel ,u"接收值:%d，门限:%d"%(ret,recvSensiLevel))
    return {u"接收灵敏度测试结果":ret}

@reader24GTestcase
def T_05_setInitParam_A(product):
    u"设置初始参数-设置DATT、RSSI、频率等初始参数并验证"
    global CURRENT_TESTING_READER,TC
    sd,sr,sf = \
        SP("rd40.master.slaveDatt",0,int), \
        SP("rd40.master.slaveRssi",95,int),  \
        SP("rd40.master.slaveFreq",29,int)
    CURRENT_TESTING_READER.setSlaveDatt(2, sd)
    CURRENT_TESTING_READER.setSlaveRssi(2, sr)
    CURRENT_TESTING_READER.setSlaveFreq(2,sf)
    ret = CURRENT_TESTING_READER.querySlaveInfo(1)
    TC.assertEqual(ret[12:], SP("rd40.slave.slaveVerifyStr","02005f1d00",str),u"参数设置验证不通过")
    return {u"DATT":sd,u"RSSI":sr,u"Freq":sf}



    