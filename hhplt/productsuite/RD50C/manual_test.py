#encoding:utf-8
u'''本工位需依据VAT弹窗内容手动对单板进行测试，每测试一项根据测试情况点击弹窗相应按钮记录测试结果。
1、请先使用万用表直接测量单板各电源网络是否存在短路现象；
2、连接24V主电源线，待单板上电后使用万用表直接测量各电源网络电压精度偏差应小于10%。
'''
import re
import time

suiteName = u'''RSDB0单板电源检测工位'''
version = "1.0"
failWeightSum = 5  #整体不通过权值，当失败权值和超过此，判定测试不通过



from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.parameters import PARAM
import hhplt.testengine.manul as manul
from hhplt.testengine.manul import askForSomething
from hhplt.testengine.manul import manulCheck
from hhplt.testengine.server import serverParam as SP

#串口夹具开合触发器

#测试函数体例：T_<序号>_方法名
#_A为自动完成测试，_M为人工测试；函数正常完成，返回值为输出数据（可空）；异常完成，抛出TestItemFailException异常，含输出（可选）
#函数的doc中，<测试名称>-<描述>
#可选的两个函数:setup(product)和rollback(product)，前者用于在每次测试开始前（不管选择了多少个用例）都执行；后者当测试失败（总权值超出）后执行

# def setup(product):
#     '''准备函数，可空'''
#     print u"这里做准备工作"
#     #print "slot="+product.productSlot
#     manul.closeAsynMessage()
#     pass
#
# def rollback(product):
#     '''回滚函数'''
#     print u'这里做回滚工作'
#     if product.getTestingProductIdCode() is not None:
#         print u'拟回收MAC地址：'+product.getTestingProductIdCode()
#         from hhplt.testengine.server import retrieveSerialCode
#         retrieveSerialCode('mac',product.getTestingProductIdCode())
#
# def finalFun(product):
#     '''结束后输出'''
#     if "boardResult" in PARAM and PARAM["boardResult"]:
#         manul.broadcastTestResult(product)

# def __checkBarCode(barCode):
#     '''检查整机条码扫描'''
#     if re.match("^[0-9]{16}$", barCode) == None:return False
#     if not barCode.startswith(SP("gs25.overall.barcodePrefix","2950000001",str)):return False
#     return True

def __checkBarCode(barCode):
    '''检查RSDB0条码扫描'''
    if re.match("^[0-9]{12}$", barCode) == None:return False
    if not barCode.startswith(PARAM["RSDB0CodeFirst"]):return False
    return True


def T_01_scanCode_A(product):
    u'扫码条码-扫描RSDB0单板条码'
    barCode = askForSomething(u'扫描条码', u'请扫描RSDB0单板条码', autoCommit=False)
    while not __checkBarCode(barCode):
        barCode = askForSomething(u'扫描条码', u'RSDB0单板条码扫描错误，请重新扫描', autoCommit=False)
    product.setTestingSuiteBarCode(barCode)
    product.setTestingProductIdCode(barCode)
    return {u"RSDB0单板条码":barCode}

def T_02_mainPowerTest_M(product):
    u"电源网络短路测试-RSDB0单板主输入电源及各分支电源网络是否短路测试"
    # powerList = ['主电源24V输入','TP2: 24V','TP3: 3.3V','TP4: 2.5V','TP5: 1.0V','TP6: 1.2V','TP7: 5.0V','TP8: 1.8V','TP62: 4.2V','TP64: 12V']
    # alist = []
    # for power in powerList:
    #     powerResult = manulCheck(u'电路短路测试',u'%s电源网络是否正常'%power)
    #     if powerResult:
    #         continue
    #     alist.append(power)
    # if alist:
    #     cir = ",".join(alist)
    #     raise TestItemFailException(failWeight=10, message=u'%s出现短路'%cir)
    # return
    powerStr = "主电源24V输入, TP2: 24V, TP3: 3.3V, TP4: 2.5V, TP5: 1.0V, TP6: 1.2V, TP7: 5.0V, TP8: 1.8V, TP62: 4.2V, TP64: 12V"
    powerResult = manulCheck(u"电路短路测试", u"%s电源网络是否正常"%powerStr)
    if powerResult:
        return
    raise TestItemFailException(failWeight=10, message=u'存在短路问题')

def T_03_branchPowerTest_M(product):
    u"电源网络电压精度测试-RSDB0单板上电后各电源网络电压精度测试"
    time.sleep(1)
    manulCheck(u'提示', u'请将RSDB0单板上电，并用万用表测量各分支电路电压精度，点ESC继续', check="nothing")
    # powerList = ['TP2: 24V','TP3: 3.3V','TP4: 2.5V','TP5: 1.0V','TP6: 1.2V','TP7: 5.0V','TP8: 1.8V','TP62: 4.2V','TP64: 12V']
    # alist = []
    # for i in powerList:
    #     powerResult = manulCheck(u"电压精度测试",u"%s 电压是否正常"%i)
    #     if powerResult:
    #         continue
    #     else:
    #         alist.append(i)
    # if alist:
    #     cir = ",".join(alist)
    #     raise TestItemFailException(failWeight=10, message=u'%s电源网络电压不正常'%cir)
    # return

    powerStr = "TP2: 24V, TP3: 3.3V, TP4: 2.5V, TP5: 1.0V, TP6: 1.2V, TP7: 5.0V, TP8: 1.8V, TP62: 4.2V, TP64: 12V"
    powerResult = manulCheck(u"电压精度测试", u"%s电压是否正常" % powerStr)
    if powerResult:
        return
    raise TestItemFailException(failWeight=10, message=u'存在电压异常问题')







