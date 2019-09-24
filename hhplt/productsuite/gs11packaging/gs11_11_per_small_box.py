#encoding:utf-8
u'''
每小盒10个OBU产品进行包装
'''

suiteName = u'''每小盒10个包装'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.testengine.manul import askForSomething
from hhplt.testengine.autoTrigger import AutoStartStopTrigger 
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.server import ServerBusiness
import re
from hhplt.testengine.testcase import uiLog

#绑定工位的自动触发器
autoTrigger = AutoStartStopTrigger

def __scan_obu(product,index):
    nowBar = product.param["nowObuBarCode"]
    obuBar = askForSomething(u"扫描镭雕条码", u"请扫描第【%d】个位置的条码\r\n应当为:%d"%(index,nowBar),autoCommit = False)
    while int(obuBar) != nowBar:
        obuBar = askForSomething(u"扫描条码", u"装配错误，应当装配的产品镭雕条码为:%d"%nowBar,autoCommit = False)
    __checkObuTestStatus(obuBar)
    product.param["nowObuBarCode"] = product.param["nowObuBarCode"] + 1
    product.addBindingCode(u"位置%d镭雕条码"%index,obuBar)
    return {u"镭雕条码":obuBar}

def __checkObuTestStatus(laserCode):
    uiLog(u'正在检查镭雕码为【%s】的产品测试情况...'%laserCode)
    with ServerBusiness(testflow = True) as sb:
        idCode = sb.getProductIdByBindingCode(productName="GS11 OBU",codeName=u"镭雕条码",code=laserCode)
        status = sb.getProductTestStatus(productName="GS11 OBU" ,idCode = idCode)
        if status is None:
            raise AbortTestException(message=u"镭雕条码为【%s】的产品尚未测试，请勿包装！"%laserCode)
        
        for sn in (u"单板测试",u"整机测试",u"交易绑定工位测试项"):
            if sn not in status["suiteStatus"] or status["suiteStatus"][sn]=='UNTESTED':
                raise AbortTestException(message="镭雕条码为【%s】的产品的[%s]测试项尚未进行，请勿包装！"%(laserCode,sn))
            if status["suiteStatus"][sn] != 'PASS':
                raise AbortTestException(message="镭雕条码为【%s】的产品的[%s]测试项未通过，请勿包装！"%(laserCode,sn))

def T_01_scanBoxBarCode_M(product):
    u'''扫描盒体条码'''
    boxBarCode = askForSomething(u"扫描条码", u"请扫描箱体条码",autoCommit = False)
    if re.match("\d{18}", boxBarCode) is None:
        raise AbortTestException(message = u'扫描盒体条码错误')
    product.param["startBarCode"] = int(boxBarCode[:16])
    product.param["num"] = int(boxBarCode[-2:])
    product.param["nowObuBarCode"] = product.param["startBarCode"]
    product.setTestingProductIdCode(boxBarCode)

def T_02_scan_obu_M(product):
    u'''扫描并检查第1个OBU产品'''
    return __scan_obu(product,1)

def T_03_scan_obu_M(product):
    u'''扫描并检查第2个OBU产品'''
    return __scan_obu(product,2)

def T_04_scan_obu_M(product):
    u'''扫描并检查第3个OBU产品'''
    return __scan_obu(product,3)

def T_05_scan_obu_M(product):
    u'''扫描并检查第4个OBU产品'''
    return __scan_obu(product,4)

def T_06_scan_obu_M(product):
    u'''扫描并检查第5个OBU产品'''
    return __scan_obu(product,5)

def T_07_scan_obu_M(product):
    u'''扫描并检查第6个OBU产品'''
    return __scan_obu(product,6)

def T_08_scan_obu_M(product):
    u'''扫描并检查第7个OBU产品'''
    return __scan_obu(product,7)

def T_09_scan_obu_M(product):
    u'''扫描并检查第8个OBU产品'''
    return __scan_obu(product,8)

def T_10_scan_obu_M(product):
    u'''扫描并检查第9个OBU产品'''
    return __scan_obu(product,9)
    
def T_11_scan_obu_M(product):
    u'''扫描并检查第10个OBU产品'''
    return __scan_obu(product,10)
