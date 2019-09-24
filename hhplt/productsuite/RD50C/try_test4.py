#encoding:utf-8
u'''请将GS10单板与工装板相连接，检查接口是否松动，指示灯正常亮起。
检查无误后，合上夹具，测试将自动开始。（如果合上夹具后测试未启动，请检查软硬件连接，或手动点击开始测试）
'''
from hhplt.testengine.server import ServerBusiness

suiteName = u'''人工手动测试项目4'''
version = "1.0"
failWeightSum = 5  #整体不通过权值，当失败权值和超过此，判定测试不通过



from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.parameters import PARAM
import hhplt.testengine.manul as manul
from hhplt.testengine.manul import askForSomething
from hhplt.testengine.manul import manulCheck
import try_test3

#串口夹具开合触发器

#测试函数体例：T_<序号>_方法名
#_A为自动完成测试，_M为人工测试；函数正常完成，返回值为输出数据（可空）；异常完成，抛出TestItemFailException异常，含输出（可选）
#函数的doc中，<测试名称>-<描述>
#可选的两个函数:setup(product)和rollback(product)，前者用于在每次测试开始前（不管选择了多少个用例）都执行；后者当测试失败（总权值超出）后执行

def setup(product):
    '''准备函数，可空'''
    print u"这里做准备工作"
    #print "slot="+product.productSlot
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


def __checkManualFinished(idCode):
    '''检查数字单板人工手动工位已完成'''
    with ServerBusiness(testflow = True) as sb:
        status = sb.getProductTestStatus(productName="RD50C_RSU" ,idCode = idCode)
        if status is None:
            raise AbortTestException(message=u"该产品尚未进行人工手动测试1，自动化测试终止")
        else:
            sn1 = try_test3.suiteName
            if sn1 not in status["suiteStatus"] or status["suiteStatus"][sn1] != 'PASS':
                raise AbortTestException(message=u"该产品的单板测试项未进行或未通过，整机测试终止")


def T_01_scanCode_A(product):
    u'扫码条码4-扫描条码'
    barCode1 = askForSomething(u'扫描条码', u'请扫描单板条码', autoCommit=False)
    barCode2 = askForSomething(u'扫描条码', u'请扫描灯板条码', autoCommit=False)
    barCode3 = askForSomething(u'扫描条码', u'请扫描整机条码', autoCommit=False)
    barCode4 = askForSomething(u'扫描条码', u'请扫描MAC', autoCommit=False)
    product.setTestingProductIdCode(barCode3)
    __checkManualFinished(barCode2)
    product.setTestingSuiteBarCode(barCode4)
    product.addBindingCode(barCode3, barCode1)
    product.addBindingCode(barCode3, barCode2)
    return {u"扫描单板条码结果": barCode1,u"扫描灯板条码结果": barCode2,u"扫描整机条码结果": barCode3}

def T_02_mainPowerTest_M(product):
    u"电源网络短路测试4-RSDB5单板主输入电源及各分支电源网络是否短路测试"
    powerList = ['主电源24V输入', '5V']
    alist = []
    for power in powerList:
        powerResult = manulCheck(u'电路短路测试',u'%s电源网络是否正常'%power)
        if powerResult:
            continue
        alist.append(power)
    if alist:
        cir = ",".join(alist)
        raise TestItemFailException(failWeight=10, message=u'%s出现短路'%cir)
    return {u"电源网络短路测试":u"全部正常"}

def T_03_branchPowerTest_M(product):
    u"电源网络电压精度测试4-RSDB5单板上电后各电源网络电压精度测试"
    powerList = ['1.2V','1.0V']
    alist = []
    for i in powerList:
        powerResult = manulCheck(u"电压精度测试",u"%s 电压是否正常"%i)
        if powerResult:
            continue
        else:
            alist.append(i)
    if alist:
        cir = ",".join(alist)
        raise TestItemFailException(failWeight=10, message=u'%s电源网络电压不正常'%cir)
    return {u"所有分支电源网络":u"正常"}

def T_04_downloadEPLD_M(product):
    u"EPLD下载测试4-RSDB0单板EPLD下载测试"
    EPLDResult = manulCheck(u"EPLD下载测试",u"EPLD下载是否成功")
    if EPLDResult:
        return {u"EPLD下载测试":u"下载成功"}
    raise TestItemFailException(failWeight=10, message=u'EPLD下载失败')

def T_05_downloadBOOT_M(product):
    u"BOOT下载测试4-RSDB0单板BOOT下载测试"
    EPLDResult = manulCheck(u"BOOT下载测试", u"BOOT下载是否成功")
    if EPLDResult:
        return {u"EPLD下载测试": u"下载成功"}
    raise TestItemFailException(failWeight=10, message=u'BOOT下载失败')