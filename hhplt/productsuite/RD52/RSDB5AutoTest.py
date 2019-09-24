#encoding:utf-8
u'''本工位测试前请先在测试PC上运行APP版本下载服务程序TFTPSRV.EXE；
1、被测RSDB5单板连接测试串口线、网口连接网线；
2、RSDB5单板上电；
3、根据VAT提示按下单板上复位按钮S1；
'''
import datetime

from hhplt.deviceresource.RD50CAutoTestMyd import MACProxy
from hhplt.deviceresource.RD52SendRegisterAgain import DeviceProxy
from hhplt.deviceresource.RD52SingleTone import proxy
from hhplt.deviceresource.checkVersion import VersionManager
from hhplt.productsuite.RD52 import downloadEPLD

suiteName = u'''RSDB5单板功能测试工位'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

import socket

from hhplt.deviceresource.RD52SingleTone import proxy, tx_pll, fpga_pll, rx_pll, proxyFrock
from hhplt.testengine.server import ServerBusiness
from os import path

import binascii
import os
import re
import telnetlib

from hhplt.testengine.testcase import superUiLog, uiLog
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.deviceresource import RD50CDownloadNetMyd
import time
from hhplt.deviceresource import TestResource, askForResource
from hhplt.parameters import PARAM
import hhplt.testengine.manul as manul
from hhplt.testengine.manul import askForSomething, manulCheck
import RSDB5ManualTest

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

# def pingIPOpen(pingIP):
#     data = os.popen('ping %s'%pingIP).readlines()
#     print data
#     if "TTL=" not in data[2]:
#         return "no"
#     elif "TTL=" in data[2]:
#         return "ok"
    # for line in data:
    #     if re.search(r'TTL=', line, re.I):
    #         return "ok"
    # return "no"

# def __askForRD52Power():
#     '''获得工装板资源'''
#     sc = askForResource('RD52Power', DeviceProxy,
#                         integratedVatBoardIp = PARAM["defaultNetOneIp"])
#     return sc

# def __askForTemperature():
#     "查看温度"
#     sc = askForResource('checkTemperature', DeviceProxy,
#                         integratedVatBoardIp=PARAM["defaultNetOneIp"])
#     return sc

# def __askForCheckVersion():
#     '''查找版本'''
#     sc = askForResource('checkVersion', VersionManager,
#                         integratedVatBoardIp = PARAM["defaultNetOneIp"])
#     return sc

def __askForPlateDeviceCom():
    '''获得工装板资源'''
    sc = askForResource('RD50CPlateDevice', RD50CDownloadNetMyd.GS10PlateDevice,
               serialPortName = PARAM["defaultCOMPort"],
               cableComsuption = 1)
    return sc

def __downloadVersion():
    sc = __askForPlateDeviceCom()  # 获取资源GS10PlateDevice
    versionFile = None
    downNet = sc.downloadVersion2(version_file=versionFile)
    return downNet

def __doorDog():
    sc = __askForPlateDeviceCom()  # 获取资源GS10PlateDevice
    downNet = sc.doorDog()
    return downNet

# def __askForVersion():
#     '''获得工装板资源'''
#     sc = askForResource('RD52AppVersion', VersionManager,
#                         integratedVatBoardIp=PARAM["defaultNetOneIp"])
#     return sc

def __checkManualFinished(idCode):
    '''检查数字单板人工手动工位已完成'''
    with ServerBusiness(testflow = True) as sb:
        status = sb.getProductTestStatus(productName="RD52_RSU" ,idCode = idCode)
        if status is None:
            raise AbortTestException(message=u"该产品尚未进行RSDB5单板EPLD下载工位的测试，单板测试终止")
        else:
            sn1 = downloadEPLD.suiteName
            if sn1 not in status["suiteStatus"] or status["suiteStatus"][sn1] != 'PASS':
                raise AbortTestException(message=u"该产品的RSDB5单板EPLD下载工位测试项未进行或未通过，单板测试终止")

def T_01_scanCode_A(product):
    u'扫码条码-扫描条码'
    barCode = askForSomething(u'扫描条码', u'请扫描RSDB5数字单板条码', autoCommit=False)
    __checkManualFinished(barCode)
    product.setTestingProductIdCode(barCode)
    product.setTestingSuiteBarCode(barCode)
    return {u"扫描条码结果": barCode}

def T_02_downloadNet1_A(product):
    u'单板网口测试-RSDB5单板网口通信功能及APP版本下载测试'
    retry = ""
    t = 0
    while True:
        t += 1
        powerResult = manulCheck(u'复位', u'%s请在点击确定按钮后，点击复位键'%retry,check="ok")
        if powerResult:
            downNet = __downloadVersion()
            if downNet == "OK":
                return {u"app版本":u"下载成功"}
            elif downNet == "loginfail":
                retry = "登录超时，请重新操作，"
                if t == 2:
                    raise TestItemFailException(failWeight=10, message=u'串口无打印')
            elif downNet == "TFTPfail":
                # retry = "TFTP开启失败，请重新操作，"
                # continue
                raise TestItemFailException(failWeight=10, message=u'BOOT下载失败，可能是没有打开TFTP')
            # elif downNet == "unknowRrror":
            else:
                raise TestItemFailException(failWeight=10, message=u'BOOT下载失败，未知异常')



# def T_02_downloadNet1_A(product):
#     u'单板网口1测试-RSDB5单板网口1（对外网口）通信功能及APP版本下载测试'
#     proxy = __askForVersion()
#     proxy.queryVersion()
#     sysVersionPath = path.abspath("C:\\Users\\MYD\\PycharmProjects\\RSU_LAST\\HHPLT\\hhplt\\productsuite\\RD52\\RD52_version\\sysversion")
#     proxy.downloadSysVersion(sysVersionPath)
#     appVersionPath = path.abspath("C:\\Users\\MYD\\PycharmProjects\\RSU_LAST\\HHPLT\\hhplt\\productsuite\\RD52\\RD52_version\\appversion")
#     proxy.downloadAppVersion(appVersionPath)
#     # 主备切换
#     proxy.switchVersion()
#     # 重启设备
#     proxy.rebootReader()
#     return {u"版本下载": u"成功"}

def myReadMac():
    macoffset = 0x40
    proxy = MACProxy(PARAM["defaultNetOneIp"])
    try:
        readMac = proxy.readEeprom(macoffset, 6)
        macstrRead = ""
        macstrRead += binascii.hexlify(readMac[0:1])
        macstrRead += binascii.hexlify(readMac[1:2])
        macstrRead += binascii.hexlify(readMac[2:3])
        macstrRead += binascii.hexlify(readMac[3:4])
        macstrRead += binascii.hexlify(readMac[4:5])
        macstrRead += binascii.hexlify(readMac[5:6])
        return macstrRead
    except:
        raise TestItemFailException(failWeight=10, message=u"读取mac失败，EEPROM测试失败")
    finally:
        proxy.close()

def myWriteMac(macstr):
    macoffset = 0x40
    proxy = MACProxy(PARAM["defaultNetOneIp"])
    for i in range(12):
        try:
            proxy.initResource()
            proxy.readEeprom(0x27, 12)
            break
        except:
            time.sleep(5)
    else:
        proxy.close()
        raise TestItemFailException(failWeight=10, message=u"建立连接失败，EEPROM测试失败")
    try:
        macLast = binascii.unhexlify(macstr)
        proxy.writeEeprom(macoffset, macLast)
    except:
        raise TestItemFailException(failWeight=10, message=u"写入mac失败，EEPROM测试失败")
    finally:
        proxy.close()

def T_03_MACTest_A(product):
    u'EEPROM测试-EEPROM读写测试'
    myWriteMac("A1A1A1A1A1A1")
    macstrRead2 = myReadMac()
    if macstrRead2.upper() == "A1A1A1A1A1A1":
        return {u"EEPROM测试":u"EEPROM读写成功"}
    raise TestItemFailException(failWeight=10, message=u"写入与分配mac不一致，EEPROM测试失败")

def T_04_checkVersionTest_A(product):
    u"查询版本号-查询版本号"
    sc = VersionManager(PARAM["defaultNetOneIp"])
    try:
        ret = sc.queryVersion()
    except:
        raise TestItemFailException(failWeight=1, message=u"版本获取失败")
    finally:
        sc.close()

    if ret["sysRuning"] == 0:
        sysVersion = ret["sys0VersionNum"]
        sysStandby = ret["sys1VersionNum"]
    else:
        sysVersion = ret["sys1VersionNum"]
        sysStandby = ret["sys0VersionNum"]
    return{u"应用版本号":ret["appRuningVersionNum"],u"系统版本号":sysVersion,u"备用系统版本号":sysStandby}

def T_05_temperatureTest_A(product):
    u"温度传感器测试-RSDB5单板温度传感器数据读取测试"
    time.sleep(8)
    sc = DeviceProxy(PARAM["defaultNetOneIp"])
    try:
        sc._init_sensor()
        localVaule = sc._get_local_temper()
        farVaule = sc._get_remote_temper()
    except:
        raise TestItemFailException(failWeight=10, message=u'温度传感器测试失败')
    finally:
        sc.close()

    if localVaule != 0 and farVaule != 0:
        return {u"本地温度": localVaule, u"远端温度": farVaule}
    raise TestItemFailException(failWeight=10, message=u'温度值不在范围内')

def FrockSendRSSI():
    proxyFrock.open(PARAM["defaultNetTwoIp"])
    try:
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
        proxyFrock._write_fpga_reg(0x56, int(PARAM["fpga56Reg"], 16))
        proxyFrock._write_fpga_reg(0x57, 0x00)
        proxyFrock._write_fpga_reg(0x57, 0x01)
        proxyFrock._write_fpga_reg(0x57, 0x00)
        time.sleep(0.5)
    except Exception as e:
        raise AbortTestException(message=u"工装板异常, %s"%e)
    finally:
        proxyFrock.close()


def FrockRecvRSSI():
    fpga_addr = "3f"
    fpga_addr = int(str(fpga_addr), 16)
    proxyFrock.open(PARAM["defaultNetTwoIp"])
    try:
        fpga_value = proxyFrock._read_fpga_reg(fpga_addr)
    except:
        raise AbortTestException(message=u"工装板异常")
    finally:
        proxyFrock.close()
    RSSIValue = int(str(hex(fpga_value)[2:]), 16)
    print "RSSI:", RSSIValue
    return RSSIValue

def T_06_simulationPowerTest_A(product):
    u"单板DAC电路测试-接入RSRB4单板发射模拟控制功率测试（MAX ,   MIN  2个值）"
    k = float(str(PARAM["frockSlope"]))
    b = float(str(PARAM["frockB"]))
    damping = float(str(PARAM["frockDamping"]))
    error = float(str(PARAM["frockError"]))
    power1 = {}
    power2 = {}
    power3 = {}
    RSSIDict = [power1,power2,power3]
    proxyFrock.open(PARAM["defaultNetTwoIp"])
    try:
        # 打开工装接收
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
        proxyFrock._write_fpga_reg(0x52, 0x14)
        proxyFrock._write_fpga_reg(0x95, 0x03)
        proxyFrock._write_fpga_reg(0x96, 0x01)
        proxyFrock._write_fpga_reg(0x9b, 0x01)
        proxyFrock._write_fpga_reg(0x90, 0x01)
        time.sleep(2)
    except Exception as e:
        raise AbortTestException(message=u"工装异常，请检查工装，%s" % e)
    finally:
        proxyFrock.close()

    proxy.open(PARAM["defaultNetOneIp"])
    try:
        # 待测单板发射单音
        # 模拟高，数字高
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
        MaxMaxKey = "最大发射功率为:" + str(round(sendPower1,2))
        if sendPower1 > float(PARAM["xxLow"]) and sendPower1 < float(PARAM["xxHigh"]):
            power1[MaxMaxKey] = "通过"
        else:
            power1[MaxMaxKey] = "失败"

        # 模拟高，数字低
        proxy._write_fpga_reg(0x56, 0x24)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x57, 0x01)
        proxy._write_fpga_reg(0x57, 0x00)
        time.sleep(0.5)
        MaxMinValue = FrockRecvRSSI()
        sendPower2 = (MaxMinValue - b) / k +error +damping
        differ2 = sendPower1 - sendPower2
        MaxMinKey = "数字衰减发射功率为:" + str(round(sendPower2,2)) + ", 与最大功率差值为:" + str(round(differ2,2))
        if differ2 > float(PARAM["xiLow"]) and differ2 < float(PARAM["xiHigh"]):
            power2[MaxMinKey] = "通过"
        else:
            power2[MaxMinKey] = "失败"

        # 模拟低，数字高
        proxy._write_fpga_reg(0x24, 0xa28)
        proxy._write_fpga_reg(0x56, 0x3c)
        proxy._write_fpga_reg(0x57, 0x00)
        proxy._write_fpga_reg(0x57, 0x01)
        proxy._write_fpga_reg(0x57, 0x00)
        time.sleep(0.5)
        MinMaxValue = FrockRecvRSSI()
        sendPower3 = (MinMaxValue - b) / k +error +damping
        differ3 = sendPower1 - sendPower3
        MinMaxKey = "模拟衰减发射功率为:" + str(round(sendPower3,2)) + ", 与最大功率差值为:" + str(round(differ3,2))
        if differ3 > float(PARAM["ixLow"]) and differ3 < float(PARAM["ixHigh"]):
            power3[MinMaxKey] = "通过"
        else:
            power3[MinMaxKey] = "失败"

        # 关闭待测单板单音
        proxy._write_fpga_reg(0x5a, 0x1)
        proxy._write_fpga_reg(0x58, 0x0)
        proxy._write_fpga_reg(0x59, 0x0)
        proxy._write_fpga_reg(0x46, 0x1)
        proxy._write_fpga_reg(0x3e, 0x0)
        proxy._write_fpga_reg(0x5a, 0x0)
    except Exception as e:
        PARAM["failNum"] = "1"
        raise TestItemFailException(failWeight=1, message=u"发射单音异常,%s" % e)
    finally:
        proxy.close()

        # 关闭工装单音
        # proxyFrock._write_fpga_reg(0x5a, 0x1)
        # proxyFrock._write_fpga_reg(0x58, 0x0)
        # proxyFrock._write_fpga_reg(0x59, 0x0)
        # proxyFrock._write_fpga_reg(0x46, 0x1)
        # proxyFrock._write_fpga_reg(0x3e, 0x0)
        # proxyFrock._write_fpga_reg(0x5a, 0x0)
    proxyFrock.open(PARAM["defaultNetTwoIp"])
    try:
        # 关闭接收
        proxyFrock._write_fpga_reg(0x5a, 0x1)
        proxyFrock._write_fpga_reg(0x46, 0x1)
        proxyFrock._write_fpga_reg(0x58, 0x0)
        proxyFrock._write_fpga_reg(0x5a, 0x0)
    except Exception as e:
        raise AbortTestException(message=u"工装异常，请检查工装，%s" % e)
    finally:
        proxyFrock.close()

    resultStr = ""
    for a in RSSIDict:
        for b in a:
            resultStr += b + "  " + a[b] + "\n"
    print resultStr

    for i in range(3):
        for j in RSSIDict[i]:
            if RSSIDict[i][j] == "失败":
                PARAM["failNum"] = "1"
                raise TestItemFailException(failWeight=1, message=u"%s"%resultStr)
    return {u"%s"%resultStr:u"全部通过"}

    # for i in RSSIDict:
    #     if RSSIDict[i] == "失败":
    #         PARAM["failNum"] = "1"
    #         message = "\n".join([a + ": " + RSSIDict[a] for a in RSSIDict])
    #         raise TestItemFailException(failWeight=1, message=unicode(message, "utf-8"))
    # RSSIstr = "\n".join([a for a in RSSIDict])
    # return {RSSIstr:u"全部测试通过"}

def T_07_RecvRSSITest_A(product):
    u"单板ADC电路测试-计算RSRB4单板接收射频信号的RSSI值测试"
    proxy.open(PARAM["defaultNetOneIp"])
    try:
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
        proxy._write_fpga_reg(0x52, 0x14)
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

        proxy._write_fpga_reg(0x5a, 0x1)
        proxy._write_fpga_reg(0x46, 0x1)
        proxy._write_fpga_reg(0x58, 0x0)
        proxy._write_fpga_reg(0x5a, 0x0)
        print "关闭接收"

    except Exception as e:
        PARAM["failNum"] = "1"
        raise TestItemFailException(failWeight=1, message=u"待测板接收异常，%s" % e)
    finally:
        proxy.close()

    proxyFrock.open(PARAM["defaultNetTwoIp"])
    try:
        proxyFrock._write_fpga_reg(0x5a, 0x1)
        proxyFrock._write_fpga_reg(0x58, 0x0)
        proxyFrock._write_fpga_reg(0x59, 0x0)
        proxyFrock._write_fpga_reg(0x46, 0x1)
        proxyFrock._write_fpga_reg(0x3e, 0x0)
        proxyFrock._write_fpga_reg(0x5a, 0x0)
        print "关闭工控单音"
    except Exception as e:
        raise AbortTestException(message=u"工装异常，请检查工装，%s" % e)
    finally:
        proxyFrock.close()

    if fpga_value > int(PARAM["recvRSSILow"]) and fpga_value < int(PARAM["recvRSSIHigh"]):
        return {u"接收RSSI值为：":fpga_value}
    else:
        PARAM["failNum"] = "1"
        raise TestItemFailException(failWeight=1, message=u"接收RSSI测试不通过,,值:%d:"%fpga_value)


def T_08_RecvRSSITest111_A(product):
    u"射频无输入接收-计算RSRB4单板无输入接收射频信号的RSSI值测试"
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

        proxy._write_fpga_reg(0x52, 0x7f)
        manulCheck(u'提示', u'请断开射频线缆', check="ok")
        fpga_addr2 = "3f"
        fpga_addr2 = int(str(fpga_addr2), 16)
        fpga_value2 = proxy._read_fpga_reg(fpga_addr2)
        print hex(fpga_value2)[2:]

        proxy._write_fpga_reg(0x5a, 0x1)
        proxy._write_fpga_reg(0x46, 0x1)
        proxy._write_fpga_reg(0x58, 0x0)
        proxy._write_fpga_reg(0x5a, 0x0)
        print "关闭接收"

    except Exception as e:
        raise AbortTestException(message=e)
    finally:
        proxy.close()

    if fpga_value2 > int(PARAM["recvNothingLow"]) and fpga_value2 < int(PARAM["recvNothingHigh"]):
        return {u"无输入接收RSSI值为：": fpga_value2}
    else:
        PARAM["failNum"] = "1"
        raise TestItemFailException(failWeight=1, message=u"无输入接收RSSI测试失败,值:%d:" % fpga_value2)


def T_09_doorDogTest_A(product):
    u"看门狗测试-RSDB5单板硬件看门狗测试"
    ip1 = PARAM["defaultNetOneIp"]
    tn = telnetlib.Telnet(ip1, port=23, timeout=10)
    tn.set_debuglevel(2)
    try:
        # 输入登录用户名
        tn.read_until('login: ')
        tn.write('rsu_c\r')
        # 输入登录密码
        tn.read_until('Password: ')
        tn.write('shhic357\r')
        # 登录完毕后执行命令
        tn.read_until("# ")
        tn.write('ps\n')
        psProcess = tn.read_until("/usr/bin/wtd")
        pslist = psProcess.split("\n")
        for oneProcess in pslist:
            if "usr/bin/wtd" in oneProcess:
                doorProcess = oneProcess.strip().split(" ")
                break
        else:
            raise TestItemFailException(failWeight=10, message=u'没有喂狗进程')
        tn.write("kill %s\n" % doorProcess[0])
        time.sleep(2)
    except:
        raise TestItemFailException(failWeight=10, message=u'看门狗测试失败')
    finally:
        tn.close()
    sc = __doorDog()
    if sc == "ok":
        return {u"看门狗测试":u"成功"}
    else:
        raise TestItemFailException(failWeight=10, message=u'看门狗失效')

