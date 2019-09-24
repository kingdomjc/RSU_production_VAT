#encoding:utf-8
u'''维修交易复测工位，用于维修后验证交易是否成功'''

suiteName = u'''维修交易复测工位'''
version = "1.0"
failWeightSum = 10

from hhplt.parameters import SESSION
from hhplt.testengine.manul import askForSomething
from hhplt.testengine.autoTrigger import AutoStartStopTrigger 
from hhplt.testengine.server import ServerBusiness
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.productsuite.gs10 import overall_unit
from hhplt.deviceresource import askForResource,CpuCardTrader
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.server import serverParam as SP
from hhplt.testengine.manul import manulCheck

import time
import re

#绑定工位的自动触发器
autoTrigger = AutoStartStopTrigger

def __askForTrader():
    '''获得交易资源(ZXRIS 8801)'''
    sc = askForResource('CpuCardTrader', CpuCardTrader.CpuCardTrader)
    return sc


def setup(product):
    SESSION["isMend"] = True   #维修复测
    
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
            uiLog(u'读取合同序列号:'+contractSerial)
            break
        except Exception,e:
            print e
            time.sleep(0.1)
    else:
        raise TestItemFailException(failWeight = 10,message = u'获得OBUID失败:'+e.message)
    return {u"OBUID":mac}

def T_03_trade_A(product):
    u'''交易测试-模拟交易测试是否成功'''
    time.sleep(1)
    sc = __askForTrader()
    sc.testTrade()
