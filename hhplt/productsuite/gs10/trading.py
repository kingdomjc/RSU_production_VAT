#encoding:utf-8
u'''交易工位，测试交易并绑定整机镭雕码'''

suiteName = u'''交易绑定工位测试项'''
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

localRecordFile = "localdata/local_record_"+ time.strftime('%Y-%m-%d',time.localtime(time.time()))+".txt"
localRecord = {}

def __writeToLocalRecord(mac,barCode,contractSerial):
    '''写入本地记录'''
    f = open(localRecordFile,'a')
    f.write("%s,%s,%s\n"%(mac,barCode,contractSerial))
    f.close()

def __askForTrader():
    '''获得交易资源(ZXRIS 8801)'''
    sc = askForResource('CpuCardTrader', CpuCardTrader.CpuCardTrader)
    return sc

def __checkTestFinished(idCode):
    '''检查产品测试已完成'''
    with ServerBusiness(testflow = True) as sb:
        status = sb.getProductTestStatus(productName="GS10 OBU" ,idCode = idCode)
        if status is None:
            raise AbortTestException(message=u"该产品尚未进行单板测试，整机测试终止")
        else:
            sn = overall_unit.suiteName;
            if sn not in status["suiteStatus"] or status["suiteStatus"][sn]=='UNTESTED':
                raise AbortTestException(message="该产品测试[%s]项尚未完成，绑定终止"%sn)
            if status["suiteStatus"][sn] != 'PASS':
                raise AbortTestException(message="该产品测试项[%s]不通过，绑定终止"%sn)

def setup(product):
    SESSION["isMend"] = False   #绑定工位不存在维修测试
    
def T_01_scanBarCode_M(product):
    u'''扫描镭雕条码-扫描镭雕条码'''
    barCode = askForSomething(u"扫描条码", u"请扫描镭雕条码",autoCommit=False)
    
    while re.match("X|[0-9]\d{15}", barCode) is None:
        barCode = askForSomething(u"扫描条码", u"条码扫描错误，请重新扫描",autoCommit = False)
        
    product.setTestingSuiteBarCode(barCode)
    product.addBindingCode(u"镭雕条码",barCode)
    return {u"镭雕条码":barCode}

def T_02_readObuId_A(product):
    u'''读取OBU内部标识-通过发卡器读取OBUID并与镭雕条码进行绑定'''
    manulCheck(u"操作提示",u"请将整机放置在发卡器上，待绿灯闪烁后确定","ok")
    sc = __askForTrader()
    for i in range(5):
        try:
            mac,contractSerial = sc.readObuId()
            uiLog(u'测试产品标识:'+mac)
            __checkTestFinished(mac)
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

def T_03_checkEsamDistrictCode_A(product):
    u'''验证ESAM匹配-验证地区分散码与整机条码'''
    sc = __askForTrader()
    pfx = product.getTestingSuiteBarCode()[:2]
    assertDisCode = SP("gs10.esamDistrictCode."+pfx,"D6D8C7EC",str)
    defaultDisCode = SP('gs10.esam.defaultDistrict','45544301',str)
    dc = sc.readEsamDistrictCode()
    uiLog(u"整机条码开头:%s,拟验证的地区分散码:%s,实际地区分散码:%s"%(pfx,assertDisCode,dc))
    if dc != defaultDisCode and dc != assertDisCode:
        raise TestItemFailException(failWeight = 10,message = u'地区分散码不匹配整机条码',output={u"地区分散码":dc})
    return {u"地区分散码":dc}

def T_04_initDf0107File_A(product):
    u'''初始化DF01文件-初始化DF01的07文件'''
    sc = __askForTrader()
    sc.initDf0107File()

def T_05_trade_A(product):
    u'''交易测试-模拟交易测试是否成功'''
    time.sleep(1)
    sc = __askForTrader()
    sc.testTrade()




