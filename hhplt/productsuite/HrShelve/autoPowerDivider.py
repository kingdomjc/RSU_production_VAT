#encoding:utf-8
u"""
模块: 海尔智能货架，功分器板测试
"""
from hhplt.deviceresource import askForResource
from hhplt.parameters import PARAM
from hhplt.productsuite.HrShelve.analyzerDeviceForHrReader import VectorNetworkAnalyzerForHrDivider
from hhplt.productsuite.HrShelve.powerDividerCtrl import PowerDividerCtrl
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.localdb import writeProductToLocalDb
from hhplt.testengine.manul import askForSomething, manulCheck
from hhplt.testengine.server import serverParam as SP
from hhplt.testengine.testcase import uiLog

suiteName = u"功分器自动测试"
version = "1.0"
failWeightSum = 10


def __getVNA():
    # 获得矢量网络分析仪
    return askForResource("VectorNetworkAnalyzerForHrDivider",  VectorNetworkAnalyzerForHrDivider,
                          vectorNetworkAnalyzerIp = PARAM["vectorNetworkAnalyzerIp"],
                          vectorNetworkAnalyzerPort = PARAM["vectorNetworkAnalyzerPort"])


def __getPDCtrl():
    # 获得功分器测试工装板资源
    return askForResource("PowerDividerCtrl",PowerDividerCtrl,
                          powerDividerCtrlCom=PARAM["powerDividerCtrlCom"])


def setup(product):
    pass

def finalFun(product):
    writeProductToLocalDb(product,"powerDivider.db")

def T_01_scanBare_M(product):
    u"扫码条码-扫描单板条码"
    barCode = askForSomething(u"扫描条码", u"请扫描单板条码",autoCommit=False)
    while len(barCode) != 10:
        barCode = askForSomething(u"扫描条码", u"条码扫描错误，请重新扫描",autoCommit = False)
    product.setTestingSuiteBarCode(barCode)
    product.setTestingProductIdCode(barCode)
    product.addBindingCode(u"单板条码",barCode)
    return {u"单板条码":barCode}

def __T_trace_A(product,port,trace,sType):
    u"Trace1测试-测试Trace1的2个值是否在合格范围内"
    vna =  __getVNA()
    loss,d2,freq = vna.readLossAndFreq(trace)
    title= u"端口%d-%s"%(port,sType)
    res = {   (u"%s回损" if sType in ("S11","S22") else u"%s差损")%title:loss}
    uiLog(u"%s，频点:%.2fMHz,回损:%.4fdB"%(title,freq/1E6,loss))
    if sType == "S21": product.addBindingCode(u"%s差损"%title,loss)
    elif sType == "S22": product.addBindingCode(u"%s回损"%title,loss)
    return res

# 端口：432165,公共：7
def __T_portTest_A(product,port):
    u"端口4测试-测试端口4的S11/S22/S21的值"
    __getPDCtrl().switchToPort(int(port))
    uiLog(u"切换矢网仪到端口%s"%port)

    res = {}
    res.update(__T_trace_A(product,port,1,"S11"))
    res.update(__T_trace_A(product,port,2,"S22"))
    res.update(__T_trace_A(product,port,3,"S21"))

    s22 = res[u"端口%d-S22回损"%port]
    s21 = res[u"端口%d-S21差损"%port]
    if not ( SP("hr.divider.port%d.S22.low"%port,0) < s22 < SP("hr.divider.port%d.S22.high"%port,0)):
        raise TestItemFailException(failWeight = 10,message = u'端口%d-S22回损值不合格'%port,output=res)

    if not ( SP("hr.divider.port%d.S21.low"%port,0) < s21 < SP("hr.divider.port%d.S21.high"%port,0)):
        raise TestItemFailException(failWeight = 10,message = u'端口%d-S21差损值不合格'%port,output=res)

    return res

def T_02_port4Test_A(product):
    u"端口4测试-测试端口4的S11/S22/S21的值"
    manulCheck(u"操作提示",u"请确认功分器单板公共端（7）连接矢网仪1端口，1-6口与工装板连接正确，点击OK开始测试","ok")
    res = __T_portTest_A(product,4)
    # 加判S11
    s11 = res[u"端口4-S11回损"]
    product.addBindingCode(u"端口7-S11回损",s11)
    if not ( SP("hr.divider.port7.S11.low",0) < s11 < SP("hr.divider.port7.S11.high",0)):
        raise TestItemFailException(failWeight = 10,message = u'端口7-S11回损值不合格',output=res)
    return res


def T_03_port3Test_A(product):
    u"端口3测试-测试端口3的S11/S22/S21的值"
    return __T_portTest_A(product,3)

def T_04_port2Test_A(product):
    u"端口2测试-测试端口2的S11/S22/S21的值"
    return __T_portTest_A(product,2)

def T_05_port1Test_A(product):
    u"端口1测试-测试端口1的S11/S22/S21的值"
    return __T_portTest_A(product,1)

def T_06_port6Test_A(product):
    u"端口6测试-测试端口6的S11/S22/S21的值"
    return __T_portTest_A(product,6)

def T_07_port5Test_A(product):
    u"端口5测试-测试端口5的S11/S22/S21的值"
    return __T_portTest_A(product,5)





