#encoding:utf-8
u"""版本下载及电流测试
"""
import serial
import time

from hhplt.deviceresource import TestResource, askForResource
from hhplt.deviceresource.RD52ReaderDevice import RD52ReaderDevice,TxPll,RxPll,MacCtrl
from hhplt.parameters import PARAM
from hhplt.testengine.server import serialCode,serverParam as SP,ServerBusiness, retrieveSerialCode
from hhplt.testengine.exceptions import TestItemFailException, AbortTestException
from hhplt.testengine.parallelTestSynAnnotation import serialSuite
from hhplt.testengine.server import serialCode
from hhplt.testengine.testcase import uiLog

suiteName = u"版本下载及电流测试"
version = "1.0"
failWeightSum = 10

import logging

logger = logging.getLogger()

VERSION_DOWNLOAD_STATES = {}

finished = 0

shouldNotRun = False    #若已超过生产，则不允许再测试了

@serialSuite
def setup(product):
    global finished,VERSION_DOWNLOAD_STATES,shouldNotRun
    if shouldNotRun: raise AbortTestException(u"CPCID已超过范围，产量已完成")

    board = __downloadBoard()
    antenna = __getRD52ReaderDevice()
    if finished == 0:
        VERSION_DOWNLOAD_STATES.update({k:False for k in range(1,17)})
        board.closeCylinder()
        board.closeAllChannel()
        time.sleep(0.5)
        antenna.open(PARAM["rd52_ipaddr"],PARAM["rd52_post"])
    product.param["versioned"] = False
    board.switchSampleResistance(product.productSlot,"0.4")

@serialSuite
def finalFun(product):
    global finished
    finished += 1
    logger.info("------------finish:%d"%finished)
    if finished == len(PARAM["productSlots"].split(",")) :  #全部完成
        __downloadBoard().openCylinder()
        __getRD52ReaderDevice().close()
        finished = 0

def rollback(product):
    pass
def __getRD52ReaderDevice():
    return askForResource("RD52ReaderDevice", RD52ReaderDevice, ipaddr=PARAM["rd52_ipaddr"],post=PARAM["rd52_post"])
def __downloadBoard():
    return askForResource("VersionDownloadBoard", VersionDownloadBoard,port = PARAM["downloadBoardCom"])

def _T_01_totalityVersionDownload_A(product):
    u"总体版本下载-首先尝试总体版本下载，对于下载失败的，后面补充下载"
    global finished
    if finished == 0:   #本批次首次下载，才执行总体下载指令
        succSlots,failSlots = __downloadBoard().downloadVersionForAllSlots()
        VERSION_DOWNLOAD_STATES.update({k:True for k in succSlots})
        VERSION_DOWNLOAD_STATES.update({k:False for k in failSlots})

    # 直接根据总体下载判定是否下载成功
    product.param["versioned"] = VERSION_DOWNLOAD_STATES[product.productSlot]
    #总体版本下载都判为成功，对于不成功者，下一步进行之


def T_02_versionDownloadRetry_A(product):
    u"版本补充下载-对于总体版本下载未成功的单板，进行补充下载"
    
    board = __downloadBoard()
    board.switchMode(product.productSlot,"poweroff")
    time.sleep(0.04)
    if not product.param["versioned"]:
        if not __downloadBoard().downloadVersionForSlot(product.productSlot):
            raise TestItemFailException(failWeight = 10,message = u"测试版本下载失败")
    board.switchMode(product.productSlot,"poweroff")
    time.sleep(0.02)
def T_03_serialTest_A(product):
    u"串口测试-测试CPC串口是否正常"
    board = __downloadBoard()
    board.switchMode(product.productSlot,"current")
    time.sleep(0.18)
    board.switchMode(product.productSlot,"serial")
    time.sleep(0.06)
    try:
        board.testSerial(product.productSlot)
    except TestItemFailException,e:
        # 进行一次电流补测
        __retestSerial(product)

def __retestSerial(product):
    # 串口补测
    board = __downloadBoard()
    try:
        board.switchMode(product.productSlot,"download") #切换到下载模式，使CPC复位
        time.sleep(0.18)
        board.switchMode(product.productSlot,"serial")
        time.sleep(0.02)
        board.testSerial(product.productSlot)
    except AbortTestException,e:
        # 如果有问题没有测出来，因为走到这里说明已经测试过串口，那么统一判为串口测试不通过
        raise TestItemFailException(failWeight=10,message=u"串口测试不通过")


def T_04_allotMac_A(product):
    u"分配MAC地址-从服务统一分配MAC"
    # 读MAC，检查之
    board = __downloadBoard()
    info40000 , info40040, info40080 = board.readInfo(product.productSlot)
    board.activeEsam(product.productSlot)
    targetMac = board.readMacFromEsam(product.productSlot,chooseDf01=True)

    mac = None
    # 检查MAC是否已经写过，如果写过，就不用分配了
    if info40000[:8] == "55555555":
        mac = info40000[8:16]
        if mac.upper().startswith(PARAM["macPrefix"]) and targetMac.upper() == mac.upper():
            uiLog(u"产品已测试过，原MAC:%s"%mac)
            product.param["retest"] = True
        else:
            mac = None
            product.param["retest"] = False

    if mac is None:
        mac = serialCode("cpc.mac")
        uiLog(u"new mac:%s"%mac);
        if mac > PARAM["endMac"]:
            global shouldNotRun
            shouldNotRun = True
            retrieveSerialCode("cpc.mac",mac)
            raise AbortTestException(u"MAC已超过范围，产量已完成")
        uiLog(u"分配新MAC:%s"%mac)
        product.param["retest"] = False

    mac = mac.upper()
    product.param["mac"] = mac
    product.setTestingProductIdCode(mac)
    product.addBindingCode("MAC",mac)
    return {"mac":mac}

def T_05_initEsam_A(product):
    u"初始化ESAM-针对非复测的板子，初始化ESAM"
    board = __downloadBoard()
    cpcId = PARAM["tempCpcId"]
    sn = cpcId[-8:]
    board.initEsam(product.productSlot,cpcId,sn)
    targetCpcId = board.readCpcId(product.productSlot)
    targetSn = board.readSn(product.productSlot)
    if cpcId.upper() != targetCpcId.upper() or sn.upper() != targetSn.upper():
        raise TestItemFailException(failWeight=10,message=u"初始化ESAM失败，目标写入的CPCID及SN与实际不符")
    # product.addBindingCode(u"临时SN",sn)
    # product.addBindingCode(u"临时CPCID",cpcId)
    return {u"临时SN":sn,u"临时CPCID":cpcId}

def T_06_initFactoryData_A(product):
    u"初始化出厂数据-出厂数据及MAC写入Flash"
    info40000 = SP("cpc.info40000","55555555000000000200020001000000",str)
    info40040 = SP("cpc.info40040","55555555011A090F2000020B0E05013C000302FF",str)
    info40080 = SP("cpc.info40080","0102",str)
    #将MAC写入到中间
    info40000 = info40000[:8] + product.param["mac"] + info40000[16:]
    board = __downloadBoard()

    uiLog(u"开始初始化单片机信息区")
    board.writeInfo(product.productSlot,info40000 , info40040, info40080)
    info40000_r , info40040_r, info40080_r = board.readInfo(product.productSlot)
    if info40000_r.upper() != info40000.upper() or info40040.upper() != info40040_r.upper() or info40080.upper() != info40080_r.upper():
        raise TestItemFailException(failWeight=10,message=u"初始化信息写入失败")

    uiLog(u"开始将MAC写入ESAM")
    board.writeMacToEsam(product.productSlot,product.param["mac"])
    targetMac = board.readMacFromEsam(product.productSlot,chooseDf01=False)
    if targetMac.upper() != product.param["mac"].upper():
        raise TestItemFailException(failWeight=10,message=u"MAC写入ESAM失败，读出结果不符")
    #检测ESAM是否成功创建目录
    t_esam = board.test_esam(product.productSlot)
    if t_esam == 0:
        uiLog(u"槽[%d] , 刷ESAM目录成功！" % int(product.productSlot))
    else:
        raise TestItemFailException(failWeight=10,message=u"刷ESAM目录失败！")
    return {"info40000":info40000 , "info40040":info40040, "info40080":info40080}
def T_07_monophonic_A(product):
    u"单音测试-测试RD52天线对CPC卡信号强度"
    antenna = __getRD52ReaderDevice()
    board = __downloadBoard()
    board.switchMode(product.productSlot, "poweroff")
    time.sleep(0.05)
    board.switchMode(product.productSlot, "serial")
    time.sleep(0.2)
    board.testSerial(product.productSlot)
    board.sendMonophonicTestCommandToTheCPC(product.productSlot)
    tx_pll = TxPll(antenna)
    #antenna.open(PARAM["rd52_ipaddr"])
    antenna._init_fpga()
    antenna.fpga_pll_config()
    antenna._write_fpga_reg(0x5a, 0x01)
    antenna._write_fpga_reg(0x3e, 0x00)
    tx_pll.config(PARAM["rd52_frequency"])
    antenna._write_fpga_reg(0x50, 0x02)
    antenna._write_fpga_reg(0x51, 0x01)
    antenna._write_fpga_reg(0x58, 0x01)
    antenna._write_fpga_reg(0x59, 0x01)
    antenna._write_fpga_reg(0x24, 0x47e)
    antenna._write_fpga_reg(0x56, 0x08)
    antenna._write_fpga_reg(0x57, 0x00)
    antenna._write_fpga_reg(0x57, 0x01)
    antenna._write_fpga_reg(0x57, 0x00)
    time.sleep(5)  #等待 RD52天线 发送单音测试
    antenna._write_fpga_reg(0x58, 0x00)
    antenna._write_fpga_reg(0x59, 0x00)
    sendMonophonicStopCommandToTheAntenna(antenna)
    data = board.stopAndResults(product.productSlot)
    detectingMonophonicResults(data)
def T_08_wake_A(product):
    u"BST唤醒测试-测试RD52天线对CPC卡唤醒功能"
    antenna = __getRD52ReaderDevice()
    board = __downloadBoard()
    board.switchMode(product.productSlot, "poweroff")
    time.sleep(0.05)
    board.switchMode(product.productSlot, "serial")
    time.sleep(0.2)
    board.testSerial(product.productSlot)
    board.sendWakeTestCommandToTheCPC(product.productSlot)
    sendBSTTestWakeupCommandToTheAntenna(antenna,PARAM["sendNumberOfWakes"],3)
    sendBSTStopCommandToTheAntenna(antenna)
    data = board.stopAndResults(product.productSlot)
    detectBSTResultsForWakeup(data, "唤醒", PARAM["detectNumberOfWakes"])
def T_09_receivingFrame_A(product):
    u"BST接收帧测试-测试RD52天线对CPC卡接收帧功能"
    antenna = __getRD52ReaderDevice()
    board = __downloadBoard()
    board.switchMode(product.productSlot, "poweroff")
    time.sleep(0.05)
    board.switchMode(product.productSlot, "serial")
    time.sleep(0.2)
    board.testSerial(product.productSlot)
    board.sendReceivingFrameTestCommandToTheCPC(product.productSlot)
    sendBSTTestFrameCommandToTheAntenna(antenna, PARAM["sendReceivingFrame"],6)
    sendBSTStopCommandToTheAntenna(antenna)
    data = board.stopAndResults(product.productSlot)
    detectBSTResults(data, "接收帧", PARAM["detectReceivingFrame"])
def T_10_currentTest_A(product):
    u"电流测试-电流测试"
    board = __downloadBoard()
    board.enterLowPowerMode(product.productSlot)
    time.sleep(0.6)
    board.switchMode(product.productSlot,"current")
    board.switchSampleResistance(product.productSlot,"20K")
    time.sleep(1)
    voltage = board.readVoltage(product.productSlot)
    readHighDC = 0
    try:
        # if not (SP("cpc.voltage.low",0) <= voltage <= SP("cpc.voltage.high",1500)):
            # raise TestItemFailException(failWeight=10,message=u"电流测试不通过，值%d，阈值%d-%d"%\
                                                          # (voltage,SP("cpc.voltage.low",0),SP("cpc.voltage.high",1500)))
        readHighDC = board.choiceCrruentBadSlot(product.productSlot)
        if readHighDC >= 60:
            raise TestItemFailException(failWeight = 10,message = u"电流波动大,02超限次数: %d" % readHighDC)                     
    finally:
        uiLog(u"槽[%d] , 测试版本超过门限电流的次数 : %d " % (int(product.productSlot),readHighDC))
        uiLog(u"槽[%d] , 测试版本瞬时电流输出 : %d " % (int(product.productSlot),voltage))
        board.switchSampleResistance(product.productSlot,"0.4")
        board.switchMode(product.productSlot,"download")
        time.sleep(0.02)
    return {u"电压":voltage}

def T_11_downloadFormalVersion_A(product):
    u"下载正式版本-下载正式版本"
    board = __downloadBoard()
    board.switchMode(product.productSlot,"poweroff")
    time.sleep(0.02) 
    if not __downloadBoard().downloadVersionForSlot(product.productSlot,versionType ="formal"):
            raise TestItemFailException(failWeight = 10,message = u"正式版本下载失败")
    board.switchMode(product.productSlot,"poweroff")
    time.sleep(0.02)
def T_12_workAppCurrentTest_A(product):
    u"正式版本电流测试-正式版本电流测试"
    board = __downloadBoard()
    board.switchMode(product.productSlot,"current")
    time.sleep(0.8)
    board.switchSampleResistance(product.productSlot,"20K")
    time.sleep(1)
    voltage = board.readVoltage(product.productSlot)
    readHighDC = 0
    try:
        # if not (SP("cpc.voltage.low",0) <= voltage <= SP("cpc.voltage.high",1500)):
            # raise TestItemFailException(failWeight=10,message=u"电流测试不通过，值%d，阈值%d-%d"%\
                                                          # (voltage,SP("cpc.voltage.low",0),SP("cpc.voltage.high",1500)))
        readHighDC = board.choiceCrruentBadSlot(product.productSlot)
        if readHighDC >= 60:
            raise TestItemFailException(failWeight = 10,message = u"电流波动大,01超限次数: %d" % readHighDC)
    finally:
        uiLog(u"槽[%d] , 正式版本超过门限电流的次数 : %d " % (int(product.productSlot),readHighDC))
        board.switchSampleResistance(product.productSlot,"0.4")
        board.switchMode(product.productSlot,"poweroff")
    return {u"正式版本电压":voltage}
def detectBSTResults(data,item,detectParam):
    # 分析CPC BST测试结果
    uiLog(u"CPC%s试结果:%s" %(item,int(data[-4:-2].encode("hex"),16)))
    c = int(data[-4:-2].encode("hex"),16) < detectParam
    if c: raise TestItemFailException(failWeight = 10,message=u"CPC%s测试结果值: %s" %(item,ord(data[-3])))
def detectBSTResultsForWakeup(data,item,detectParam):
    # 分析CPC BST测试结果
    uiLog(u"CPC%s试结果:%s" %(item,ord(data[-3])))
    c = ord(data[-3]) < detectParam
    if c: raise TestItemFailException(failWeight = 10,message=u"CPC%s测试结果值: %s" %(item,ord(data[-3])))
def sendMonophonicStopCommandToTheAntenna(antenna):
    antenna._write_fpga_reg(0x5a, 0x1)
    antenna._write_fpga_reg(0x58, 0x0)
    antenna._write_fpga_reg(0x59, 0x0)
    antenna._write_fpga_reg(0x46, 0x1)
    antenna._write_fpga_reg(0x3e, 0x0)
    antenna._write_fpga_reg(0x5a, 0x0)
def detectingMonophonicResults(data):
    # 分析CPC单音测试结果
    uiLog(u"CPC单音测试信号强度:%s" % ord(data[-3]))
    c = PARAM["minMonophonicSignalStrength"] <= ord(data[-3]) <= PARAM["maxMonophonicSignalStrength"]
    if not c: raise TestItemFailException(failWeight = 10,message=u"CPC单音测试结果值: %s" % ord(data[-3]))
def sendBSTTestWakeupCommandToTheAntenna(antenna,numberOfTimesSent,waitingSeconds):
    # 向天线发送BST测试命令
    tx_pll = TxPll(antenna)
    mac_ctrl = MacCtrl(antenna)
    antenna._init_fpga()
    antenna.fpga_pll_config()
    antenna._write_fpga_reg(0x5a, 0x01)
    tx_pll.config(PARAM["rd52_frequency"])
    antenna._write_fpga_reg(0x50, 0x02)
    antenna._write_fpga_reg(0x51, 0x01)
    antenna._write_fpga_reg(0x58, 0x01)
    antenna._write_fpga_reg(0x59, 0x01)
    antenna._write_fpga_reg(0x56, 0x24)
    antenna._write_fpga_reg(0x57, 0x00)
    antenna._write_fpga_reg(0x57, 0x01)
    antenna._write_fpga_reg(0x57, 0x00)
    mac_ctrl.send_test_frame(numberOfTimesSent, 0)  # 修改发送次数
    time.sleep(waitingSeconds)  # 等待 RD52天线 发送测试
def sendBSTTestFrameCommandToTheAntenna(antenna,numberOfTimesSent,waitingSeconds):
    # 向天线发送BST测试命令
    tx_pll = TxPll(antenna)
    mac_ctrl = MacCtrl(antenna)
    antenna._init_fpga()
    antenna.fpga_pll_config()
    antenna._write_fpga_reg(0x5a, 0x01)
    tx_pll.config(PARAM["rd52_frequency"])
    antenna._write_fpga_reg(0x50, 0x02)
    antenna._write_fpga_reg(0x51, 0x01)
    antenna._write_fpga_reg(0x58, 0x01)
    antenna._write_fpga_reg(0x59, 0x01)
    antenna._write_fpga_reg(0x56, 0x08)
    antenna._write_fpga_reg(0x57, 0x00)
    antenna._write_fpga_reg(0x57, 0x01)
    antenna._write_fpga_reg(0x57, 0x00)
    mac_ctrl.send_test_frame(numberOfTimesSent, 0)  # 修改发送次数
    time.sleep(waitingSeconds)  # 等待 RD52天线 发送测试
def sendBSTStopCommandToTheAntenna(antenna):
    antenna._write_fpga_reg(0x5a, 0x1)
    antenna._write_fpga_reg(0x58, 0x0)
    antenna._write_fpga_reg(0x59, 0x0)
    antenna._write_fpga_reg(0x46, 0x1)
    antenna._write_fpga_reg(0x3e, 0x0)
    antenna._write_fpga_reg(0x5a, 0x0)
class VersionDownloadBoard(TestResource):
    # 版本下载板资源
    def __init__(self,param):
        self.serialPort = param["port"]
        self.serialCom = None

    def initResource(self):
        self.serialCom = serial.Serial(port = self.serialPort,baudrate=115200,timeout=6)

    def retrive(self):
        self.serialCom.close()

    def __sendAndRecv(self,cmdHex):
        # 发送并接收，为便于处理，入参是HEX，返回是字符串
        self.serialCom.flush()
        logger.info("-> %s"%cmdHex)

        cmd = cmdHex.decode("hex")
        targetRsctl = cmd[2]

        self.serialCom.write(cmd)
        # 全部下载指令的返回帧长度是变长的，先读帧头
        while True:
            firstChar = self.serialCom.read(1)
            if firstChar == "": raise AbortTestException(message=u"下载工装板通信错误") # 啥也没读到，不玩了

            if firstChar != "\x55":
                logger.info("<= %s"%firstChar.encode("hex"))
                continue

            ret = self.serialCom.read(5)
            if ret == "": raise AbortTestException(message=u"下载工装板通信错误") # 啥也没读到，不玩了

            if  ret[0]!= "\xAA":
                logger.info("<= %s"%firstChar.encode("hex"))
                continue

            # 注意：这里面对帧头的检测是不严谨的。根据实际串口的特点，这样勉强够用。

            restLen = ord(ret[3])
            dataAndBcc = self.serialCom.read(restLen + 1)   #把剩下的DATA和CRC读回来
            wholeRtnHex = "55" + ret.encode("hex") + dataAndBcc.encode("hex")
            logger.info("<- %s"%wholeRtnHex)
            if ret[1] == targetRsctl:break

        return wholeRtnHex.decode("hex")

    def downloadVersionForAllSlots(self,versionType = "test"):
        # 为全部槽位下载版本，返回两个列表，分别是成功槽位组，和失败槽位组
        cmdHex = "55AA30000230FE%s4A"%("01" if versionType == "test" else "02")
        rtn = self.__sendAndRecv(cmdHex)
        dataAndBcc = rtn[6:]
        if dataAndBcc[0] != "\xFE" or dataAndBcc[-4] != "\xEE":
            raise AbortTestException(message=u"下载工装板通信错误")
        failedSlots = ["%d"%ord(c) for c in dataAndBcc[1:-4]]
        succSlots = filter(lambda s:s not in failedSlots,["%d"%i for i in range(1,17)])
        return succSlots,failedSlots

    def downloadVersionForSlot(self,slot,versionType = "test"):
        # 为某个槽下载版本，下载成功返回True
        if int(slot) <= 8:  
            cmdHex = "55AA3100022008011A"
        else:
            cmdHex = "55AA31000220080219"
        reset_isp = self.__sendAndRecv(cmdHex)
        if reset_isp[-2] != "\x00":
            return False
        time.sleep(0.1)
        cmdHex = "55AA40000330%s%s%.2xF8"%(
            "F8" if 1<= int(slot) <= 8 else "F9",
            "01" if versionType=="formal" else "02",
            int(slot) )
        rtn = self.__sendAndRecv(cmdHex)
        dataAndBcc = rtn[6:]
        return dataAndBcc[-2] == "\x00"

    def switchMode(self,slot,mode="current"):
        # 切换模式，mode=current为电流检测模式，serial为串口模式,download为下载模式，poweroff为掉电模式，
        cmdHex = "55AA5000032006%.2x%.2x06"%(int(slot),{
            "current":4,"serial":2,"download":1,"poweroff":3
                                          }[mode])
        rtn = self.__sendAndRecv(cmdHex)
        if rtn[-2] != "\x00": raise AbortTestException(message=u"模式切换错误")

    def switchSampleResistance(self,slot,resMode="0.4",sampleDelayTime = 2):
        # 切换采样电阻，reMode=01:0.4，02:20K，正常工作使用0.4电阻
        cmdHex = "55AA6000052007%.2x%s%.4x01"%(int(slot),{"0.4":"01","20K":"02"}[resMode],sampleDelayTime)
        rtn = self.__sendAndRecv(cmdHex)
        if rtn[-2] != "\x00": raise AbortTestException(message=u"工装切换电阻失败")

    def enterLowPowerMode(self,slot):
        # CPC 进入低功耗模式
        cmdHex = "55AA7000021011%.2x4A"%int(slot)
        logger.info("-> %s"%cmdHex)
        self.serialCom.write(cmdHex.decode("hex"))

    def testSerial(self,slot):
        # 串口测试
        cmdHex = "55AA8000021016%.2x4A"%(int(slot))
        try:
            rtn = self.__sendAndRecv(cmdHex)
            if rtn[-2] != "\x00": raise TestItemFailException(failWeight=10,message=u"串口测试不通过")
        except AbortTestException,e:
            #串口不通，统一判为不良，而非工装故障
            raise TestItemFailException(failWeight=10,message=u"串口无响应，也可能是工装不良")

    def readInfo(self,slot):
        # 读取信息，返回0x40000 / 0x40040 / 0x40080处的信息(HEX)
        cmdHex = "55AA9000021021%.2x4A"%(int(slot))
        rtn = self.__sendAndRecv(cmdHex)
        info40000,info40040,info40080 = rtn[8:24],rtn[24:44],rtn[44:46]
        return info40000.encode("hex"),info40040.encode("hex"),info40080.encode("hex")

    def writeInfo(self,slot,info40000,info40040,info40080):
        # 写信息，入参分别是0x40000 / 0x40040 / 0x40080处的信息(HEX)
        cmdHex = "55AAA000291020%.2x26%s%s%s4A"%(int(slot),info40000,info40040,info40080)
        try:
            rtn = self.__sendAndRecv(cmdHex)

            # 由于7-16口写操作的响应太慢，暂时上位机先忽略写操作的响应
            self.serialCom.flush()
            logger.info("-> %s"%cmdHex)
            #self.serialCom.write(cmdHex.decode("hex"))
            #time.sleep(0.2)
        except AbortTestException,e:
            # 对于写信息来说，不做单步判定，留待读出来后判定
            if rtn[-2] != "\x00":
                raise TestItemFailException(failWeight=10,message=u"写入Flash失败")

    def readVoltage(self,slot,readTimes = 50):
        # 读取电压值，入参是ADC转换次数，返回电压值（整数）
        cmdHex = "55AAB000032002%.2x%.2x31"%(int(slot),readTimes)
        rtn = self.__sendAndRecv(cmdHex)
        if rtn[-2] != "\x00": raise AbortTestException(message=u"读取电压值失败")
        return int(rtn[-4:-2].encode("hex"),16)


    def readCpcId(self,slot):
        # 读取CPCID，返回CPCID（HEX字符串）
        rtn = self.__sendAndRecv("55AAC000021001%.2x4A"%(int(slot)))
        if rtn[-2] != "\x00": raise TestItemFailException(failWeight=10,message=u"读取CPCID失败")
        return rtn[8:16].encode("hex")

    def readSn(self,slot):
        # 读取SN，返回SN（HEX字符串）
        rtn = self.__sendAndRecv("55AAD000021002%.2x4A"%(int(slot)))
        if rtn[-2] != "\x00": raise TestItemFailException(failWeight=10,message=u"读取SN失败")
        return rtn[8:12].encode("hex")

    def __transferToEsam(self,slot,cmdHex,filter9000 = True):
        # ESAM透传
        cmdHex = "55AA1000%.2x1014%.2x%s4A"%(len(cmdHex)/2 + 2,int(slot),cmdHex)
        rtn = self.__sendAndRecv(cmdHex)
        if rtn[-2] != "\x00": raise TestItemFailException(failWeight=10,message=u"CPC透传失败")
        apdu =  rtn[8:-2].encode("hex")
        if apdu.endswith("9000") and filter9000: return apdu[:-4]
        return apdu

    def activeEsam(self,slot):
        # 激活ESAM
        self.__sendAndRecv("55AA1100031012%.2x114A"%int(slot))

    def initEsam(self,slot,cpcId,sn):
        # 初始化ESAM，入参是槽号、CPCID、SN
        all_zero = "00000000000000000000000000000000"
        issue_info = "C9CFBAA331010001"
        import esam_erease_wenxin as eew
        eew.HFCARD_COMMAND = lambda cmdHex:self.__transferToEsam(slot,cmdHex)
        eew.activeEsam  = lambda :self.activeEsam(slot)
        self.activeEsam(slot)
        eew.cpc_update_startup(all_zero, 0, str(PARAM["issue_info"]), str(cpcId))
        eew.update_SN(sn)

    def writeMacToEsam(self,slot,mac,chooseDf01 = True):
        # 将MAC写入ESAM的DF01下的EF06文件
        if chooseDf01:
            self.__transferToEsam(slot,"00A4000002DF01")    #选择DF01文件
        self.__transferToEsam(slot,"00D686000866666666%s"%mac)    #写ESAM，66666666是魔术字

    def readMacFromEsam(self,slot,chooseDf01 = True):
        # 读取ESAM中的MAC，即读取EF06，然后去掉魔术字，并返回MAC。
        if chooseDf01:
            self.__transferToEsam(slot,"00A4000002DF01")    #选择DF01文件
        rtn = self.__transferToEsam(slot,"00B0860008",filter9000=False)    # 读
        if rtn.endswith("9000"):
            return rtn[8:16]
        raise TestItemFailException(failWeight=10,message=u"读取ESAM-EF06失败")


    def closeCylinder(self):
        # 压下气缸，开始测试
        cmdHex = "55AAC000032004010107"
        self.__sendAndRecv(cmdHex)
        cmdHex = "55AA3100022008011A"
        self.__sendAndRecv(cmdHex)
        cmdHex = "55AA31000220080219"
        self.__sendAndRecv(cmdHex)

        time.sleep(1.5)

    def openCylinder(self):
        # 松开气缸，结束测试
        cmdHex = "55AAD000032004010007"
        self.__sendAndRecv(cmdHex)
        cmdHex = "55AA3100022008011A"
        self.__sendAndRecv(cmdHex)
        cmdHex = "55AA31000220080219"
        self.__sendAndRecv(cmdHex)
     

    def closeAllChannel(self):
        # 关闭所有通道
        self.__sendAndRecv("55AA40000240FFFF4A")
        time.sleep(0.1)

    def test_esam(self,slot):
        self.switchMode(slot,"poweroff")
        time.sleep(0.12)
        self.switchMode(slot,"serial")
        time.sleep(0.06)  
        cmdHex = "55AA6000031012%.2x114A"%(int(slot))
        reset_isp = self.__sendAndRecv(cmdHex)
        if reset_isp[-2] != "\x00":
            raise TestItemFailException(failWeight=10,message=u"初始化ESAM失败")
        cmdHex = "55AA6000071014%.2x00B08100084A"%(int(slot))
        reset_isp = self.__sendAndRecv(cmdHex)
        if reset_isp[-2] != "\x00":
            raise TestItemFailException(failWeight=10,message=u"刷ESAM目录失败")
        if reset_isp[-4] == "\x6A" and reset_isp[-3] == "\x82":
            raise TestItemFailException(failWeight=10,message=u"刷ESAM目录失败")
        else:
            return 0
    def __sendAndRecvLong(self,cmdHex):
        # 发送并接收，为便于处理，入参是HEX，返回是字符串
        self.serialCom.flush()
        logger.info("-> %s"%cmdHex)

        cmd = cmdHex.decode("hex")
        targetRsctl = cmd[2]

        self.serialCom.write(cmd)
        # 全部下载指令的返回帧长度是变长的，先读帧头
        while True:
            firstChar = self.serialCom.read(1)
            if firstChar == "": raise AbortTestException(message=u"下载工装板通信错误") # 啥也没读到，不玩了

            if firstChar != "\x55":
                logger.info("<= %s"%firstChar.encode("hex"))
                continue

            ret = self.serialCom.read(5)
            if ret == "": raise AbortTestException(message=u"下载工装板通信错误") # 啥也没读到，不玩了

            if  ret[0]!= "\xAA":
                logger.info("<= %s"%firstChar.encode("hex"))
                continue

            # 注意：这里面对帧头的检测是不严谨的。根据实际串口的特点，这样勉强够用。

            restLen = int(ret[2:4].encode("hex"),16)
            dataAndBcc = self.serialCom.read(restLen + 1)   #把剩下的DATA和CRC读回来
            wholeRtnHex = "55" + ret.encode("hex") + dataAndBcc.encode("hex")
            logger.info("<- %s"%wholeRtnHex)
            if ret[1] == targetRsctl:break

        return wholeRtnHex.decode("hex")
    def choiceCrruentBadSlot(self,slot,readTimes = 10):
            # 读取电压值，入参是ADC转换次数，返回电压值（整数）
        cmdHex = "55AAB000032001%.2x%.2x31"%(int(slot),readTimes)
        rtn = self.__sendAndRecvLong(cmdHex)
        if rtn[-2] != "\x00": raise AbortTestException(message=u"读取电压值失败")
        high_value = 0
        for i in range(0,len(rtn[8:-3]),2):
            dc_value = int(rtn[i+8:i+10].encode("hex"),16)
            if dc_value >= 1200:
                high_value += 1
        return high_value
    def sendMonophonicTestCommandToTheCPC(self,slot):
        # 向CPC发送单音测试命令
        cmdHex = "55AA8000021054%.2xC7" % (int(slot))
        rtn = self.__sendAndRecvLong(cmdHex)
        if rtn[-2] != "\x00": raise AbortTestException(message=u"向CPC发送单音测试命令错误")
    def stopAndResults(self,slot):
        # 向CPC发送结束测试命令，并返回结果
        cmdHex = "55AA80000210F0%.2x63" % (int(slot))
        rtn = self.__sendAndRecvLong(cmdHex)
        if rtn[-2] != "\x00": raise AbortTestException(message=u"向CPC发送结束测试命令错误")
        return rtn
    def sendWakeTestCommandToTheCPC(self,slot):
        # 向CPC发送唤醒测试命令
        cmdHex = "55AA8000021055%.2xC6" % (int(slot))
        rtn = self.__sendAndRecvLong(cmdHex)
        if rtn[-2] != "\x00": raise AbortTestException(message=u"向CPC发送唤醒测试命令错误")
    def sendReceivingFrameTestCommandToTheCPC(self,slot):
        # 向CPC发送接收帧测试命令
        cmdHex = "55AA8000021058%.2xCB" % (int(slot))
        rtn = self.__sendAndRecvLong(cmdHex)
        if rtn[-2] != "\x00": raise AbortTestException(message=u"向CPC发送接收帧测试命令错误")
