#encoding:utf-8
u'''请将GS10单板与工装板相连接，检查接口是否松动，指示灯正常亮起。
检查无误后，合上夹具，测试将自动开始。（如果合上夹具后测试未启动，请检查软硬件连接，或手动点击开始测试）
'''
import time

from hhplt.deviceresource.RD52SingleTone import proxy, fpga_pll, tx_pll
from hhplt.testengine.server import ServerBusiness, serialCode

suiteName = u'''人工手动测试项目1'''
version = "1.0"
failWeightSum = 5  #整体不通过权值，当失败权值和超过此，判定测试不通过



from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.parameters import PARAM
import hhplt.testengine.manul as manul
from hhplt.testengine.manul import askForSomething
from hhplt.testengine.manul import manulCheck


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
#
def __checkAutoFinished(idCode):
    '''检查RSDB0单板功能测试工位已完成'''
    with ServerBusiness(testflow = True) as sb:
        status = sb.getProductTestStatus(productName="RD52_RSU" ,idCode = idCode)
        if status is None:
            raise AbortTestException(message=u"RSDB5尚未进行单板功能测试，整机测试终止")
        else:
            sn = RSDB5AutoTest.suiteName
            if sn not in status["suiteStatus"] or status["suiteStatus"][sn] != 'PASS':
                raise AbortTestException(message=u"RSDB5单板功能测试项未进行或未通过，整机测试终止")

def T_01_scanCode_A(product):
    u'扫码条码1-扫描条码'
    barCode = askForSomething(u'扫描条码', u'请扫描RSDB5条码', autoCommit=False)
    __checkAutoFinished(barCode)
    product.setTestingSuiteBarCode(barCode)
    product.setTestingProductIdCode(barCode)

def T_02_simulationPowerTest_A(product):
    u"单板DAC电路测试-接入RSRB4单板发射模拟控制功率测试（MAX , MIN  2个值）"
    try:
        right = []
        error = []
        # 待测单板发射单音
        # 模拟高，数字高
        proxy.open(PARAM["defaultNetOneIp"])
        proxy._init_fpga()
        fpga_pll.config()
        proxy._write_fpga_reg(0x5a, 0x01)
        proxy._write_fpga_reg(0x3e, 0x00)
        tx_pll.config(5830)
        proxy._write_fpga_reg(0x50, 0x02)
        proxy._write_fpga_reg(0x51, 0x01)
        proxy._write_fpga_reg(0x58, 0x01)
        proxy._write_fpga_reg(0x59, 0x01)
        proxy._write_fpga_reg(0x24, 0x47e)
        proxy._write_fpga_reg(0x56, 0x3c)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x57, 0x01)
        proxy._write_fpga_reg(0x57, 0x00)
        time.sleep(0.5)

        MaxMax = manulCheck(u'提示', u'最大功率MaxMax')
        if MaxMax:
            right.append("最大功率")
        else:
            error.append("最大功率")
        # 模拟高，数字低
        proxy._write_fpga_reg(0x56, 0x24)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x57, 0x01)
        proxy._write_fpga_reg(0x57, 0x00)
        MaxMin = manulCheck(u'提示', u'衰减数字信号MaxMin')
        if MaxMin:
            right.append("衰减数字")
        else:
            error.append("衰减数字")

        # 模拟低，数字高
        proxy._write_fpga_reg(0x24, 0xa28)
        proxy._write_fpga_reg(0x56, 0x3c)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x57, 0x01)
        proxy._write_fpga_reg(0x57, 0x00)
        MinMax = manulCheck(u'提示', u'衰减模拟信号MinMax')
        if MinMax:
            right.append("衰减模拟")
        else:
            error.append("衰减模拟")

        # 关闭待测单板单音
        proxy._write_fpga_reg(0x5a, 0x1)
        proxy._write_fpga_reg(0x58, 0x0)
        proxy._write_fpga_reg(0x59, 0x0)
        proxy._write_fpga_reg(0x46, 0x1)
        proxy._write_fpga_reg(0x3e, 0x0)
        proxy._write_fpga_reg(0x5a, 0x0)



    except Exception as e:
        raise AbortTestException(message=e)
    finally:
        proxy.close()

    # rightStr = ",".join(right)
    # errorStr = ","
    # if error != []:
    #     raise TestItemFailException(failWeight=10, message=u"")




# barCode2 = 0
# def T_01_scanCode_A(product):
#     u'扫码条码1-扫描条码'
#     while True:
#         mac = serialCode(PARAM["macName"])
#         print mac
#         if int(mac,16) > int(PARAM["macMax"],16):
#             print "超过了"
#             break



# def T_01_scanCode_A(product):
#     u'扫码条码1-扫描条码'
#     barCode1 = askForSomething(u'扫描条码', u'请扫描MAC条码', autoCommit=False)
#     product.addBindingCode(u"MAC",barCode1)
#     product.setTestingSuiteBarCode(u"zhengji03")
#     product.setTestingProductIdCode(u"piduid03")
#
#
# def T_02_mainPowerTest_M(product):
#     u"电源网络短路测试1-RSDB5单板主输入电源及各分支电源网络是否短路测试"
#     with ServerBusiness(testflow=True) as sb:
#         status = sb.getProductTestStatus(productName=u"RD50C_RSU", idCode=u"piduid03")
#         if status is None:
#             print "新的，写mac,写版本号"
#             return
#         else:
#             aaa = sb.getBindingCode(productName=u"RD50C_RSU", idCode=u"piduid03", bindingCodeName=u"MAC")
#             if aaa is not None and aaa != "":
#                 if aaa == "mac03":
#                     print "该产品已经完成mac写入，并写入成功,进行下一步测试"
#                     return
#                 else:                                            #两种情况 1.idCode不存在 2.bindingCodeName不存在
#                     raise AbortTestException(message=u"mac写入错误")
#             else:
#                 raise AbortTestException(message=u"没有绑定mac")
#








    # print "合同:",bbb
#     powerList = ['主电源24V输入', '1.0V']
#     alist = []
#     for power in powerList:
#         powerResult = manulCheck(u'电路短路测试',u'%s电源网络是否正常'%power)
#         if powerResult:
#             continue
#         alist.append(power)
#     if alist:
#         cir = ",".join(alist)
#         PARAM["failNum"] = "1"
#         raise TestItemFailException(failWeight=1, message=u'%s出现短路'%cir)
#     return {u"电源网络短路测试":u"全部正常"}
#
# def T_03_branchPowerTest_M(product):
#     u"电源网络电压精度测试1-RSDB5单板上电后各电源网络电压精度测试"
#     powerList = ['5V','3.3V']
#     alist = []
#     for i in powerList:
#         powerResult = manulCheck(u"电压精度测试",u"%s 电压是否正常"%i)
#         if powerResult:
#             continue
#         else:
#             alist.append(i)
#     if alist:
#         cir = ",".join(alist)
#         raise TestItemFailException(failWeight=10, message=u'%s电源网络电压不正常'%cir)
#     return {u"所有分支电源网络":u"正常"}
#
# #====================================================================================================================
#
# def T_04_downloadEPLD_M(product):
#     u"EPLD下载测试1-RSDB0单板EPLD下载测试"
#     if PARAM["failNum"] == "1":
#         raise TestItemFailException(failWeight=10, message=u'灯板测试失败，请更换下一个灯板')
#     EPLDResult = manulCheck(u"EPLD下载测试",u"EPLD下载是否成功")
#     if EPLDResult:
#         return {u"EPLD下载测试":u"下载成功"}
#     PARAM["failNum"] = "1"
#     raise TestItemFailException(failWeight=1, message=u'EPLD下载失败')
#
# def T_05_downloadBOOT_M(product):
#     u"BOOT下载测试1-RSDB0单板BOOT下载测试"
#     EPLDResult = manulCheck(u"BOOT下载测试", u"BOOT下载是否成功")
#     if EPLDResult:
#         barCode1 = askForSomething(u'扫描条码', u'请扫描单板条码', autoCommit=False)
#         barCode3 = askForSomething(u'扫描条码', u'请扫描整机条码', autoCommit=False)
#         product.setTestingProductIdCode(barCode3)
#         product.setTestingSuiteBarCode("MAC1505")
#
#         return {u"单板条码":barCode1,u"灯板条码":barCode2,u"整机条码":barCode3,u"MAC":"MAC1505"}
#     PARAM["failNum"] = "1"
#     raise TestItemFailException(failWeight=1, message=u'BOOT下载失败')
