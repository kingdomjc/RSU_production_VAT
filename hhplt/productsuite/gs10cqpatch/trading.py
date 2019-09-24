#encoding:utf-8
u'''维修交易测试工位，测试交易并绑定整机镭雕码'''

suiteName = u'''维修交易测试工位'''
version = "1.0"
failWeightSum = 10

from hhplt.parameters import SESSION,PARAM
from hhplt.testengine.autoTrigger import AutoStartStopTrigger
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.deviceresource import askForResource,ShhicGS25Trader
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.server import serverParam as SP
from hhplt.testengine.manul import manulCheck
import time
import re


#绑定工位的自动触发器
autoTrigger = AutoStartStopTrigger

localRecordFile = "localdata/local_record_"+ time.strftime('%Y-%m-%d',time.localtime(time.time()))+".txt"
localRecord = {}

def __writeToLocalRecord(mac,barCode,contractSerial):
    '''写入本地记录'''
    f = open(localRecordFile,'a')
    f.write("%s,%s,%s\n"%(mac,barCode,contractSerial))
    f.close()

def __askForTrader():
    '''获得交易资源(ZXRIS 8801)'''
    sc = askForResource('ShhicGS25Trader', ShhicGS25Trader.ShhicGS25)
    return sc

def setup(product):
    SESSION["isMend"] = True

def T_02_readObuId_A(product):
    u'''读取OBU内部标识-通过发卡器读取OBUID并与镭雕条码进行绑定'''
    manulCheck(u"操作提示",u"请将整机放置在发卡器上，待绿灯闪烁后确定","ok")
    sc = __askForTrader()
    for i in range(5):
        try:
            mac,contractSerial = sc.readObuId()
            uiLog(u'测试产品标识:'+mac)
            product.setTestingProductIdCode(mac)
            product.addBindingCode(u"合同序列号",contractSerial)
            uiLog(u'绑定合同序列号:'+contractSerial)
            esamVersion = sc.getEsamVersion()
            uiLog(u'ESAM版本:'+esamVersion)
            __writeToLocalRecord(mac,product.getTestingSuiteBarCode(),contractSerial)   #记录到本地文件
            break
        except Exception,e:
            print e
            time.sleep(0.1)
    else:
        raise TestItemFailException(failWeight = 10,message = u'获得OBUID失败:'+e.message)
    return {u"OBUID":mac,u"Esam版本":esamVersion}

# def T_04_initDf0107File_A(product):
#     u'''初始化DF01文件-初始化DF01的07文件'''
#     sc = __askForTrader()
#     sc.initDf0107File()

def T_05_trade_A(product):
    u'''交易测试-模拟交易测试是否成功'''
    time.sleep(1)
    sc = __askForTrader()
    sc.testTrade()




