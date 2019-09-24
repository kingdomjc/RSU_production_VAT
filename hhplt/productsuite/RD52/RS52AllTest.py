#encoding:utf-8
u'''1、将已测试通过的RSDB5单板和RSRB4单板安装在底壳上（不盖上盖），连接RD52外部线缆整机上电开始测试；
2、安装RSAB9天线板后进行整机交易测试。
'''
import binascii
import os
import re
import socket
import struct
import telnetlib
import time

from hhplt.deviceresource import askForResource, TestResourceInitException
from hhplt.deviceresource.RD50CAutoTestMyd import MACProxy
from hhplt.deviceresource.RSUOpenAntenna import RSUTradeTest
from hhplt.deviceresource.checkVersion import VersionManager
from hhplt.deviceresource.codec_ff import EtcCodec

suiteName = u'''整机测试工位'''
version = "1.0"
failWeightSum = 5  #整体不通过权值，当失败权值和超过此，判定测试不通过



from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.parameters import PARAM, SESSION
from hhplt.testengine.manul import askForSomething
from hhplt.testengine.manul import manulCheck
from hhplt.testengine.server import ServerBusiness, serialCode
import RSRB4SendRecvTest, RSDB5AutoTest
#串口夹具开合触发器

#测试函数体例：T_<序号>_方法名
#_A为自动完成测试，_M为人工测试；函数正常完成，返回值为输出数据（可空）；异常完成，抛出TestItemFailException异常，含输出（可选）
#函数的doc中，<测试名称>-<描述>
#可选的两个函数:setup(product)和rollback(product)，前者用于在每次测试开始前（不管选择了多少个用例）都执行；后者当测试失败（总权值超出）后执行

# def __askForRD50CMAC():
#     '''获得工装板资源'''
#     sc = askForResource('RD50CMAC', MACProxy,
#                         integratedVatBoardIp = PARAM["defaultNetOneIp"])
#     return sc

# def __askForRSUTrade():
#     "RD50C控制板开关天线"
#     sc = askForResource('RD50CTrade', RSUTradeTest,
#                         integratedVatBoardIp=PARAM["RD50CToolingIp"],
#                         integratedVatBoardPort = PARAM["RD50CToolingPort"])
#     return sc
def setup(product):
    '''准备函数，可空'''
    SESSION["AllBarcode"] = ""


def finalFun(product):
    '''结束后输出'''
    pass

def pingIPOpen(pingIP):
    data = os.popen('ping %s'%pingIP).readlines()
    print data
    for line in data:
        if re.search(r'TTL=', line, re.I):
            return "ok"
    return "no"


def __checkManualFinished(idCode1,idCode2):
    '''检查数字单板人工手动工位已完成'''
    with ServerBusiness(testflow = True) as sb:
        status1 = sb.getProductTestStatus(productName="RD52_RSU", idCode = idCode1)
        status2 = sb.getProductTestStatus(productName="RD52_RSU", idCode = idCode2)
        if status1 is None:
            raise AbortTestException(message=u"RSDB5数字板尚未进行单板测试，整机测试终止")
        else:
            sn1 = RSDB5AutoTest.suiteName
            if sn1 not in status1["suiteStatus"] or status1["suiteStatus"][sn1] != 'PASS':
                raise AbortTestException(message=u"RSDB5的单板功能测试未进行或未通过，整机测试终止")

        if status2 is None:
            raise AbortTestException(message=u"RSRB4射频板尚未进行单板测试，整机测试终止")
        else:
            sn2 = RSRB4SendRecvTest.suiteName
            if sn2 not in status2["suiteStatus"] or status2["suiteStatus"][sn2] != 'PASS':
                raise AbortTestException(message=u"RSRB4的单板电源&单板功能测试测试项未进行或未通过，整机测试终止")




# def T_01_scanCode_A(product):
#     u'扫码条码-扫描条码'
#     global mac
#     barCode1 = askForSomething(u'扫描条码', u'请扫描RSDB5数字单板条码', autoCommit=False)
#     barCode2 = askForSomething(u'扫描条码', u'请扫描RSRB4射频单板条码', autoCommit=False)
#     barCode3 = askForSomething(u'扫描条码', u'请扫描整机条码', autoCommit=False)
#     __checkManualFinished(barCode1,barCode2)
#
#     product.setTestingSuiteBarCode(barCode1)
#     product.setTestingProductIdCode(barCode3)
#     mac = serialCode("mac")
#
#     return {u"RSDB5数字单板条码":barCode1, u"RSRB4射频单板条码":barCode2, u'整机条码':barCode3, u"MAC地址":mac}

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
        raise TestItemFailException(failWeight=10, message=u"读取mac失败")
    finally:
        proxy.close()

def myWriteMac(macstr):
    macoffset = 0x40
    proxy = MACProxy(PARAM["defaultNetOneIp"])
    try:
        macLast = binascii.unhexlify(macstr)
        proxy.writeEeprom(macoffset, macLast)
    except:
        raise TestItemFailException(failWeight=10, message=u"写入mac失败")
    finally:
        proxy.close()

def myWriteIp():
    ipoffset = 0x27
    proxy = MACProxy(PARAM["defaultNetOneIp"])
    ipstr = socket.inet_aton(PARAM["writeIP"])
    maskstr = socket.inet_aton(PARAM["writeMask"])
    gatewaystr = socket.inet_aton(PARAM["writeGateway"])
    try:
        proxy.writeEeprom(ipoffset, ipstr + maskstr + gatewaystr)
    except:
        raise TestItemFailException(failWeight=10, message=u"写入IP失败")
    finally:
        proxy.close()

def myCheckIp():
    ipoffset = 0x27
    proxy = MACProxy(PARAM["defaultNetOneIp"])
    try:
        rawip = proxy.readEeprom(ipoffset, 12)
    except:
        raise TestItemFailException(failWeight=10, message=u"读EEPROM失败")
    finally:
        proxy.close()
    ip = socket.inet_ntoa(rawip[0:4])
    mask = socket.inet_ntoa(rawip[4:8])
    gateway = socket.inet_ntoa(rawip[8:12])
    if ip + mask + gateway == PARAM["writeIP"] + PARAM["writeMask"] + PARAM["writeGateway"]:
        return "ok"
    return "no"

def T_01_saomiaoCode_A(product):
    u'扫描条码-RD52整机MAC写入测试'
    print "准备函数是否清空：", SESSION["AllBarcode"]
    barCode = askForSomething(u'扫描条码', u'请扫描整机条码', autoCommit=False)
    SESSION["AllBarcode"] = barCode
    product.setTestingProductIdCode(barCode)
    product.setTestingSuiteBarCode(barCode)

def T_02_MACTest_A(product):
    u'写入MAC-RD52整机MAC写入测试'
    if SESSION["AllBarcode"] == "":
        raise TestItemFailException(failWeight=10, message=u"未进行条码扫描，无法进行mac写入")
    for i in range(8):
        pingResult = pingIPOpen(PARAM["defaultNetOneIp"])
        if pingResult == "ok":
            break
        time.sleep(5)
    else:
        raise TestItemFailException(failWeight=10, message=u"连接失败有可能是网口通信问题")
    time.sleep(3)
    with ServerBusiness(testflow=True) as sb:
        getMac = sb.getBindingCode(productName=u"RD52_RSU", idCode=SESSION["AllBarcode"], bindingCodeName=u"MAC")
        if getMac is not None and getMac != "":
            # macstrRead = myReadMac()
            # if macstrRead.upper() != getMac:
            myWriteMac(getMac)
            macstrRead2 = myReadMac()
            if macstrRead2.upper() == getMac:
                return {u"mac地址":u"mac地址写入成功，%s" % getMac}
            raise TestItemFailException(failWeight=10, message=u"写入与分配mac不一致，写入mac失败")
        #     else:
        #         return {u"mac地址":u"mac已存在"}
        else:
            raise TestItemFailException(failWeight=10, message=u"整机条码未绑定mac,请退回上一工位")

def resetCheckPing():
    ip = PARAM["defaultNetOneIp"]
    tn = telnetlib.Telnet(ip, port=23, timeout=10)
    tn.set_debuglevel(2)
    try:
        tn.read_until('login: ')
        tn.write('rsu_c\r')
        tn.read_until('Password: ')
        tn.write('shhic357\r')
        tn.write('reboot\r')
    except:
        return "noReboot"
    finally:
        time.sleep(2)
        tn.close()
    for i in range(5):
        pingResult = pingIPOpen(PARAM["writeIP"])
        if pingResult == "ok":
            break
        time.sleep(5)
    else:
        return "no"
    return "ok"

def T_03_IPTest_A(product):
    u'写入IP-RD52整机IP写入并重启'
    myWriteIp()
    myResult = myCheckIp()
    if myResult == "ok":
        pingResult = resetCheckPing()
        if pingResult == "ok":
            return {u"ip地址":u"ip地址写入成功"}
        elif pingResult == "noReboot":
            raise AbortTestException(message=u"rsu重启失败，请检查连接")
        raise TestItemFailException(failWeight=10, message=u"设备无法ping通IP")
    raise TestItemFailException(failWeight=10, message=u"写入IP不一致")

def tradeTest():
    rssiList = []
    macId = PARAM["frockMacId"]
    rd50cIp = PARAM["RD50CToolingIp"]
    tn = telnetlib.Telnet(rd50cIp, port=23, timeout=10)
    tn.set_debuglevel(2)
    try:
        tn.read_until('login: ')
        tn.write('rsu_c\r')
        tn.read_until('Password: ')
        tn.write('shhic357\r')
        tn.write('reboot\r')
    except:
        raise AbortTestException(message=u"工装控制器重启失败，请检查工装连接")
    finally:
        time.sleep(2)
        tn.close()

    # for i in range(10):
    #     pingResult = pingIPOpen(PARAM["defaultNetOneIp"])
    #     if pingResult == "ok":
    #         break
    #     time.sleep(5)
    # else:
    #     raise TestItemFailException(failWeight=10, message=u"连接失败有可能是网口通信问题")
    # tnRD52 = telnetlib.Telnet(PARAM["defaultNetOneIp"], port=23, timeout=10)
    # try:
    #     tnRD52.set_debuglevel(2)
    #     tnRD52.read_until('login: ')
    #     tnRD52.write('rsu_c\r')
    #     tnRD52.read_until('Password: ')
    #     tnRD52.write('shhic357\r')
    #     tnRD52.write('reboot\r')
    # except:
    #     raise TestItemFailException(failWeight=10, message=u"交易测试失败")
    # finally:
    #     time.sleep(2)
    #     tnRD52.close()
    for i in range(10):
        try:
            tn = telnetlib.Telnet(rd50cIp, port=23, timeout=10)
            tn.set_debuglevel(2)
            break
        except:
            time.sleep(10)
    else:
        raise AbortTestException(message=u"工装控制器连接失败，请检查工装")

    try:
        tn.read_until('login: ')
        tn.write('rsu_c\r')
        tn.read_until('Password: ')
        tn.write('shhic357\r')
        tn.write('cd opt\n')
        tn.write("cd bin\n")
        tn.write("logm scheduler:debug\n")
        time.sleep(3)
        x = tn.read_very_eager()
    except:
        raise AbortTestException(message=u"工装控制器连接失败，请检查工装")
    finally:
        tn.close()
    # try:
    #     tn.write('cd opt\n')
    #     tn.write("cd bin\n")
    #     tn.write("logm scheduler:debug\n")
    #     time.sleep(8)
    #     x = tn.read_very_eager()
    # except:
    #     raise AbortTestException(message=u"工装控制器连接失败，请检查工装")
    # finally:
    #     tn.close()

    for i in x.split("\n"):
        if "macid:%s trade end retcode:" % macId in i:
            rssiList.append(i[-5:].strip())
    print rssiList
    if len(rssiList) == 0:
        raise TestItemFailException(failWeight=10,message=u"交易失败，没有读到obu的MAC地址")
    rssiNewList = [int(j, 16) for j in rssiList]
    rssiResult = sum(rssiNewList) / len(rssiNewList)
    print rssiResult
    return rssiResult

def T_04_businessRSSITest_A(product):
    u"整机交易测试-交易过程中包括读取RSSI值测试"
    manulCheck(u'提示', u'请将RSU放置到指定位置，然后点击确定按钮开始整机交易测试', check="ok")
    manulResult = tradeTest()
    if manulResult > int(PARAM["tradeRSSILow"]) and manulResult < int(PARAM["tradeRSSIHigh"]):
        return {u"交易测试RSSI":u"%d"%manulResult}
    raise TestItemFailException(failWeight=10, message=u"交易测试失败，RSSI值：%d" % manulResult)