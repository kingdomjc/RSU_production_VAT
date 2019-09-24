#encoding:utf-8
u'''1、请先依据VAT弹窗内容使用万用表直接测量单板各电源网络是否存在短路现象；
2、将电路测试正常的单板连接入RSRB4单板测试工装环境中后再继续后面的测试；
3、依据VAT弹窗内容使用万用表测试单板各电源网络电压，电压精度偏差应小于10%；
'''

suiteName = u'''RSRB4单板电源&单板功能测试工位'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过


import socket

from hhplt.deviceresource.RD52SingleTone import proxy, tx_pll, fpga_pll, rx_pll, proxyFrock
from hhplt.testengine.server import ServerBusiness
import binascii
import os
import re
import telnetlib
from hhplt.deviceresource.RD50CAutoTestMyd import PsamProxy, DeviceProxy, RTCProxy, MACProxy
from hhplt.testengine.testcase import superUiLog, uiLog
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.deviceresource import RD50CDownloadNetMyd
import time
from hhplt.deviceresource import TestResource, askForResource
from hhplt.parameters import PARAM
import hhplt.testengine.manul as manul
from hhplt.testengine.manul import askForSomething, manulCheck


#串口夹具开合触发器

#测试函数体例：T_<序号>_方法名
#_A为自动完成测试，_M为人工测试；函数正常完成，返回值为输出数据（可空）；异常完成，抛出TestItemFailException异常，含输出（可选）
#函数的doc中，<测试名称>-<描述>
#可选的两个函数:setup(product)和rollback(product)，前者用于在每次测试开始前（不管选择了多少个用例）都执行；后者当测试失败（总权值超出）后执行

def pingIPOpen(pingIP):
    data = os.popen('ping %s'%pingIP).readlines()
    print data
    for line in data:
        if re.search(r'TTL=', line, re.I):
            return "ok"
    return "no"
    # for i in data:
    #     if "TTL=" in i:
    #         return "ok"
    # else:
    #     return "no"
    # if "TTL=" not in data[2]:
    #     return "no"
    # elif "TTL=" in data[2]:
    #     return "ok"
def __checkBarCode(barCode):
    '''检查RSRB4条码扫描'''
    if re.match("^[0-9]{12}$", barCode) == None:return False
    if not barCode.startswith(PARAM["RSRB4CodeFirst"]):return False
    return True

def T_01_scanCode_A(product):
    u'扫码条码-扫描条码'
    barCode = askForSomething(u'扫描条码', u'请扫描RSRB4射频单板条码', autoCommit=False)
    while not __checkBarCode(barCode):
        barCode = askForSomething(u"扫描条码", u"RSRB4单板条码扫描错误，请重新扫描",autoCommit=False)
    product.setTestingProductIdCode(barCode)
    product.setTestingSuiteBarCode(barCode)
    return {u"扫描条码结果": barCode}

def T_02_mainPowerTest_M(product):
    u"电源网络短路测试-RSRB4单板主输入电源及各分支电源网络是否短路测试"
    # powerList = ['6V', '3.6V', '-5.5V', '5V(1)分支','5V(2)分支']
    # alist = []
    # for power in powerList:
    #     powerResult = manulCheck(u'电路短路测试',u'%s电源网络是否正常'%power)
    #     if powerResult:
    #         continue
    #     alist.append(power)
    # if alist:
    #     cir = ",".join(alist)
    #     raise TestItemFailException(failWeight=10, message=u'%s出现短路'%cir)
    # return {u"电源网络短路测试":u"全部正常"}
    powerStr = "6V, 3.6V, -5.5V, 5V(1)分支, 5V(2)分支"
    powerResult = manulCheck(u"电路短路测试", u'%s电源网络是否正常'%powerStr)
    if powerResult:
        return
    raise TestItemFailException(failWeight=10, message=u"存在短路问题")

def T_03_branchPowerTest_M(product):
    u"电源网络电压精度测试-RSRB4单板上电后各电源网络电压精度测试"
    time.sleep(1)
    manulCheck(u'提示', u'请将RSRB4单板上电，并用万用表测量各分支电路电压精度，点ESC继续', check="nothing")
    # powerList = ['-5.5V分支','5V(1)分支','5V(2)分支']
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
    # return {u"所有分支电源网络":u"正常"}
    powerStr = "-5.5V, 5V(1)分支, 5V(2)分支"
    powerResult = manulCheck(u"电压精度测试", u'%s电压是否正常' % powerStr)
    if powerResult:
        return
    raise TestItemFailException(failWeight=10, message=u"存在电压异常问题")


def FrockSendRSSI():
    try:
        proxyFrock.open(PARAM["defaultNetTwoIp"])
        proxyFrock._init_fpga()
        fpga_pll.config1()
        proxyFrock._write_fpga_reg(0x5a, 0x01)
        proxyFrock._write_fpga_reg(0x3e, 0x00)
        tx_pll.config1(5790)
        proxyFrock._write_fpga_reg(0x50, 0x02)
        proxyFrock._write_fpga_reg(0x51, 0x01)
        proxyFrock._write_fpga_reg(0x58, 0x01)
        proxyFrock._write_fpga_reg(0x59, 0x01)
        proxyFrock._write_fpga_reg(0x24, 0x47e)
        proxyFrock._write_fpga_reg(0x56, 0x38)
        proxyFrock._write_fpga_reg(0x57, 0x00)
        proxyFrock._write_fpga_reg(0x57, 0x01)
        proxyFrock._write_fpga_reg(0x57, 0x00)
        time.sleep(0.5)
    except Exception as e:
        raise AbortTestException(message=u"工装板异常")

def FrockRecvRSSI():
    fpga_addr = "3f"
    fpga_addr = int(str(fpga_addr), 16)
    try:
        fpga_value = proxyFrock._read_fpga_reg(fpga_addr)
    except:
        raise AbortTestException(message=u"工装板异常")
    RSSIValue = int(str(hex(fpga_value)[2:]), 16)
    print "RSSI:", RSSIValue
    return RSSIValue

def _T_04_simulationPowerTest_A(product):
    u"发射模拟控制功率测试-RSRB4单板发射模拟控制功率测试（MAX ,   MIN  2个值）"
    for i in range(10):
        pingResult = pingIPOpen(PARAM["defaultNetOneIp"])
        if pingResult == "ok":
            break
        time.sleep(5)
    else:
        raise TestItemFailException(failWeight=10, message=u"连接失败有可能是网口通信问题")

    k = float(str(PARAM["frockSlope"]))
    b = float(str(PARAM["frockB"]))
    damping = float(str(PARAM["frockDamping"]))
    error = float(str(PARAM["frockError"]))

    RSSIDict = {}
    try:
        # 打开工装接收
        proxyFrock.open(PARAM["defaultNetTwoIp"])
        fpga_pll.config1()
        proxyFrock._write_fpga_reg(0x5a, 0x01)
        rx_pll.config1(5762)
        proxyFrock._write_fpga_reg(0x59, 0x00)
        proxyFrock._write_fpga_reg(0x50, 0x01)
        proxyFrock._write_fpga_reg(0x51, 0x02)
        proxyFrock._write_fpga_reg(0x58, 0x01)
        proxyFrock._write_fpga_reg(0x56, 0x00)
        proxyFrock._write_fpga_reg(0x57, 0x00)
        proxyFrock._write_fpga_reg(0x57, 0x01)
        proxyFrock._write_fpga_reg(0x57, 0x00)
        proxyFrock._write_fpga_reg(0x52, 0x00)
        proxyFrock._write_fpga_reg(0x95, 0x03)
        proxyFrock._write_fpga_reg(0x96, 0x01)
        proxyFrock._write_fpga_reg(0x9b, 0x01)
        proxyFrock._write_fpga_reg(0x90, 0x01)
        time.sleep(2)

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
        MaxMaxValue = FrockRecvRSSI()
        sendPower1 = (MaxMaxValue - b) / k +error +damping
        MaxMaxKey = "MaxMax的发射功率为" + str(sendPower1)
        if sendPower1 > float(PARAM["xxLow"]) and sendPower1 < float(PARAM["xxHigh"]):
            RSSIDict[MaxMaxKey] = "通过"
        else:
            RSSIDict[MaxMaxKey] = "失败"

        # 模拟高，数字低
        proxy._write_fpga_reg(0x56, 0x24)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x57, 0x01)
        proxy._write_fpga_reg(0x57, 0x00)
        MaxMinValue = FrockRecvRSSI()
        sendPower2 = (MaxMinValue - b) / k +error +damping
        if sendPower2 > float(PARAM["xiLow"]) and sendPower2 < float(PARAM["xiHigh"]):
            RSSIDict["MaxMin的发射功率为" + str(sendPower2)] = "通过"
        else:
            RSSIDict["MaxMin的发射功率为" + str(sendPower2)] = "失败"

        # 模拟低，数字高
        proxy._write_fpga_reg(0x24, 0xa28)
        proxy._write_fpga_reg(0x56, 0x3c)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x57, 0x01)
        proxy._write_fpga_reg(0x57, 0x00)
        MinMaxValue = FrockRecvRSSI()
        sendPower3 = (MinMaxValue - b) / k +error +damping
        MinMaxKey = "MinMax的发射功率为" + str(sendPower3)
        if sendPower3 > float(PARAM["ixLow"]) and sendPower3 < float(PARAM["ixHigh"]):
            RSSIDict[MinMaxKey] = "通过"
        else:
            RSSIDict[MinMaxKey] = "失败"

        # 关闭待测单板单音
        proxy._write_fpga_reg(0x5a, 0x1)
        proxy._write_fpga_reg(0x58, 0x0)
        proxy._write_fpga_reg(0x59, 0x0)
        proxy._write_fpga_reg(0x46, 0x1)
        proxy._write_fpga_reg(0x3e, 0x0)
        proxy._write_fpga_reg(0x5a, 0x0)
        # 关闭工装单音
        proxyFrock._write_fpga_reg(0x5a, 0x1)
        proxyFrock._write_fpga_reg(0x58, 0x0)
        proxyFrock._write_fpga_reg(0x59, 0x0)
        proxyFrock._write_fpga_reg(0x46, 0x1)
        proxyFrock._write_fpga_reg(0x3e, 0x0)
        proxyFrock._write_fpga_reg(0x5a, 0x0)
    except Exception as e:
        raise AbortTestException(message=e)
    finally:
        proxy.close()
        proxyFrock.close()

    for i in RSSIDict:
        if RSSIDict[i] == "失败":
            PARAM["failNum"] = "1"
            message = "\n".join([a + ": " + RSSIDict[a] for a in RSSIDict])
            raise TestItemFailException(failWeight=1, message=unicode(message, "utf-8"))
    RSSIstr = ",".join([a for a in RSSIDict])
    return {RSSIstr:u"全部测试通过"}


def _T_05_RecvRSSITest_A(product):
    u"接收RSSI值测试-RSRB4单板射频信号接收RSSI值测试"
    try:
        proxy.open(PARAM["defaultNetOneIp"])
        fpga_pll.config()
        proxy._write_fpga_reg(0x5a, 0x01)
        rx_pll.config(5722)
        proxy._write_fpga_reg(0x59, 0x00)
        proxy._write_fpga_reg(0x50, 0x01)
        proxy._write_fpga_reg(0x51, 0x02)
        proxy._write_fpga_reg(0x58, 0x01)
        proxy._write_fpga_reg(0x56, 0x00)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x57, 0x01)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x52, 0x00)
        proxy._write_fpga_reg(0x95, 0x03)
        proxy._write_fpga_reg(0x96, 0x01)
        proxy._write_fpga_reg(0x9b, 0x01)
        proxy._write_fpga_reg(0x90, 0x01)
        time.sleep(0.5)
        # 工装发射单音
        FrockSendRSSI()
        fpga_addr = "3f"
        fpga_addr = int(str(fpga_addr), 16)
        fpga_value = proxy._read_fpga_reg(fpga_addr)
        print hex(fpga_value)[2:]

        proxyFrock._write_fpga_reg(0x5a, 0x1)
        proxyFrock._write_fpga_reg(0x58, 0x0)
        proxyFrock._write_fpga_reg(0x59, 0x0)
        proxyFrock._write_fpga_reg(0x46, 0x1)
        proxyFrock._write_fpga_reg(0x3e, 0x0)
        proxyFrock._write_fpga_reg(0x5a, 0x0)
        print "关闭工控单音"

        proxy._write_fpga_reg(0x5a, 0x1)
        proxy._write_fpga_reg(0x58, 0x0)
        proxy._write_fpga_reg(0x59, 0x0)
        proxy._write_fpga_reg(0x46, 0x1)
        proxy._write_fpga_reg(0x3e, 0x0)
        proxy._write_fpga_reg(0x5a, 0x0)
        print "关闭单音"

    except Exception as e:
        raise AbortTestException(message=e)
    finally:
        proxy.close()
        proxyFrock.close()
    print fpga_value
    if fpga_value > int(PARAM["recvRSSILow"]) and fpga_value < int(PARAM["recvRSSIHigh"]):
        return {u"RSSI值为：":fpga_value,u"16进制：":hex(fpga_value)[2:]}
    raise TestItemFailException(failWeight=10, message=u"RSSI测试不通过")