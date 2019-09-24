#encoding:utf-8
u'''本工位对数字板、射频板、整机条码进行绑定关系
'''
import re
import time

from hhplt.parameters import PARAM
from hhplt.productsuite.RD52 import RSDB5AutoTest, RSRB4SendRecvTest
from hhplt.testengine.exceptions import AbortTestException
from hhplt.testengine.manul import askForSomething
from hhplt.testengine.server import ServerBusiness, serialCode

suiteName = u'''绑定条码工位'''
version = "1.0"
failWeightSum = 5  #整体不通过权值，当失败权值和超过此，判定测试不通过

def __checkRSDB5Finished(idCode):
    '''检查数字单板功能测试已完成'''
    with ServerBusiness(testflow = True) as sb:
        status = sb.getProductTestStatus(productName="RD52_RSU", idCode = idCode)
        if status is None:
            raise AbortTestException(message=u"RSDB5数字板尚未进行单板测试，整机测试终止")
        else:
            sn = RSDB5AutoTest.suiteName
            if sn not in status["suiteStatus"] or status["suiteStatus"][sn] != 'PASS':
                raise AbortTestException(message=u"RSDB5的单板功能测试未进行或未通过，整机测试终止")

def __checkRSRB4Finished(idCode):
    '''检查射频单板功能测试已完成'''
    with ServerBusiness(testflow=True) as sb:
        status = sb.getProductTestStatus(productName="RD52_RSU", idCode=idCode)
        if status is None:
            raise AbortTestException(message=u"RSRB4射频板尚未进行单板测试，整机测试终止")
        else:
            sn = RSRB4SendRecvTest.suiteName
            if sn not in status["suiteStatus"] or status["suiteStatus"][sn] != 'PASS':
                raise AbortTestException(message=u"RSRB4的单板电源&单板功能测试测试项未进行或未通过，整机测试终止")

def __checkBarCode(barCode):
    '''检查整机条码扫描'''
    if re.match("^[0-9]{12}$", barCode) == None:return False
    if not barCode.startswith(PARAM["AllCodeFirst"]):return False
    return True

def T_01_scanCode_A(product):
    u'扫码条码-扫描条码'
    barCode1 = askForSomething(u'扫描条码', u'请扫描RSDB5数字单板条码', autoCommit=False)
    __checkRSDB5Finished(barCode1)
    barCode2 = askForSomething(u'扫描条码', u'请扫描RSRB4射频单板条码', autoCommit=False)
    __checkRSRB4Finished(barCode2)
    barCode3 = askForSomething(u'扫描条码', u'请扫描整机条码', autoCommit=False)
    while not __checkBarCode(barCode3):
        barCode3 = askForSomething(u"扫描条码", u"整机条码扫描错误，请重新扫描", autoCommit=False)

    product.setTestingProductIdCode(barCode3)
    product.setTestingSuiteBarCode(barCode1)

    with ServerBusiness(testflow=True) as sb:
        getMac = sb.getBindingCode(productName=u"RD52_RSU", idCode=barCode3, bindingCodeName=u"MAC")
        if getMac is not None and getMac != "":
            mac = getMac
        else:
            mac = serialCode(PARAM["macName"])
            if int(mac, 16) > int(PARAM["macMax"], 16):
                raise AbortTestException(message=u"MAC地址超出范围，没有可分配mac")
            product.addBindingCode(u"MAC", mac)

    # mac = serialCode(PARAM["macName"])
    # if int(mac, 16) > int(PARAM["macMax"], 16):
    #     raise AbortTestException(message=u"MAC地址超出范围，没有可分配mac")
    # product.addBindingCode(u"MAC", mac)

    return {u"RSDB5数字单板条码":barCode1, u"RSRB4射频单板条码":barCode2, u'整机条码':barCode3, u"MAC地址":mac}