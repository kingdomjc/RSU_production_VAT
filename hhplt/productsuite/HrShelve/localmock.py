#encoding:utf-8
u"""
模块: 海尔智能货架，玩玩
"""
from hhplt.deviceresource import askForResource
from hhplt.parameters import PARAM
from hhplt.productsuite.HrShelve.analyzerDeviceForHrReader import VectorNetworkAnalyzerForHrAntenna
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.manul import askForSomething, manulCheck
from hhplt.testengine.server import serverParam as SP
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.localdb import writeProductToLocalDb

suiteName = u"玩玩"
version = "1.0"
failWeightSum = 10


def setup(product):
    pass

def finalFun(product):
    writeProductToLocalDb(product,"mockPr.db")

def T_01_scanBare_M(product):
    u"扫码条码-扫描单板条码"
    barCode = askForSomething(u"扫描条码", u"请扫描单板条码",autoCommit=False)
    while len(barCode) != 10:
        barCode = askForSomething(u"扫描条码", u"条码扫描错误，请重新扫描",autoCommit = False)
    product.setTestingSuiteBarCode(barCode)
    product.setTestingProductIdCode(barCode)
    product.addBindingCode(u"单板条码",barCode)
    return {u"单板条码":barCode}

def T_02_marker4_A(product):
    u"Marker6(最小频点)测试-最小频点测试"
    res = {u"端口1-S11回损":200}
    product.addBindingCode(u"端口1-S11回损",200)
    return res




