#encoding:utf-8
u'''1、组装整机（使用已测试RSDB0单板和全新未测试RSIB0单板），不盖外壳上盖板；
2、被测整机网口连接网线，4个PSAM卡槽插上PSAM卡；
3、被测整机上电。
'''

from hhplt.testengine.server import serialCode, ServerBusiness

suiteName = u'''整机测试工位'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过


import socket
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
from hhplt.parameters import PARAM, SESSION
import hhplt.testengine.manul as manul
from hhplt.testengine.manul import askForSomething, manulCheck
import auto_test1
#串口夹具开合触发器

#测试函数体例：T_<序号>_方法名
#_A为自动完成测试，_M为人工测试；函数正常完成，返回值为输出数据（可空）；异常完成，抛出TestItemFailException异常，含输出（可选）
#函数的doc中，<测试名称>-<描述>
#可选的两个函数:setup(product)和rollback(product)，前者用于在每次测试开始前（不管选择了多少个用例）都执行；后者当测试失败（总权值超出）后执行

def __askForRD50CMAC():
    '''获得工装板资源'''
    sc = askForResource('RD50CMAC', MACProxy,
                        integratedVatBoardIp = PARAM["defaultNetOneIp"])
    return sc

def __askForRD50CNet1():
    '''获得工装板资源'''
    sc = askForResource('RD50CPSAMTest', PsamProxy,
                        integratedVatBoardIp = PARAM["defaultNetOneIp"])
    return sc

def __askForRD50CLight():
    '''获得工装板资源'''
    sc = askForResource('RD50CLightTest', DeviceProxy,
                        integratedVatBoardIp = PARAM["defaultNetOneIp"])
    return sc

def pingIPOpen(pingIP):
    data = os.popen('ping %s'%pingIP).readlines()
    print data
    for line in data:
        if re.search(r'TTL=', line, re.I):
            return "ok"
    return "no"

def __checkManualFinished(idCode):
    '''检查RSDB0单板功能测试工位已完成'''
    with ServerBusiness(testflow = True) as sb:
        status = sb.getProductTestStatus(productName="RD50C_RSU" ,idCode = idCode)
        if status is None:
            raise AbortTestException(message=u"RSDB0尚未进行单板测试，整机测试终止")
        else:
            sn1 = auto_test1.suiteName
            if sn1 not in status["suiteStatus"] or status["suiteStatus"][sn1] != 'PASS':
                raise AbortTestException(message=u"RSDB0单板功能测试项未进行或未通过，整机测试终止")

def __checkBarCodeAll(barCode):
    '''检查整机条码扫描'''
    if re.match("^[0-9]{12}$", barCode) == None:return False
    if not barCode.startswith(PARAM["AllCodeFirst"]):return False
    return True

def myReadMac(macoffset):
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

def myWriteMac(macoffset,macstr):

    proxy = MACProxy(PARAM["defaultNetOneIp"])
    try:
        macLast = binascii.unhexlify(macstr)
        proxy.writeEeprom(macoffset, macLast)
    except:
        raise TestItemFailException(failWeight=10, message=u"写入mac失败")
    finally:
        proxy.close()

def T_01_scanAllCode_A(product):
    u'扫码条码并写入MAC-扫码单板、整机条码分配MAC并写入'
    barCode1 = askForSomething(u'扫描条码', u'请扫描RSDB0单板条码', autoCommit=False)
    __checkManualFinished(barCode1)
    barCode3 = askForSomething(u'扫描条码', u'请扫描整机条码', autoCommit=False)
    while not __checkBarCodeAll(barCode3):
        barCode3 = askForSomething(u"扫描条码", u"整机条码扫描错误，请重新扫描", autoCommit=False)
    product.setTestingProductIdCode(barCode3)
    product.setTestingSuiteBarCode(barCode1)
    with ServerBusiness(testflow=True) as sb:
        getMac = sb.getBindingCode(productName=u"RD50C_RSU", idCode=barCode3, bindingCodeName=u"MAC")
        if getMac is not None and getMac != "":
            mac = getMac
        else:
            mac = serialCode(PARAM["macName"])
            if int(mac, 16) > int(PARAM["macMax"], 16):
                raise AbortTestException(message=u"MAC地址超出范围，没有可分配mac")
            product.addBindingCode(u"MAC", mac)

        getMac2 = sb.getBindingCode(productName=u"RD50C_RSU", idCode=barCode3, bindingCodeName=u"MAC2")
        if getMac2 is not None and getMac2 != "":
            mac2 = getMac2
        else:
            mac2 = serialCode(PARAM["macName"])
            if int(mac2, 16) > int(PARAM["macMax"], 16):
                raise AbortTestException(message=u"MAC地址超出范围，没有可分配mac")
            product.addBindingCode(u"MAC2", mac2)


    for i in range(10):
        pingResult = pingIPOpen(PARAM["defaultNetOneIp"])
        if pingResult == "ok":
            break
        time.sleep(5)
    else:
        raise TestItemFailException(failWeight=10, message=u"连接失败有可能是网口通信问题")
    macoffset = 0x46
    myWriteMac(macoffset,mac)
    macstrRead = myReadMac(macoffset)

    macoffset2 = 0x40
    myWriteMac(macoffset2,mac2)
    macstrRead2 = myReadMac(macoffset2)

    if macstrRead.upper() == mac and macstrRead2.upper() == mac2:
        return {u"单板条码": barCode1, u"整机条码": barCode3, u"MAC1地址": mac, u"MAC2地址": mac2}
    else:
        TestItemFailException(failWeight=10, message=u"写入与分配mac不一致，写入mac失败")

def myWriteIp():
    ipoffset = 0x33
    ipoffset2 = 0x27
    proxy = MACProxy(PARAM["defaultNetOneIp"])
    ipstr = socket.inet_aton(PARAM["writeIP"])
    maskstr = socket.inet_aton(PARAM["writeMask"])
    gatewaystr = socket.inet_aton(PARAM["writeGateway"])

    ipstr2 = socket.inet_aton(PARAM["writeIP2"])
    maskstr2 = socket.inet_aton(PARAM["writeMask"])
    gatewaystr2 = socket.inet_aton(PARAM["writeGateway2"])
    try:
        proxy.writeEeprom(ipoffset, ipstr + maskstr + gatewaystr)
        proxy.writeEeprom(ipoffset2, ipstr2 + maskstr2 + gatewaystr2)
    except:
        raise TestItemFailException(failWeight=10, message=u"写入IP失败")
    finally:
        proxy.close()

def myCheckIp():
    ipoffset = 0x33
    ipoffset2 = 0x27
    proxy = MACProxy(PARAM["defaultNetOneIp"])
    try:
        rawip = proxy.readEeprom(ipoffset, 12)
        rawip2 = proxy.readEeprom(ipoffset2, 12)
    except:
        raise TestItemFailException(failWeight=10, message=u"读EEPROM失败")
    finally:
        proxy.close()

    ip = socket.inet_ntoa(rawip[0:4])
    mask = socket.inet_ntoa(rawip[4:8])
    gateway = socket.inet_ntoa(rawip[8:12])

    ip2 = socket.inet_ntoa(rawip2[0:4])
    mask2 = socket.inet_ntoa(rawip2[4:8])
    gateway2 = socket.inet_ntoa(rawip2[8:12])
    if ip + mask + gateway == PARAM["writeIP"] + PARAM["writeMask"] + PARAM["writeGateway"] and \
            ip2 + mask2 + gateway2 == PARAM["writeIP2"] + PARAM["writeMask"] + PARAM["writeGateway2"]:
        return "ok"
    return "no"

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

def T_02_IPTest_A(product):
    u'写入IP-RD52整机IP写入并重启'
    myWriteIp()
    myResult = myCheckIp()
    if myResult == "ok":
        pingResult = resetCheckPing()
        if pingResult == "ok":
            return {u"ip地址": u"ip地址写入成功"}
        elif pingResult == "noReboot":
            raise AbortTestException(message=u"rsu重启失败，请检查连接")
        raise TestItemFailException(failWeight=10, message=u"设备无法ping通IP")
    raise TestItemFailException(failWeight=10, message=u"写入IP不一致")

def T_03_IP2Test_A(product):
    u'网口2测试-网口2ping通测试'
    pingReslt = pingIPOpen(PARAM["writeIP2"])
    if pingReslt:
        return {u"网口2":u"测试通过"}
    raise TestItemFailException(failWeight=10, message=u"网口2测试失败")