#encoding:utf-8
u'''
线下维修解绑定
用于解除绑定关系，当单板维修时需要更换ESAM等原件时，应首先使用此进行解绑定
'''

suiteName = u'''线下维修解绑定'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.testengine.manul import askForSomething
from hhplt.testengine.server import ServerBusiness
from hhplt.testengine.exceptions import AbortTestException
from hhplt.testengine.autoTrigger import AutoStartStopTrigger 

autoTrigger = AutoStartStopTrigger

def setup(product):
    
    pass

def T_01_scanBarCode_M(product):
    u'''扫描单板条码-扫描镭雕条码'''
    barCode = askForSomething(u"扫描条码", u"请扫描单板条码",autoCommit=False)
    product.setTestingSuiteBarCode(barCode)
    return {u"单板条码":barCode}

def T_02_getMacByBarCode_A(product):
    u'''根据单板条码查询MACID-根据单板条码查询MACID'''
    sb = ServerBusiness()
    sb.__enter__()
    try:
        mac = sb.getProductIdByBarCode(productName="GS11 OBU",suiteName="单板测试",barCode=product.getTestingSuiteBarCode())
    except ServerBusiness.NormalException,e:
        raise AbortTestException(message=u"没有此单板的测试结果")
    product.setTestingProductIdCode(mac)
    return {"MACID":mac}
    
def T_03_unbindAllCode_A(product):
    u'''解除单板绑定属性-解除单板的绑定属性'''
    with ServerBusiness() as sb:
        #ESAMID与GS10共用，因为需要两类产品共同比对
        sb.unbindCode(productName="GS10 OBU",idCode=product.getTestingProductIdCode(),bindingCodeName="ESAMID")
        sb.unbindCode(productName="GS11 OBU",idCode=product.getTestingProductIdCode(),bindingCodeName=u"合同序列号")
        sb.unbindCode(productName="GS11 OBU",idCode=product.getTestingProductIdCode(),bindingCodeName=u"镭雕条码")

