#encoding:utf-8
u'''请将GS10单板与工装板相连接，检查接口是否松动，指示灯正常亮起。
检查无误后，合上夹具，测试将自动开始。（如果合上夹具后测试未启动，请检查软硬件连接，或手动点击开始测试）
'''


suiteName = u'''绑定'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.testengine.manul import askForSomething
from hhplt.testengine.server import serialCode

from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.server import ServerBusiness
import time

from hhplt.deviceresource import askForResource,GS10IOBoardDevice

#测试函数体例：T_<序号>_方法名
#_A为自动完成测试，_M为人工测试；函数正常完成，返回值为输出数据（可空）；异常完成，抛出TestItemFailException异常，含输出（可选）
#函数的doc中，<测试名称>-<描述>
#可选的两个函数:setup(product)和rollback(product)，前者用于在每次测试开始前（不管选择了多少个用例）都执行；后者当测试失败（总权值超出）后执行


def __checkAndPersistEsamId(idCode,esamId):
    '''检查并立即持久ESAMID的绑定关系'''
    with ServerBusiness() as sb:
        if not sb.checkAndPersistUniqueBindingCode(productName="MOCK PRODUCT" , idCode=idCode , 
                                                   bindingCodeName=u"ESAMID" , code = esamId):
            raise TestItemFailException(failWeight = 10,message = u'ESAMID重复',output={"ESAMID":esamId})  
        
def __unbindEsam(idCode):
    '''解除绑定关系'''
    with ServerBusiness() as sb:
        sb.unbindCode(productName="MOCK PRODUCT",idCode=idCode,bindingCodeName="ESAMID")

def setup(product):
    '''准备函数，可空'''
    print u"这里做准备工作"
    pass

def rollback(product):
    '''回滚函数'''
    print u'这里做回滚工作'
    if not (product.finishSmoothly and product.testResult):
        #如果测试失败，要解绑定ESAM关系
        __unbindEsam(product.getTestingProductIdCode())


def T_01_initFactorySetting_A(product):
    u'''出厂信息写入-出厂信息写入（包括MAC地址，唤醒灵敏度参数）'''
    mac = serialCode("mac")
    barCode = askForSomething(u"扫描条码", u"请扫描条码",autoCommit = False)
    product.setTestingSuiteBarCode(barCode)
    product.setTestingProductIdCode(mac)
    time.sleep(1)
    return {"扫描条码结果":barCode,"写入MAC地址":mac}

    
def T_02_testVerisonDownload_A(product):
    u'''测试版本下载-下载测试版本，自动判断是否下载成功'''
    esamid = askForSomething(u"测试输入", u"输入一个ESAMid用于绑定",autoCommit = False)
    __checkAndPersistEsamId(product.getTestingProductIdCode(),esamid)

def T_03_soundLight_M(product):
    u'''声光指示测试-指示灯显示正常，蜂鸣器响声正常。人工确认后才停止显示和响'''
    time.sleep(1)
    from hhplt.testengine.manul import manulCheck
    if manulCheck(u"声光指示测试", u"请确认这破玩意是正常亮了吗？"):
        return {"随便写的返回值":300}
    else:
        raise TestItemFailException(failWeight = 10,message = u'声光测试失败')
    
    
def T_04_BatteryVoltage_A(product):
    u'''电池电路电压测试-返回电池电路电压值，后台根据配置判定'''
    with ServerBusiness(testflow=True) as sb:
        pass
    product.addBindingCode(u"印刷卡号","88888")
    time.sleep(1)
    
    
    
    
    
    
    

    
    
    