#encoding:utf-8
u'''请将GS10单板与工装板相连接，检查接口是否松动，指示灯正常亮起。
检查无误后，合上夹具，测试将自动开始。（如果合上夹具后测试未启动，请检查软硬件连接，或手动点击开始测试）
'''


suiteName = u'''虚拟测试项'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过



from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.server import ServerBusiness
from hhplt.deviceresource import OBU_tc56
import time
from hhplt.deviceresource import TestResource, askForResource
from hhplt.testengine.server import serverParam as SP,serialCode
from hhplt.parameters import PARAM
import hhplt.testengine.manul as manul


#串口夹具开合触发器

#测试函数体例：T_<序号>_方法名
#_A为自动完成测试，_M为人工测试；函数正常完成，返回值为输出数据（可空）；异常完成，抛出TestItemFailException异常，含输出（可选）
#函数的doc中，<测试名称>-<描述>
#可选的两个函数:setup(product)和rollback(product)，前者用于在每次测试开始前（不管选择了多少个用例）都执行；后者当测试失败（总权值超出）后执行

def __getOBU_tc56():
    return askForResource("OBU_tc56", OBU_tc56)

def setup(product):
    '''准备函数，可空'''
    print u"这里做准备工作"
    print "slot="+product.productSlot
    manul.closeAsynMessage()
    pass

def rollback(product):
    '''回滚函数'''
    print u'这里做回滚工作'
    if product.getTestingProductIdCode() is not None:
        print u'拟回收MAC地址：'+product.getTestingProductIdCode()
        from hhplt.testengine.server import retrieveSerialCode
        retrieveSerialCode('mac',product.getTestingProductIdCode())

def finalFun(product):
    '''结束后输出'''
    if "boardResult" in PARAM and PARAM["boardResult"]:
        manul.broadcastTestResult(product)


def T_01_initFactorySetting_A(product):
    u'''出厂信息写入-出厂信息写入（包括MAC地址，唤醒灵敏度参数）'''
    from hhplt.testengine.manul import askForSomething
    from hhplt.testengine.server import serialCode
    mac = serialCode("mac")
    barCode = askForSomething(u"扫描条码", u"请扫描条码",autoCommit = False)
    product.setTestingSuiteBarCode(barCode)
    product.setTestingProductIdCode(mac)
    time.sleep(1)
    return {"扫描条码结果":barCode,"写入MAC地址":mac}

    
def T_02_testVerisonDownload_A(product):
    u'''测试版本下载-下载测试版本，自动判断是否下载成功'''
    from hhplt.testengine.manul import showAsynMessage,closeAsynMessage
    showAsynMessage(u"异步消息",u"这是个异步消息，3秒后自动关闭")
    time.sleep(3)
    closeAsynMessage()

#    product.setTestingProductIdCode("F40015A0")
#    raise TestItemFailException(failWeight = 3,message = u'测试版本下载失败')

def T_03_soundLight_M(product):
    u'''声光指示测试-指示灯显示正常，蜂鸣器响声正常。人工确认后才停止显示和响'''
    time.sleep(1)
    from hhplt.testengine.manul import manulCheck
    if manulCheck(u"声光指示测试", u"请确认这破玩意是正常亮了吗？"):
        return {"随便写的返回值":300}
    else:
        raise TestItemFailException(failWeight = 10,message = u'声光测试失败')
#        raise AbortTestException(message = u'服务端连接异常')
    
    
def T_04_BatteryVoltage_A(product):
    u'''电池电路电压测试-返回电池电路电压值，后台根据配置判定'''
    with ServerBusiness(testflow=True) as sb:
        pass
    product.addBindingCode(u"印刷卡号","88888")
    sl,sh = SP('gs11.deepStaticCurrent.low',2),SP('gs11.deepStaticCurrent.high',18)
    return {"sl":sl,"sh":sh}
    time.sleep(1)

    
    
    