#encoding:utf-8
'''
Created on 2014-8-28
用于服务端的测试
@author: 张文硕
'''


from hhplt.parameters import SESSION,GLOBAL
from hhplt.testengine.server import ServerBusiness,serialCode,retrieveSerialCode,serverParam as SP
import time

class _WndMock:
    def emit(self,*p):
        for msg in p:
            print msg
        
GLOBAL["mainWnd"]=_WndMock()
SESSION["serverIp"] = "192.168.10.180"
SESSION["testor"] = "super"
#SESSION["serverIp"] = "192.168.1.179"


#with ServerBusiness() as sb:
#    print sb.markTestingProductFinishSuccessfully(productName="gs01",barCode="123123123")


#retrieveSerialCode('mac','F4000005')
#retrieveSerialCode('mac','F4000008')
#for i in range(5):
#    print serialCode("mac")
#retrieveSerialCode('mac','F4000005')
#retrieveSerialCode('mac','F4000008')
#for i in range(5):
#    print serialCode("mac")


sl,sh = SP('gs11.deepStaticCurrent.low',2),SP('gs11.deepStaticCurrent.high',18)
print sl,sh

#while True:
#    print serialCode("mac")
#    time.sleep(1)
    
    
#with ServerBusiness() as sb:
#    print u'根据条码查找标识',sb.getProductIdByBarCode(productName="GS10 OBU",barCode="910000100019")
#    print u'根据绑定码查找标识',sb.getProductIdByBindingCode(productName="MOCK PRODUCT",codeName=u"印刷卡号",code="88888")
#    print u'根据标识码查找测试结果',sb.getProductTestStatus(productName='MOCK PRODUCT',idCode='F400048A')
#    print u'标记测试集完成',sb.markTestingProductFinishSuccessfully(productName="MOCK PRODUCT",idCode='F400048A')
#    print u'再根据标识码查找测试结果',sb.getProductTestStatus(productName='GS10 OBU',idCode='F40041F3')

#with ServerBusiness() as sb:
#    try:
##        idCode = sb.getProductIdByBarCode(productName="GS10 OBU",barCode="910000100019")
#        idCode = sb.getProductIdByBindingCode(productName="GS10 OBU",codeName=u"镭雕条码",code="5001241411100009")
#    except ServerBusiness.NormalException,e:
#        idCode = None
#    print idCode
