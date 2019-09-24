#encoding:utf-8
u'''验证MAC地址并重新进行交易绑定'''

suiteName = u'''MAC验证与重新交易测试项'''
version = "1.0"
failWeightSum = 10

from hhplt.productsuite.gs10 import trading
from hhplt.testengine.manul import manulCheck,askForSomething
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.exceptions import AbortTestException
import time
import os

alreadyIssuedPackage = set()

localRecordFile = os.path.dirname(os.path.abspath(__file__))+os.sep+"localdata\\local_record.txt"
localRecord = {}

def __writeToLocalRecord(mac,barCode,contractSerial):
    '''写入本地记录'''
    global localRecord
    localRecord[mac]=barCode
    f = open(localRecordFile,'a')
    f.write("%s,%s,%s\n"%(mac,barCode,contractSerial))
    f.close()


def __getAlreadyIssuedPackage():
    '''获取已发货的7000个的MAC集合'''
    global alreadyIssuedPackage
    if len(alreadyIssuedPackage) == 0:
        packageFile = os.path.dirname(os.path.abspath(__file__))+os.sep+"localdata\\already_issued.txt"
        f = open(packageFile)
        for line in f.readlines():
            alreadyIssuedPackage.add(line.strip())
        f.close()
    return alreadyIssuedPackage

def __getLocalRecordPackage():
    '''获取本地存在的已测过的Map{mac:barCode}'''
    global localRecord,localRecordFile
    if len(localRecord) == 0:
        f = open(localRecordFile)
        for line in f.readlines():
            ls = line.split(":")
            mac = ls[0].strip()
            bar = ls[1].strip()
            localRecord[mac] = bar
        f.close()
    return localRecord
    
def __checkIfMacInAlreadyIssued(mac):
    '''检查MAC地址是否在已发货的7000个中'''
    return mac in __getAlreadyIssuedPackage()

def __checkIfMacHasRetraded(mac,barCode,contractSerial):
    '''检查MAC是否已经在本地绑定过，如果没绑定过，就记录下来'''
    pkg = __getLocalRecordPackage()
    if mac in pkg :
        if barCode != pkg[mac]:
            return True
    else:
        __writeToLocalRecord(mac,barCode,contractSerial)


def T_01_scanBarCode_M(product):
    u'''扫描镭雕条码-扫描镭雕条码'''
    return trading.T_01_scanBarCode_M(product)

def T_02_readObuId_A(product):
    u'''读取OBU内部标识-通过发卡器读取OBUID并与镭雕条码进行绑定'''
    manulCheck(u"操作提示",u"请将整机放置在发卡器上，待绿灯闪烁后确定","ok")
    sc = trading.__askForTrader()
    for i in range(5):
        try:
            mac,contractSerial = sc.readObuId()
            uiLog(u'测试产品标识:'+mac)
            product.setTestingProductIdCode(mac)
            product.addBindingCode(u"合同序列号",contractSerial)
            uiLog(u'绑定合同序列号:'+contractSerial)
            product.param["contractSerial"] = contractSerial
            break
        except Exception,e:
            print e
            time.sleep(0.1)
    else:
        raise AbortTestException(u'获得OBUID失败:'+e.message)
    return {u"OBUID":mac}

#def T_02_readObuIdMock_A(product):
#    u'''读取OBU内部标识桩-通过发卡器读取OBUID并与镭雕条码进行绑定'''
#    mac = askForSomething(u"桩输入", u"写一个MAC进来",autoCommit=False)
#    product.setTestingProductIdCode(mac)

def T_03_checkMac_A(product):
    u'''检查读取到的MAC地址是否存在错误-检查该MAC地址是否与之前的OBU重复'''
    mac = product.getTestingProductIdCode()
    barCode = product.getTestingSuiteBarCode()
    contractSerial = product.param["contractSerial"]
    if __checkIfMacInAlreadyIssued(mac):
        uiLog(u'该MAC地址存在于已发货的7000个中')
        raise AbortTestException(u'该MAC地址存在于已发货的7000个中，请重新写入MAC')
    if __checkIfMacHasRetraded(mac,barCode,contractSerial):
        uiLog(u'该MAC地址已绑定其他镭雕码')
        raise AbortTestException(u'该MAC地址已绑定其他镭雕码，请重新写入MAC')
    
def T_04_trade_A(product):        
    u'''交易测试-模拟交易测试是否成功'''
    try:
        trading.T_03_trade_A(product)
    except Exception,e:
        raise AbortTestException(u'交易验证失败，请返修:'+e.message)
    
    
    
    
    
    
