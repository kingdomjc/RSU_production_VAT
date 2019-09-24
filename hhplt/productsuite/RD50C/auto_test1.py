#encoding:utf-8
u'''本工位测试前请先在测试PC上运行APP版本下载服务程序TFTPSRV.EXE；
1、被测RSDB0单板通过排线连接作为工装的RSIB0板（LED&PSAM卡面板）、测试串口线、网口连接网线；
2、RSDB0单板上电；
3、根据VAT提示按下单板上复位按钮S1；
4、面板灯测试项需人工观察判断面板灯运行情况。
'''
import socket

import serial

from hhplt.deviceresource.checkVersion import VersionManager
from hhplt.productsuite.RD50C import downloadEPLD
from hhplt.testengine.server import ServerBusiness

suiteName = u'''RSDB0单板功能测试工位'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过


import binascii
import os
import re
import telnetlib
from hhplt.deviceresource.RD50CAutoTestMyd import PsamProxy, DeviceProxy, RTCProxy, MACProxy, PCIEProxy
from hhplt.testengine.testcase import superUiLog, uiLog
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.deviceresource import RD50CDownloadNetMyd
import time
from hhplt.deviceresource import TestResource, askForResource
from hhplt.parameters import PARAM
import hhplt.testengine.manul as manul
from hhplt.testengine.manul import askForSomething, manulCheck
import manual_test

#串口夹具开合触发器

#测试函数体例：T_<序号>_方法名
#_A为自动完成测试，_M为人工测试；函数正常完成，返回值为输出数据（可空）；异常完成，抛出TestItemFailException异常，含输出（可选）
#函数的doc中，<测试名称>-<描述>
#可选的两个函数:setup(product)和rollback(product)，前者用于在每次测试开始前（不管选择了多少个用例）都执行；后者当测试失败（总权值超出）后执行


def __checkManualFinished(idCode):
    '''检查RSDB0单板电源&BOOT下载工位已完成'''
    with ServerBusiness(testflow = True) as sb:
        status = sb.getProductTestStatus(productName="RD50C_RSU" ,idCode = idCode)
        if status is None:
            raise AbortTestException(message=u"RSDB0尚未进行单板测试，RSDB0单板功能测试终止")
        else:
            sn1 = downloadEPLD.suiteName
            if sn1 not in status["suiteStatus"] or status["suiteStatus"][sn1] != 'PASS':
                raise AbortTestException(message=u"RSDB0单板电源&BOOT下载测试项未进行或未通过，RSDB0单板功能测试终止")

def pingIPOpen(pingIP):
    data = os.popen('ping %s' % pingIP).readlines()
    print data
    for line in data:
        if re.search(r'TTL=', line, re.I):
            return "ok"
    return "no"

def __doorDog():
    sc = __askForPlateDeviceCom()  # 获取资源GS10PlateDevice
    downNet = sc.doorDog()
    return downNet

def __askForPlateDeviceCom():
    '''获得工装板资源'''
    sc = askForResource('RD50CPlateDevice', RD50CDownloadNetMyd.GS10PlateDevice,
               serialPortName = PARAM["defaultCOMPort"],
               cableComsuption = 1)
    return sc

def __downloadVersion():
    sc = __askForPlateDeviceCom()  # 获取资源GS10PlateDevice
    versionFile = None
    downNet = sc.downloadVersion(version_file=versionFile)
    return downNet

def T_01_scanCode_A(product):
    u'扫码条码-扫描条码'
    barCode = askForSomething(u'扫描条码', u'请扫描RSDB0单板条码', autoCommit=False)
    __checkManualFinished(barCode)
    product.setTestingProductIdCode(barCode)
    product.setTestingSuiteBarCode(barCode)
    return {u"RSDB0单板条码": barCode}

def T_02_downloadNet1_A(product):
    u'单板网口测试-RSDB0单板网口通信功能及APP版本下载测试'
    retry = ""
    t = 0
    while True:
        t += 1
        powerResult = manulCheck(u'复位', u'%s请在点击确定按钮后，按下单板上的复位按键S1'%retry,check="ok")
        if powerResult:
            downNet = __downloadVersion()
            if downNet == "OK":
                return
            elif downNet == "loginfail":
                retry = "登录超时，请重新操作，"
                if t == 2:
                    raise TestItemFailException(failWeight=10, message=u'串口无打印')
            elif downNet == "TFTPfail":
                # retry = "TFTP开启失败，请重新操作，"
                # continue
                raise TestItemFailException(failWeight=10, message=u'APP版本下载失败, 可能是没有打开TFTP')
            else:
                raise TestItemFailException(failWeight=10, message=u'BOOT下载失败，未知异常')

def myReadMac():
    macoffset = 0x46
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
    macoffset = 0x46
    proxy = MACProxy(PARAM["defaultNetOneIp"])
    for i in range(25):
        try:
            print "读个看看%d" % i
            proxy.initResource()
            proxy.readEeprom(0x27, 12)
            break
        except:
            time.sleep(10)
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
    # sc = __askForCheckVersion()
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

def T_05_PSAMTest_A(product):
    u'PSAM卡接口测试-RSDB0单板连接RSIB0单板进行4个PSAM卡接口测试'
    errorList = []
    # proxy = __askForRD50CNet1()
    proxy = PsamProxy(PARAM["defaultNetOneIp"])
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
        PARAM["failNum"] = "1"
        raise TestItemFailException(failWeight=1, message=u'PSAM卡槽%s激活失败' % ",".join(errorList))
    return

def T_06_lightTest_M(protduct):
    u"面板灯接口测试-RSDB0单板连接RSIB0单板进行单板面板灯接口测试"
    LightDict = {"系统PWR":"长亮","系统RUN":"闪烁","系统SAM":"长亮"}
    alist = []
    for alight in LightDict:
        lightResult = manulCheck(u"面板灯接口测试", u"请观察%s灯是否%s"%(alight,LightDict[alight]))
        if lightResult:
            continue
        alist.append(alight)
    # proxy = __askForRD50CLight()
    proxy = DeviceProxy(PARAM["defaultNetOneIp"])
    try:
        epld_addr = int(str("da"), 16)
        epld_value = int(str("0"), 16)
        proxy._write_epld(epld_addr, epld_value)
        redlightResult = manulCheck(u"系统报警灯", u"请观察系统ALM灯是否闪烁,点击正常后ALM灯将会关闭")
        if redlightResult:
            epld_addr1 = int(str("da"), 16)
            epld_value1 = int(str("1"), 16)
            proxy._write_epld(epld_addr1, epld_value1)
        else:
            alist.append("系统ALM")
            epld_addr1 = int(str("da"), 16)
            epld_value1 = int(str("1"), 16)
            proxy._write_epld(epld_addr1, epld_value1)
        time.sleep(0.5)
        epld_addr1 = int(str("17c"), 16)
        epld_value1 = int(str("00"), 16)
        proxy._write_epld(epld_addr1, epld_value1)
        sixlightResult = manulCheck(u"led灯亮起提示", u"led灯ANT1-ANT6是否亮起，判断后会关闭led灯")
        if sixlightResult:
            epld_addr1 = int(str("17c"), 16)
            epld_value1 = int(str("3f"), 16)
            proxy._write_epld(epld_addr1, epld_value1)
        else:
            alist.append("ANT1-ANT6灯")
            epld_addr1 = int(str("17c"), 16)
            epld_value1 = int(str("3f"), 16)
            proxy._write_epld(epld_addr1, epld_value1)
    finally:
        proxy.close()
    if alist:
        cir = ",".join(alist)
        PARAM["failNum"] = "1"
        raise TestItemFailException(failWeight=1, message=u"%s测试不正常" % cir)
    return

def _T_07_PCIETest_A(product):
    u"PCIE测试-PCIE测试"
    proxy = PCIEProxy(PARAM["PCIEIp"])
    try:
        recvResult = proxy.sendPcie()
        print recvResult
    except:
        raise TestItemFailException(failWeight=10, message=u"PCIE测试失败")
    finally:
        proxy.close()

def T_07_carDetection_A(protduct):
    u"车检串口-车检串口"
    proxy = DeviceProxy(PARAM["defaultNetOneIp"])
    try:
        epld_addr = int(str("d4"), 16)
        epld_value = int(str("7"), 16)
        proxy._write_epld(epld_addr, epld_value)
        pullOutResult = manulCheck(u"提示", u"请再车检插口的工装接口插拔之后，点击确定")
        if pullOutResult:
            read_epld_addr = int(str("90"), 16)
            readResult = proxy._read_epld(read_epld_addr)
            readResult = hex(readResult)[2:]
            print readResult
            if readResult != "c0":
                proxy.close()
                PARAM["failNum"] = "1"
                raise TestItemFailException(failWeight=1, message=u"车检口测试失败，错误码%s"%readResult)
            epld_addr1 = int(str("d2"),16)
            epld_value1 = int(str("1"),16)
            epld_value2 = int(str("0"),16)
            proxy._write_epld(epld_addr1, epld_value1)
            time.sleep(0.5)
            proxy._write_epld(epld_addr1, epld_value2)
    finally:
        proxy.close()

def _T_08_serialPort_A(product):
    u"串口测试-串口测试"
    time.sleep(10)
    ip1 = PARAM["defaultNetOneIp"]
    tn = telnetlib.Telnet(ip1, port=23, timeout=10)
    try:
        tn.set_debuglevel(2)
        tn.read_until('login: ')
        tn.write('rsu_c\r')
        tn.read_until('Password: ')
        tn.write('shhic357\r')
        tn.read_until("#")
        tn.write('cat /dev/ttyS1 > myd.txt & \n')
        tn.read_until("#")

        se = serial.Serial(PARAM["serialPort"], 115200)
        for i in range(4):
            se.write("%s\n"%"mynameisco"*10)
        time.sleep(2)
        se.close()
        tn.write("wc -l myd.txt\n")
        b = tn.read_until("#", 4)
        l = b.split("\n")[1].strip()[0]
        print l
    except:
        raise AbortTestException(message=u"请检查工装连接是否正常")
    finally:
        tn.close()
    # for i in l:
    #     if "4 myd.txt" in i:
    #         return {u"串口测试": u"成功"}
    if int(l) > 0:
        return {u"串口测试": u"成功，%s"%l}
    else:
        raise TestItemFailException(failWeight=10, message=u'串口测试失败')

def T_09_RTCTest_A(product):
    u"RTC时钟测试-RSDB0单板RTC时钟时间设置测试"
    setList =[]
    tmList = []
    timeNow = time.localtime()
    set_year = int(timeNow[0])
    set_mon = int(timeNow[1])
    set_day = int(timeNow[2])
    set_wday = int(timeNow[6])
    set_hour = int(timeNow[3])
    set_min = int(timeNow[4])
    set_sec = int(timeNow[5])
    proxy = RTCProxy(PARAM["defaultNetOneIp"])
    try:
        proxy.rtc_init()
        proxy.rtc_set(set_year,set_mon,set_day,set_wday,set_hour,set_min,set_sec)
        setList.extend((set_year,set_mon,set_day,set_wday,set_hour,set_min,set_sec))
        ack = proxy.rtc_read()
    except:
        raise TestItemFailException(failWeight=1, message=u'RTC时钟设置失败')
    finally:
        proxy.close()
    rtc_time = binascii.hexlify(ack)
    ret = int(rtc_time[0:8], 16)
    tm_sec = int(rtc_time[8:16], 16)
    tm_min = int(rtc_time[16:24], 16)
    tm_hour = int(rtc_time[24:32], 16)
    tm_mday = int(rtc_time[32:40], 16)
    tm_mon = int(rtc_time[40:48], 16)
    tm_year = int(rtc_time[48:56], 16)
    tm_wday = int(rtc_time[56:64], 16)
    tmList.extend((tm_year, tm_mon, tm_mday, tm_wday, tm_hour, tm_min, tm_sec))
    print "tmList",tmList
    if ret == 0:
        print "get rtc time: %d-%d-%d,%d,%d:%d:%d \r\n" % (tm_year, tm_mon, tm_mday, tm_wday, tm_hour, tm_min, tm_sec)
    if setList == tmList:
        return
    else:
        PARAM["failNum"] = "1"
        raise TestItemFailException(failWeight=1, message=u'RTC时钟设置失败')

def T_10_doorDogTest_A(product):
    u"看门狗测试-RSDB0单板硬件看门狗测试"
    ip1 = PARAM["defaultNetOneIp"]
    tn = telnetlib.Telnet(ip1, port=23, timeout=10)
    try:
        tn.set_debuglevel(2)
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

