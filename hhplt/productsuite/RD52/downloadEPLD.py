#encoding:utf-8
u'''本工位需依据VAT弹窗内容手动对单板进行测试，每测试一项根据测试情况点击弹窗相应按钮记录测试结果。
'''
import re
import time

from hhplt.productsuite.RD52 import RSDB5ManualTest

suiteName = u'''RSDB5单板EPLD下载工位'''
version = "1.0"
failWeightSum = 5  #整体不通过权值，当失败权值和超过此，判定测试不通过



from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.parameters import PARAM
import hhplt.testengine.manul as manul
from hhplt.testengine.manul import askForSomething
from hhplt.testengine.manul import manulCheck
from hhplt.testengine.server import serverParam as SP, ServerBusiness


def __checkManualFinished(idCode):
    '''检查数字单板人工手动工位已完成'''
    with ServerBusiness(testflow = True) as sb:
        status = sb.getProductTestStatus(productName="RD52_RSU" ,idCode = idCode)
        if status is None:
            raise AbortTestException(message=u"该产品尚未进行RSDB5单板电源检测工位的测试，单板测试终止")
        else:
            sn1 = RSDB5ManualTest.suiteName
            if sn1 not in status["suiteStatus"] or status["suiteStatus"][sn1] != 'PASS':
                raise AbortTestException(message=u"该产品的RSDB5单板电源检测工位测试项未进行或未通过，单板测试终止")

def T_01_scanCode_A(product):
    u'扫码条码-扫描条码'
    barCode = askForSomething(u'扫描条码', u'请扫描RSDB5数字单板条码', autoCommit=False)
    __checkManualFinished(barCode)
    product.setTestingProductIdCode(barCode)
    product.setTestingSuiteBarCode(barCode)
    return {u"扫描条码结果": barCode}


def T_02_downloadEPLD_M(product):
    u"EPLD下载测试-RSDB5单板EPLD下载测试"
    EPLDResult = manulCheck(u"EPLD下载测试",u"EPLD下载是否成功",check = 'sucess')
    if EPLDResult:
        return {u"EPLD下载测试":u"下载成功"}
    raise TestItemFailException(failWeight=10, message=u'EPLD下载失败')

def T_03_downloadBOOT_M(product):
    u"BOOT下载测试-RSDB5单板BOOT下载测试"
    EPLDResult = manulCheck(u"BOOT下载测试", u"BOOT下载是否成功",check = 'sucess')
    if EPLDResult:
        return {u"EPLD下载测试": u"下载成功"}
    raise TestItemFailException(failWeight=10, message=u'BOOT下载失败')
