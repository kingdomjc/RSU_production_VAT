#encoding:utf-8
'''
Created on 2019-2-25

串口工装板

@author: 刘琪
'''
import serial
import time
import logging
from hhplt.testengine.exceptions import TestItemFailException, AbortTestException
from hhplt.deviceresource import TestResource
import binascii

logger = logging.getLogger()
class SerialToolingBoard(TestResource):
    def __init__(self,param):
        self.serialPort = str(param["port"])
        self.serialCom = None

    def initResource(self):
        self.serialCom = serial.Serial(port = self.serialPort,baudrate=115200,timeout=5)

    def retrive(self):
        self.serialCom.close()

    def sendAndRecv(self,cmdHex):
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

    def testSerial(self,slot):
        # 串口测试
        cmdStr = "55AA8000021016%.2x85"%(int(slot))
        cmdStr = self.get_crc(cmdStr)
        try:
            rtn = self.sendAndRecv(cmdStr)
            if rtn[-2] != "\x00": raise TestItemFailException(failWeight=10,message=u"串口测试不通过")
        except AbortTestException,e:
            #串口不通，统一判为不良，而非工装故障
            raise TestItemFailException(failWeight=10,message=u"串口无响应，也可能是工装不良")
    # calculate BRC
    def get_crc(self,cmd):
        calc_len = (len(cmd))/2 - 3
        send_cmd = bytearray.fromhex(cmd)
        #a = cmd.decode("hex")
        send_cmd = list(send_cmd)
        i = 0
        bcc_calc = 0
        while i < calc_len:
            bcc_calc = bcc_calc^send_cmd[2 + i]
            i = i + 1
        return "%s%.2x"%(cmd[:-2],bcc_calc)
    def switchMode(self,slot,mode="current"):
        # 切换模式，mode=current为电流检测模式，serial为串口模式,download为下载模式，poweroff为掉电模式，
        cmdHex = "55AA5000032006%.2x%.2x06"%(int(slot),{
            "current":4,"serial":2,"download":1,"poweroff":3
                                          }[mode])
        rtn = self.sendAndRecv(cmdHex)
        if rtn[-2] != "\x00": raise AbortTestException(message=u"模式切换错误")