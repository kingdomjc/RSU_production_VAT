#encoding:utf-8
u"主设备单板测试"

suiteName = u'''主设备单板测试'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过



from hhplt.testengine.manul import askForSomething,manulCheck
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.productsuite.rd40.RD40MSTestcase.Reader24G import Reader24G,Reader24G_Exception
from hhplt.testengine.server import serverParam as SP,serialCode,ServerBusiness
from hhplt.parameters import SESSION,PARAM
from hhplt.testengine.testcase import uiLog,superUiLog

from hhplt.testengine.testutil import WrappedPyUnitTestCase

import binascii,socket,struct,time

CURRENT_TESTING_READER = Reader24G()   #正在测试的阅读器
TC = WrappedPyUnitTestCase()

def setup(product): 
    global CURRENT_TESTING_READER
    try:
        CURRENT_TESTING_READER.open(0,SP("rd40.defaultClientIp","192.168.0.10",str),SP("rd40.defaultClientPort",5000,int))
    except Exception,e:
        raise AbortTestException(message = u'打开设备网口失败')

def finalFun(product):
    global CURRENT_TESTING_READER
    CURRENT_TESTING_READER.close()

def reader24GTestcase(testFun):
    #基于侯哥封装的用例的Reade24G的实际用例，标识此装饰器
    def reader24GTestcaseWrapped(product):
        try:
            return testFun(product)
        except Reader24G_Exception,e:
            raise TestItemFailException(failWeight = 10,message = u'用例测试失败'+e.msg)
    reader24GTestcaseWrapped.__doc__ = testFun.__doc__
    reader24GTestcaseWrapped.__name__ = testFun.__name__
    return reader24GTestcaseWrapped

def T_01_scanBarCode_M(product):
    u"扫描条码-扫描主设备条码"
    barCode = askForSomething(u"扫描条码", u"请扫描单板条码",autoCommit=False)
    product.setTestingSuiteBarCode(barCode)
    return {u"主单板条码":barCode}

def T_02_testLED_M(product):
    u"上电后判定LED是否闪亮-人工判断单板上电后，板上的LED闪亮"
    manulCheck(u"操作提示",u"请连接单板外围的线缆，连线完成后确定","ok")
    mcr = manulCheck(u"LED测试", u"请确认但板上的LED正常闪动")
    if not mcr:raise TestItemFailException(failWeight = 10,message = u'单板LED测试不通过')
    
@reader24GTestcase
def T_04_testEeprom_A(product):
    u"验证EEPROM-自动验证EEPROM读写是否正常"
    global CURRENT_TESTING_READER,TC
    reader = CURRENT_TESTING_READER
    for x in range(4):
        reader.writeEeprom(0*x, 32, "\x01\x02\x03\x04"*8)
        ret = reader.readEeprom(0*x, 32)
        TC.assertEqual(ret, "\x01\x02\x03\x04"*8,u"EEPROM验证失败")

@reader24GTestcase
def T_05_testNandFlash_A(product):
    u"测试NandFlash-自动验证Nan的Flash读写是否正常"
    global CURRENT_TESTING_READER
    CURRENT_TESTING_READER.testNandFlash()

@reader24GTestcase
def T_06_setDeviceSn_A(product):
    u"分配设备编号-自动分配全局唯一的设备编号"
    global CURRENT_TESTING_READER,TC
    ret = CURRENT_TESTING_READER.readDeviceSn()
    if not ret.startswith("FFFF"):
        uiLog(u"设备编号已分配:"+ret)
        product.setTestingProductIdCode(ret)
        return {u"设备编号":ret}
    else:
        deviceSn = serialCode("rd40.deviceSn")
        uiLog(u"分配新的设备编号:"+deviceSn)
        CURRENT_TESTING_READER.setDeviceSn(deviceSn)
        ret = CURRENT_TESTING_READER.readDeviceSn()
        TC.assertEqual(ret, deviceSn,u"DeviceSN读取验证失败")
        uiLog(u"设备编号写入DeviceSn成功")
        CURRENT_TESTING_READER.setAppDeviceId(deviceSn)
        ret = CURRENT_TESTING_READER.readAppDeviceId()
        TC.assertEqual(ret, deviceSn,u"AppDeviceId读取验证失败")
        uiLog(u"设备编号写入AppDeviceId成功")
        product.setTestingProductIdCode(ret)
        return {u"设备编号":ret}

@reader24GTestcase
def T_07_testRtc_A(product):
    u"RTC测试-自动测试RTC"
    global CURRENT_TESTING_READER,TC
    CURRENT_TESTING_READER.setRtc("\x14\x10\x08\x1a\x0c\x0d\x0e")
    time.sleep(2)
    ret = CURRENT_TESTING_READER.readRtc()
    TC.assertEqual(ret, "1410081a0c0d10")

@reader24GTestcase
def T_08_testRs485_A(product):
    u"RS485串口测试-测试RS485串口读写是否正常"
    global CURRENT_TESTING_READER,TC
    try:
        CURRENT_TESTING_READER.close()
        CURRENT_TESTING_READER.open(1, '', PARAM['readerSerialCom'])
        ret = CURRENT_TESTING_READER.queryServerIp()
        TC.assertNotEqual(ret, None)
        return {u"串口读取值":binascii.hexlify(ret)}
    finally:
        CURRENT_TESTING_READER.close()
        CURRENT_TESTING_READER.open(0,SP("rd40.defaultClientIp","192.168.0.10",str),SP("rd40.defaultClientPort",5000,int))

@reader24GTestcase
def T_09_testSendPower_A(product):
    u"发射功率测试-发射功率测试"
    global CURRENT_TESTING_READER,TC
    l,h = {},{}
    l[1],h[1], l[2],h[2], l[3],h[3], l[4],h[4], l[5],h[5] = \
        (int(x) for x in SP("rd40.master.powerLevelLimit","65,70,68,73,72,77,77,82,84,90",str).split(","))
    result = {}
    for level in range(1,6):
        ret = CURRENT_TESTING_READER.testSendPower(1, 2, level)
        TC.assertGreaterEqual(ret, l[level],u"级别%d功率超过下限，功率值:%d,下限:%d"%(level,ret,l[level]))
        TC.assertLessEqual(ret, h[level],u"级别%d功率超过上限，功率值:%d,上限:%d"%(level,ret,h[level]))
        result[u"%d级功率值"%level] = ret
    return result

@reader24GTestcase
def T_10_testRecvSensi_A(product):
    u"接收灵敏度测试-测试接收灵敏度"
    global CURRENT_TESTING_READER,TC
    recvSensiLevel = SP("rd40.master.recvSensiLevel",970,int)
    CURRENT_TESTING_READER.enterRecvSensi(1, 2)
    time.sleep(7)
    ret = CURRENT_TESTING_READER.getRecvSensiResult(1, 2)
    TC.assertGreaterEqual(ret,recvSensiLevel,u"接收值:%d，门限:%d"%(ret,recvSensiLevel))
    return {u"接收灵敏度测试结果":ret}
    
@reader24GTestcase
def T_11_initParams_A(product):
    u"设置初始参数-设置链路模式、判决间隔、DATT、RSSI、方向等参数并进行验证"
    global CURRENT_TESTING_READER,TC
    reader = CURRENT_TESTING_READER
    clm,ji,sd,sr,sdr = \
        SP("rd40.master.commLinkMode",0,int),  \
        SP("rd40.master.judgeInterval",30,int),    \
        SP("rd40.master.slaveDatt",0,int), \
        SP("rd40.master.slaveRssi",95,int),    \
        SP("rd40.master.slaveDirection",1,int)

    reader.setCommLink(clm)
    uiLog(u"设置链路方式:%d"%clm)
    
    reader.setJudgeInterval(ji)
    uiLog(u"设置判决间隔:%d"%ji)
    
    reader.setSlaveDatt(1,sd)
    uiLog(u"设置DATT:%d"%sd)
    
    reader.setSlaveRssi(1,sr)
    uiLog(u"设置RSSI:%d"%sr)
    
    reader.setSlaveDirection(1,sdr)
    uiLog(u"设置显示方向:%d"%sdr)
    
    ret = reader.querySlaveInfo(1)
    TC.assertEqual(ret[0:12], SP("rd40.master.slaveVerifyStr","0201005f1d01",str),u"参数设置验证失败")

    return {u"链路方式":clm,u"判决间隔":ji,u"DATT":sd,u"RSSI":sr,u"显示方向":sdr}


@reader24GTestcase
def T_12_setInitServerIp_A(product):
    u"设置初始服务IP-设置默认初始服务IP"
    global CURRENT_TESTING_READER,TC
    ip = SP("rd40.defaultServerIp","192.168.0.200",str)
    port = SP("rd40.defaultServerPort",5000,int)
    serverAddrStr = binascii.hexlify(socket.inet_aton(ip))
    CURRENT_TESTING_READER.setServerIp(serverAddrStr, port)
    ret = CURRENT_TESTING_READER.queryServerIp()
    addr = socket.inet_ntoa(ret[0:4])
    port = ord(ret[4])*256+ord(ret[5])
    TC.assertEqual(addr, ip)
    TC.assertEqual(port, port)
    return {u"初始服务IP":ip}

@reader24GTestcase
def T_13_setMac_A(product):
    u"设置MAC地址-设置初始MAC地址"
    global CURRENT_TESTING_READER,TC
    ret = CURRENT_TESTING_READER.readMacAddr()
    nowMac = binascii.hexlify(ret)
    
    with ServerBusiness(testflow = True) as sb:
        shouldMac = sb.getBindingCode(productName=u"KC-RD40-M",
                                      idCode=product.getTestingProductIdCode(),
                                      bindingCodeName=u"MAC")
    if shouldMac != "":
        if shouldMac == nowMac:
            uiLog(u"已分配过MAC地址")
            return {u"MAC地址":nowMac}
        else:
            uiLog(u"重写MAC地址:"+shouldMac)
            mac_addr = binascii.unhexlify(shouldMac)
            CURRENT_TESTING_READER.setMacAddr(mac_addr)
            ret = CURRENT_TESTING_READER.readMacAddr()
            TC.assertEqual(ret, mac_addr)
            product.addBindingCode(u"MAC",shouldMac)
            return {u"MAC地址":shouldMac}
    else:
        mac = serialCode("rd40.mac")
        uiLog(u"分配新的MAC地址:"+mac)
        mac_addr = binascii.unhexlify(mac)
        CURRENT_TESTING_READER.setMacAddr(mac_addr)
        ret = CURRENT_TESTING_READER.readMacAddr()
        TC.assertEqual(ret, mac_addr)
        product.addBindingCode(u"MAC",mac)
        return {u"MAC地址":mac}
    
@reader24GTestcase
def T_14_setDevceIp_A(product):
    u"设置初始IP-设置设备初始IP"
    global CURRENT_TESTING_READER,TC
    ip,mask,default_gateway = \
        SP("rd40.defaultDeviceIp","192.168.0.10",str),\
        SP("rd40.defaultDeviceMask","255.255.255.0",str),\
        SP("rd40.defaultDeviceGateway","192.168.0.1",str)
    ipAddrStr = binascii.hexlify(socket.inet_aton(ip))
    netMaskStr = binascii.hexlify(socket.inet_aton(mask))
    gatewayStr = binascii.hexlify(socket.inet_aton(default_gateway))
    CURRENT_TESTING_READER.setDeviceIp(ipAddrStr, netMaskStr, gatewayStr)
    device_ip = CURRENT_TESTING_READER.queryIpAddress()
    addr = socket.inet_ntoa(binascii.unhexlify(device_ip[0:8]))
    netmask = socket.inet_ntoa(binascii.unhexlify(device_ip[8:16]))
    gateway = socket.inet_ntoa(binascii.unhexlify(device_ip[16:24]))
    TC.assertEqual(addr, ip)
    TC.assertEqual(netmask, mask)
    TC.assertEqual(gateway, default_gateway)
    return {u"ip":ip,u"mask":mask,u"gateway":default_gateway}

@reader24GTestcase
def T_15_wholelyVerify_A(product):
    u"整体参数验证-对整体参数进行验证"
    global CURRENT_TESTING_READER,TC
    ret = CURRENT_TESTING_READER.queryMasterConfig()
    ip_addr = socket.inet_ntoa(ret[0:4])
    net_mask =  socket.inet_ntoa(ret[4:8])
    gate_way =  socket.inet_ntoa(ret[8:12])
    server_ip =  socket.inet_ntoa(ret[12:16])
    (server_port, ) = struct.unpack("!H", ret[16:18])
    (judge_time, ) = struct.unpack("!I", ret[18:22])
    comm_link = ord(ret[22])
    version = ret[23:]
    TC.assertEqual(ip_addr, SP("rd40.defaultDeviceIp","192.168.0.10",str))
    TC.assertEqual(net_mask, SP("rd40.defaultDeviceMask","255.255.255.0",str))
    TC.assertEqual(gate_way, SP("rd40.defaultDeviceGateway","192.168.0.1",str))
    TC.assertEqual(server_ip, SP("rd40.defaultServerIp","192.168.0.200",str))
    TC.assertEqual(server_port, SP("rd40.defaultServerPort",5000,int))
    TC.assertEqual(judge_time, SP("rd40.judgeInterval",30,int))
    TC.assertEqual(comm_link, SP("rd40.commLinkMode",0,int))



    