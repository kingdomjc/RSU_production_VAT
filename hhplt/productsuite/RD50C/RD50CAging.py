#encoding:utf-8
u'''RD50C老化测试
'''
import binascii
import os
import re
import socket
import struct
import telnetlib
import time

from hhplt.deviceresource import askForResource, TestResourceInitException
from hhplt.deviceresource.RD50CAutoTestMyd import MACProxy, PsamProxy
from hhplt.deviceresource.RSUOpenAntenna import RSUTradeTest
from hhplt.deviceresource.checkVersion import VersionManager
from hhplt.deviceresource.codec_ff import EtcCodec
from hhplt.productsuite.RD50C import lightBoard_test
from hhplt.testengine.testcase import superUiLog, uiLog

suiteName = u'''老化测试工位'''
version = "1.0"
failWeightSum = 5  #整体不通过权值，当失败权值和超过此，判定测试不通过



from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.parameters import PARAM
from hhplt.testengine.manul import askForSomething
from hhplt.testengine.manul import manulCheck
from hhplt.testengine.server import ServerBusiness, serialCode
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

def __checkManualFinished(idCode):
    '''检查数字单板人工手动工位已完成'''
    with ServerBusiness(testflow = True) as sb:
        status1 = sb.getProductTestStatus(productName="RD50C_RSU", idCode = idCode)
        if status1 is None:
            raise AbortTestException(message=u"尚未进行整机测试，老化测试终止")
        else:
            sn = lightBoard_test.suiteName
            if sn not in status1["suiteStatus"] or status1["suiteStatus"][sn] != 'PASS':
                raise AbortTestException(message=u"整机测试未通过，老化测试终止")

def T_01_scanCode_A(product):
    u'扫码条码-扫描条码'
    barCode = askForSomething(u'扫描条码', u'请扫描整机条码', autoCommit=False)
    __checkManualFinished(barCode)
    product.setTestingProductIdCode(barCode)
    product.setTestingSuiteBarCode(barCode)

def myWriteIp():
    ipoffset = 0x33
    ipoffset2 = 0x27
    proxy = MACProxy(PARAM["writeIP"])
    time.sleep(5)
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
    proxy = MACProxy(PARAM["writeIP"])
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
    u'网口1测试-RD52整机IP写入并重启'
    for i in range(8):
        pingResult = pingIPOpen(PARAM["writeIP"])
        if pingResult == "ok":
            break
        time.sleep(5)
    else:
        raise TestItemFailException(failWeight=10, message=u"连接失败有可能是网口通信问题")

    myWriteIp()
    myResult = myCheckIp()
    if myResult == "ok":
        pingResult = resetCheckPing()
        if pingResult == "ok":
            return {u"网口1": u"ip地址写入成功"}
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

def T_04_PSAMTest_A(product):
    u'PSAM卡接口测试-RSDB0单板连接RSIB0单板进行4个PSAM卡接口测试'
    errorList = []
    proxy = PsamProxy(PARAM["writeIP"])
    command = "00a4000002df01"
    try:
        for slot in range(4):
            ack = proxy.active(slot)
            if ack[0:4] != "e800":
                superUiLog(u"PSAM卡槽[%d]激活失败"%(slot+1) + ack)
                errorList.append(str(slot+1))
                continue
            else:
                superUiLog(u"PSAM卡槽[%d]激活成功"%(slot+1) + ack[4:])
                ackRead = proxy.exchangeApdu(slot, command)
                if ackRead[0:4] != "e900":
                    uiLog(u"命令执行失败 " + ack)
                else:
                    uiLog(u"命令执行成功 " + ack[4:])
    finally:
        proxy.close()
    if errorList != []:
        raise TestItemFailException(failWeight=10, message=u'PSAM卡槽%s激活失败' % ",".join(errorList))
    return