#encoding:utf-8
u"""
模块: 海尔智能货架，天线测试
"""
from hhplt.deviceresource import askForResource
from hhplt.parameters import PARAM
from hhplt.productsuite.HrShelve.analyzerDeviceForHrReader import VectorNetworkAnalyzerForHrAntenna
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.localdb import writeProductToLocalDb
from hhplt.testengine.manul import askForSomething, manulCheck
from hhplt.testengine.server import serverParam as SP
from hhplt.testengine.testcase import uiLog

suiteName = u"天线测试"
version = "1.0"
failWeightSum = 10



def __getVNA():
    # 获得矢量网络分析仪
    return askForResource("VectorNetworkAnalyzerForHrDivider",  VectorNetworkAnalyzerForHrAntenna,
                          vectorNetworkAnalyzerIp = PARAM["vectorNetworkAnalyzerIp"],
                          vectorNetworkAnalyzerPort = PARAM["vectorNetworkAnalyzerPort"])


def setup(product):
    pass

def finalFun(product):
    writeProductToLocalDb(product,"antenna.db")

def T_01_scanBare_M(product):
    u"扫码条码-扫描单板条码"
    barCode = askForSomething(u"扫描条码", u"请扫描单板条码",autoCommit=False)
    while len(barCode) != 10:
        barCode = askForSomething(u"扫描条码", u"条码扫描错误，请重新扫描",autoCommit = False)
    product.setTestingSuiteBarCode(barCode)
    product.setTestingProductIdCode(barCode)
    product.addBindingCode(u"单板条码",barCode)
    return {u"单板条码":barCode}


def __T_markerJudge(product,s,freq,marker):
    title = u"marker%d"%marker
    res = {u"%s-S11值"%title:s,u"%s-频点位置"%title:freq}
    uiLog(u"Marker%d，频点:%.2fMHz，S11值:%.4fdB"%(marker,freq/1E6,s))
    product.addBindingCode(u"%s-S11值"%title,s)
    return res

def T_02_exteriorCheck_M(product):
    u"外观检查-检查螺钉插销是否完整"
    if not manulCheck(u"外观检查",u"请仔细检查天线外观，螺钉、插销等是否完整"):
        raise TestItemFailException(failWeight = 10,message = u'外观检查不合格')


def T_03_marker1_A(product):
    u"Marker1测试-频率12.8M"
    manulCheck(u"操作提示",u"请确认天线单板与矢网仪连接正确，点击OK开始测试","ok")
    vna = __getVNA()
    s,d2,freq = vna.readMarkerAntFreq(1,12800000)
    res = __T_markerJudge(product,s,freq,1)
    if not ( SP("hr.antenna.marker1.s.low",0) < s < SP("hr.antenna.marker1.s.high",0)):
        raise TestItemFailException(failWeight = 10,message = u'频点1-S值不合格',output=res)
    return res

def T_04_marker2_A(product):
    u"Marker2测试-频率13.32M"
    vna = __getVNA()
    s,d2,freq = vna.readMarkerAntFreq(2,13320000)
    res = __T_markerJudge(product,s,freq,2)
    if not ( SP("hr.antenna.marker1.s.low",0) < s < SP("hr.antenna.marker1.s.high",0)):
        raise TestItemFailException(failWeight = 10,message = u'频点2-S值不合格',output=res)
    return res

def T_05_marker3_A(product):
    u"Marker3测试-频率13.56M"
    vna = __getVNA()
    s,d2,freq = vna.readMarkerAntFreq(3,13560000)
    res = __T_markerJudge(product,s,freq,3)
    if not ( SP("hr.antenna.marker1.s.low",0) < s < SP("hr.antenna.marker1.s.high",0)):
        raise TestItemFailException(failWeight = 10,message = u'频点3-S值不合格',output=res)
    return res

def T_06_marker4_A(product):
    u"Marker4测试-频率13.8M"
    vna = __getVNA()
    s,d2,freq = vna.readMarkerAntFreq(4,13800000)
    res = __T_markerJudge(product,s,freq,4)
    if not ( SP("hr.antenna.marker1.s.low",0) < s < SP("hr.antenna.marker1.s.high",0)):
        raise TestItemFailException(failWeight = 10,message = u'频点4-S值不合格',output=res)
    return res

def T_07_marker4_A(product):
    u"Marker5测试-频率14.32M"
    vna = __getVNA()
    s,d2,freq = vna.readMarkerAntFreq(5,14320000)
    res = __T_markerJudge(product,s,freq,5)
    if not ( SP("hr.antenna.marker5.s.low",0) < s < SP("hr.antenna.marker5.s.high",0)):
        raise TestItemFailException(failWeight = 10,message = u'频点5-S值不合格',output=res)
    return res

def T_08_marker4_A(product):
    u"Marker6(最小频点)测试-最小频点测试"
    vna = __getVNA()
    s,d2,freq = vna.readMarker6()
    res = __T_markerJudge(product,s,freq,6)
    freq /= 1000000 #换算成MHz
    product.addBindingCode(u"marker6-频率值",freq)
    if not ( SP("hr.antenna.marker6.s.low",0) < s < SP("hr.antenna.marker6.s.high",0)):
        raise TestItemFailException(failWeight = 10,message = u'频点6-S值不合格',output=res)
    if not ( SP("hr.antenna.marker6.freq.low",0) < freq < SP("hr.antenna.marker6.freq.high",0)):
        raise TestItemFailException(failWeight = 10,message = u'6频点频率不合格',output=res)


