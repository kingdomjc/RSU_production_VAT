#encoding:utf-8
u"""单音测试
"""
import serial
import time

from hhplt.deviceresource import askForResource, retrieveAllResource
from hhplt.deviceresource.RD52ReaderDevice import RD52ReaderDevice
from hhplt.deviceresource.SerialToolingBoard import SerialToolingBoard
from hhplt.parameters import PARAM
from hhplt.testengine.server import serialCode,serverParam as SP,ServerBusiness
from hhplt.testengine.exceptions import TestItemFailException, AbortTestException
from hhplt.testengine.parallelTestSynAnnotation import serialSuite
from hhplt.testengine.server import serialCode
from hhplt.testengine.testcase import uiLog

suiteName = u"单音测试"
version = "1.0"
failWeightSum = 10

import logging

logger = logging.getLogger()

VERSION_DOWNLOAD_STATES = {}

finished = 0
board = None #工装板设备
antenna = None #RD52天线
shouldNotRun = False    #若已超过生产，则不允许再测试了

@serialSuite
def setup(product):
    global finished,VERSION_DOWNLOAD_STATES,shouldNotRun,antenna,board
    if shouldNotRun: raise AbortTestException(u"CPCID已超过范围，产量已完成")
    antenna = __getRD52ReaderDevice()
    board = __getSerialToolingBoard()
    if finished == 0:
        VERSION_DOWNLOAD_STATES.update({k:False for k in range(1,17)})
        #board.closeCylinder()
        #board.closeAllChannel()
        time.sleep(0.5)
    product.param["versioned"] = False
    #board.switchSampleResistance(product.productSlot,"0.4")

@serialSuite
def finalFun(product):
    global finished,antenna,board
    finished += 1
    logger.info("------------finish:%d"%finished)
    if finished == len(PARAM["productSlots"].split(",")) :  #全部完成
        retrieveAllResource()
        finished = 0

def rollback(product):
    pass

def __getRD52ReaderDevice():
    return askForResource("RD52ReaderDevice", RD52ReaderDevice, ipaddr=PARAM["rd52_ipaddr"],post=PARAM["rd52_post"])
def __getSerialToolingBoard():
    return askForResource("SerialToolingBoard", SerialToolingBoard, port=PARAM["downloadBoardCom"])

def T_01_monophonic_A(product):
    u"单音测试"
    #proxy = __getRD52ReaderDevice()
    #board = askForResource("SerialToolingBoard", SerialToolingBoard, port=PARAM["downloadBoardCom"])
    #board.switchMode(product.productSlot,"current")
    #time.sleep(0.1)
    #board.switchMode(product.productSlot,"serial")
    #time.sleep(0.2)
    board.testSerial(product.productSlot)
    #board.testSerial(1)
    sendMonophonicTestCommandToTheCPC(board,product.productSlot)
    tx_pll = TxPll(antenna)
    antenna.open(PARAM["rd52_ipaddr"])
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
    data = stopAndResults(board)
    detectingMonophonicResults(data)

def T_02_wake_A(product):
    u"BST唤醒测试"
    sendWakeTestCommandToTheCPC(board)
    sendBSTTestCommandToTheAntenna(antenna,PARAM["sendNumberOfWakes"],1)
    sendBSTStopCommandToTheAntenna(antenna)
    data = stopAndResults(board)
    detectBSTResults(data, "唤醒", PARAM["detectNumberOfWakes"])

def T_03_receivingFrame_A(product):
    u"BST接收帧测试"
    sendReceivingFrameTestCommandToTheCPC(board)
    sendBSTTestCommandToTheAntenna(antenna, PARAM["sendReceivingFrame"],2)
    sendBSTStopCommandToTheAntenna(antenna)
    data = stopAndResults(board)
    detectBSTResults(data, "接收帧", PARAM["detectReceivingFrame"])

def detectingMonophonicResults(data):
    # 分析CPC单音测试结果
    uiLog(u"CPC单音测试信号强度:%s" % ord(data[-3]))
    c = PARAM["minMonophonicSignalStrength"] <= ord(data[-3]) <= PARAM["maxMonophonicSignalStrength"]
    if not c: raise TestItemFailException(failWeight = 10,message=u"CPC单音测试结果值: %s" % ord(data[-3]))
def detectWakeupResults(data):
    # 分析CPC唤醒测试结果
    uiLog(u"CPC唤醒测试结果:%s" % ord(data[-3]))
    c = ord(data[-3]) < PARAM["detectNumberOfWakes"]
    if c: raise TestItemFailException(failWeight = 10,message=u"CPC唤醒测试结果值: %s" % ord(data[-3]))
def detectBSTResults(data,item,detectParam):
    # 分析CPC BST测试结果
    uiLog(u"CPC%s试结果:%s" %(item,ord(data[-3])))
    c = ord(data[-3]) < detectParam
    if c: raise TestItemFailException(failWeight = 10,message=u"CPC%s测试结果值: %s" %(item,ord(data[-3])))
def stopAndResults(board):
    # 向CPC发送结束测试命令，并返回结果
    cmdHex = "55AA80000210F00163"
    rtn = board.sendAndRecv(cmdHex)
    if rtn[-2] != "\x00": raise AbortTestException(message=u"向CPC发送结束测试命令错误")
    return rtn
def sendMonophonicTestCommandToTheCPC(board,slot):
    # 向CPC发送单音测试命令
    cmdHex = "55AA8000021054%.2xC7" % (int(slot))
    rtn = board.sendAndRecv(cmdHex)
    if rtn[-2] != "\x00": raise AbortTestException(message=u"向CPC发送单音测试命令错误")
def sendWakeTestCommandToTheCPC(board):
    # 向CPC发送唤醒测试命令
    cmdHex = "55AA800002105501C6"
    rtn = board.sendAndRecv(cmdHex)
    if rtn[-2] != "\x00": raise AbortTestException(message=u"向CPC发送唤醒测试命令错误")
def sendReceivingFrameTestCommandToTheCPC(board):
    # 向CPC发送接收帧测试命令
    cmdHex = "55AA800002105801CB"
    rtn = board.sendAndRecv(cmdHex)
    if rtn[-2] != "\x00": raise AbortTestException(message=u"向CPC发送接收帧测试命令错误")
def sendBSTTestCommandToTheAntenna(antenna,numberOfTimesSent,waitingSeconds):
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
    antenna._write_fpga_reg(0x56, 0x25)
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
def sendMonophonicStopCommandToTheAntenna(antenna):
    antenna._write_fpga_reg(0x5a, 0x1)
    antenna._write_fpga_reg(0x58, 0x0)
    antenna._write_fpga_reg(0x59, 0x0)
    antenna._write_fpga_reg(0x46, 0x1)
    antenna._write_fpga_reg(0x3e, 0x0)
    antenna._write_fpga_reg(0x5a, 0x0)
class TxPll(object):
    def __init__(self, proxy=None):
        self.proxy = proxy

    def _write_and_trig(self, value):
        self.proxy._write_fpga_reg(0x54, value)
        self.proxy._write_fpga_reg(0x55, 0x0000)
        self.proxy._write_fpga_reg(0x55, 0x0001)
        self.proxy._write_fpga_reg(0x55, 0x0000)

    def config(self, channel):
        if channel == 5830:
            #print "channel freq is %d " % 5830
            self._write_and_trig(0x0204)
            self._write_and_trig(0x0404)
            # self._write_and_trig(0x063e)
            self._write_and_trig(0x1030)
            self._write_and_trig(0x084d)
            self._write_and_trig(0x0a11)
            self._write_and_trig(0x0c08)
            self._write_and_trig(0x0e91)
            # self._write_and_trig(0x1030)
            self._write_and_trig(0x063e)
            self._write_and_trig(0x1200)
            self._write_and_trig(0x1400)
            self._write_and_trig(0x16b9)
            self._write_and_trig(0x180d)
            self._write_and_trig(0x1ac0)
        else:  # 5840
            #print "channel freq is %d " % 5840
            # proxy._write_fpga_reg(0x5c,01)
            self._write_and_trig(0x0204)
            self._write_and_trig(0x0404)
            self._write_and_trig(0x063f)
            # self._write_and_trig(0x1000)
            self._write_and_trig(0x084d)
            self._write_and_trig(0x0a11)
            self._write_and_trig(0x0c08)
            self._write_and_trig(0x0e92)
            self._write_and_trig(0x1000)
            # self._write_and_trig(0x063f)
            self._write_and_trig(0x1200)
            self._write_and_trig(0x1400)
            self._write_and_trig(0x16b9)
            self._write_and_trig(0x180d)
            self._write_and_trig(0x1ac0)
            # proxy._write_fpga_reg(0x5c,0x0001)

    def is_lock(self):
        if self.proxy._read_fpga_reg(0x34) == 1:
            return True
        else:
            return False

class RxPll(object):
    def __init__(self, proxy=None):
        self.proxy = proxy
    def _write_and_trig(self, value):
        self.proxy._write_fpga_reg(0x54, value)
        self.proxy._write_fpga_reg(0x55, 0x0000)
        self.proxy._write_fpga_reg(0x55, 0x0001)
        self.proxy._write_fpga_reg(0x55, 0x0000)

    def config(self, channel):
        if channel == 5720:
            print "channel freq is %d " % 5720
            self.proxy._write_and_trig(0x0204)
            self.proxy._write_and_trig(0x0404)
            # self._write_and_trig(0x063f)
            self.proxy._write_and_trig(0x063e)
            self.proxy._write_and_trig(0x084d)
            self.proxy._write_and_trig(0x0a11)
            self.proxy._write_and_trig(0x0c08)
            self.proxy._write_and_trig(0x0e8f)
            # self._write_and_trig(0x1000)
            # self._write_and_trig(0x1200)
            # self._write_and_trig(0x1400)
            self.proxy._write_and_trig(0x1003)
            self.proxy._write_and_trig(0x1233)
            self.proxy._write_and_trig(0x1430)
            self.proxy._write_and_trig(0x16b9)
            self.proxy._write_and_trig(0x180d)
            self.proxy._write_and_trig(0x1ac0)
        else:
            print "channel freq is %d " % 5730
            self.proxy._write_and_trig(0x0204)
            self.proxy._write_and_trig(0x0404)
            self.proxy._write_and_trig(0x063e)
            self.proxy._write_and_trig(0x084d)
            self.proxy._write_and_trig(0x0a11)
            self.proxy._write_and_trig(0x0c08)
            self.proxy._write_and_trig(0x0e8f)
            # self._write_and_trig(0x0e90)
            # self._write_and_trig(0x1010)
            # self._write_and_trig(0x1020)
            self.proxy._write_and_trig(0x1013)
            # self._write_and_trig(0x1200)
            self.proxy._write_and_trig(0x1233)
            # self._write_and_trig(0x1400)
            self.proxy._write_and_trig(0x1430)
            self.proxy._write_and_trig(0x16b9)
            self.proxy._write_and_trig(0x180d)
            self.proxy._write_and_trig(0x1ac0)

            # chang Freq 5722~5724MHz
            # self._write_and_trig(0x063e)
            # self._write_and_trig(0x1003)
            # self._write_and_trig(0x1233)
            # self._write_and_trig(0x1430)

    def config_pn9(self, channel):
        if channel == 5720:
            print "channel freq is %d " % 5720
            self.proxy._write_and_trig(0x0204)
            self.proxy._write_and_trig(0x0406)
            self.proxy._write_and_trig(0x063f)
            self.proxy._write_and_trig(0x084d)
            self.proxy._write_and_trig(0x0a11)
            self.proxy._write_and_trig(0x0c08)
            self.proxy._write_and_trig(0x0e8f)
            self.proxy._write_and_trig(0x1000)
            self.proxy._write_and_trig(0x1200)
            self.proxy._write_and_trig(0x1400)
            self.proxy._write_and_trig(0x16b9)
            # self._write_and_trig(0x16a1)
            self.proxy._write_and_trig(0x180d)
            self.proxy._write_and_trig(0x1ac0)
        else:
            print "channel freq is %d " % 5730
            self.proxy._write_and_trig(0x0204)
            self.proxy._write_and_trig(0x0406)
            self.proxy._write_and_trig(0x063e)
            self.proxy._write_and_trig(0x084d)
            self.proxy._write_and_trig(0x0a11)
            self.proxy._write_and_trig(0x0c08)
            self.proxy._write_and_trig(0x0e8f)
            self.proxy._write_and_trig(0x1010)
            self.proxy._write_and_trig(0x1200)
            self.proxy._write_and_trig(0x1400)
            self.proxy._write_and_trig(0x16b9)
            # self._write_and_trig(0x16a1)
            self.proxy._write_and_trig(0x180d)
            self.proxy._write_and_trig(0x1ac0)

    def is_lock(self):
        if self.proxy._read_fpga_reg(0xf4) == 1:
            return True
        else:
            return False
class MacCtrl(object):
    def __init__(self, proxy=None):
        self.proxy = proxy
    def send_test_frame(self, num, flag):
        self.proxy._write_fpga_reg(0x20, 0x0003) #FORWARD_FILT_EN
        self.proxy._write_fpga_reg(0x21, 0x7ffe) #FORWARD_PWADJ
        self.proxy._write_fpga_reg(0x22, 0x47e) #ask_high_val max:1f00
        self.proxy._write_fpga_reg(0x23, 0x7d0) #ask_low_val
        self.proxy._write_fpga_reg(0x24, 0x7d0) #ask_no_val
        self.proxy._write_fpga_reg(0x0e, 0x0003) #wake signal guard 0.5ms
        self.proxy._write_fpga_reg(0x44, 0x0005) #resend interval 20ms
        self.proxy._write_fpga_reg(0x56, 0x0030)
        self.proxy._write_fpga_reg(0x57, 0x0000)
        self.proxy._write_fpga_reg(0x57, 0x0001)
        self.proxy._write_fpga_reg(0x57, 0x0000)
        self.proxy._write_fpga_reg(0x45, num) #resend cnt
        self.proxy._write_fpga_reg(0x46, 0x0000) #
        '''
        proxy._write_fpga_reg(0x200, 0x0009)
        proxy._write_fpga_reg(0x201, 0x0200)
        proxy._write_fpga_reg(0x202, 0x7740)
        proxy._write_fpga_reg(0x203, 0x0599)
        proxy._write_fpga_reg(0x204, 0x0001)
        proxy._write_fpga_reg(0x205, 0x8014)
        proxy._write_fpga_reg(0x206, 0x0001)
        proxy._write_fpga_reg(0x207, 0x1000)
        proxy._write_fpga_reg(0x208, 0xca79)
        proxy._write_fpga_reg(0x209, 0xb25f)
        proxy._write_fpga_reg(0x20a, 0xcaa3)
        proxy._write_fpga_reg(0x20b, 0xf0fb)
        proxy._write_fpga_reg(0x20c, 0x0000)
        proxy._write_fpga_reg(0x20d, 0xb673)
        '''
        self.proxy._write_fpga_reg(0x200, 0xffff)
        self.proxy._write_fpga_reg(0x201, 0xffff)
        self.proxy._write_fpga_reg(0x202, 0x0350)
        self.proxy._write_fpga_reg(0x203, 0xc091)
        self.proxy._write_fpga_reg(0x204, 0x0009)
        self.proxy._write_fpga_reg(0x205, 0x9103)
        self.proxy._write_fpga_reg(0x206, 0x7b38)
        self.proxy._write_fpga_reg(0x207, 0x5359)
        self.proxy._write_fpga_reg(0x208, 0x0100)
        self.proxy._write_fpga_reg(0x209, 0x8141)
        self.proxy._write_fpga_reg(0x20a, 0xb129)
        self.proxy._write_fpga_reg(0x20b, 0x001a)
        self.proxy._write_fpga_reg(0x20c, 0x0000)
        self.proxy._write_fpga_reg(0x20d, 0x0000)
        self.proxy._write_fpga_reg(0x20e, 0x0000)
        self.proxy._write_fpga_reg(0x20f, 0x1913)
        self.proxy._write_fpga_reg(0x08, 0x0020)
        self.proxy._write_fpga_reg(0x09, 0x0000)
        time.sleep(0.1)
        if 1 == flag:
            self.proxy._write_fpga_reg(0x09, 0x0003)
            self.proxy._write_fpga_reg(0x23, 0x7d0) #ask_low_val
            self.proxy._write_fpga_reg(0x24, 0x7d0) #ask_no_val
            self.proxy._write_fpga_reg(0x0e, 0x0003) #wake signal guard 0.5ms
            self.proxy._write_fpga_reg(0x44, 0x003f) #resend interval 5ms
            self.proxy._write_fpga_reg(0x56, 0x0027)
            self.proxy._write_fpga_reg(0x57, 0x0000)
            self.proxy._write_fpga_reg(0x57, 0x0001)
            self.proxy._write_fpga_reg(0x57, 0x0000)
        else:
            self.proxy._write_fpga_reg(0x09, 0x0003)