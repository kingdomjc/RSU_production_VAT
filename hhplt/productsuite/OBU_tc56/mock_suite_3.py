#encoding:utf-8
u'''这项测试又是虚拟测试项，用于调试'''

import time
from threading import RLock

suiteName = u'''并行虚拟测试项3'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.parameters import SESSION

from hhplt.testengine.parallelTestSynAnnotation import syntest,serialSuite


def finalFun(product):
    pass

def setup(product):
    pass

serialIdCode = 1000

def T_01_initFactorySetting_A(product):
    u'''出厂信息写入-出厂信息写入（包括MAC地址，唤醒灵敏度参数）'''
    global serialIdCode
    serialIdCode += 1
    product.setTestingProductIdCode("%.5d"%serialIdCode)
#    raise AbortTestException(message=u"终止了啊") 
    time.sleep(0.5)
    
#@syntest
def T_03_soundLight_M(product):
    u'''声光指示测试-指示灯显示正常，蜂鸣器响声正常。人工确认后才停止显示和响'''
    global serialIdCode
    product.addBindingCode(u"PID","%.5d"%(serialIdCode+10))
    product.addBindingCode(u"中文","%.5d"%(serialIdCode+10))
    time.sleep(0.5)

    
def T_04_BatteryVoltage_A(product):
    u'''电池电路电压测试-返回电池电路电压值，后台根据配置判定'''
    global serialIdCode
    product.addBindingCode(u"EPC","%.5d"%(serialIdCode+100))
    time.sleep(0.5)
    return {u"槽思密达":product.productSlot}

@syntest
def T_05_anotherSoundLight_M(product):
    u'''又一个声光指示测试-指示灯显示正常，蜂鸣器响声正常。人工确认后才停止显示和响'''
    time.sleep(1)
    from hhplt.testengine.manul import manulCheck
    if manulCheck(u"声光指示测试", u"请确认槽位【%s】破玩意是正常亮了吗？"%product.productSlot):
        return {"随便写的返回值":300}
    else:
        raise TestItemFailException(failWeight = 10,message = u'声光测试失败')


