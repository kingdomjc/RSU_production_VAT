#encoding:utf-8
"""
模块: OBU版本下载板驱动


@author:zws
"""
from threading import Thread, RLock
from hhplt.parameters import SESSION, PARAM

import time

import binascii

import serial

from hhplt.deviceresource import TestResource
from hhplt.testengine.autoTrigger import AbstractAutoTrigger
from hhplt.testengine.exceptions import TestItemFailException


class ObuVersionDownloadBoard(TestResource,Thread):

    def __init__(self,initParam):
        Thread.__init__(self)
        self.currentRsctl = 0
        self.serialLock = RLock()
        self.serialPort = initParam["downloadBoardSerialPort"]

    def initResource(self):
        self.boardSerial = serial.Serial(port=self.serialPort,baudrate = 115200,timeout = 1)

    def retrive(self):
        self.boardSerial.close()

    def __fetchRsctl(self):
        self.currentRsctl += 1
        self.currentRsctl %= 0xFF
        return self.currentRsctl

    @staticmethod
    def __calcBcc(frame):
        return reduce(lambda x,y:x^y,frame,0)

    def __buildFrame(self,cmd,data):
        # 构造命令帧
        frame = [0x55,0xaa,self.__fetchRsctl(),0x00,len(data)+1,cmd]
        #frame = [0x55,0xaa,self.__fetchRsctl(),0x00,len(data),cmd]
        frame.extend(data)
        frame.append(self.__calcBcc(frame[2:]))
        return bytearray(frame)

    def __sendAndRecv(self,cmd,data,targetLen = 8):
        # 发送并接收，返回值为接收帧的cmd,data
        self.serialLock.acquire()
        try:
            frame = self.__buildFrame(cmd,data)
            print "DownloadBoard->",binascii.hexlify(frame)
            self.boardSerial.flush()
            self.boardSerial.write(frame)
            response = self.boardSerial.read(targetLen)
            print "DownloadBoard<-",binascii.hexlify(response)
            if response == '':
                raise TestItemFailException(failWeight = 10,message = u'串口无响应')
            response = [ord(c) for c in response]
            if True:    #self.__calcBcc(response[2:-1]) == response[-1]:
                # 不验证BCC
                resCmd = response[5]
                dataLen = response[4] - 1
                data = response[6:6+dataLen]
                return resCmd,data
            else:
                raise TestItemFailException(failWeight = 10,message = u'串口接收BCC错误')
        finally:
            self.serialLock.release()

    #######################################################################

    def selectChannelForUpdateVersion(self,channel):
        # 使能通道，用于固件更新，通道号：1-6
        self.__sendAndRecv(0xA2,[0x07,0x00])
        indx = channel - 1
        model2 = (indx & 0b100) >> 2
        model1 = (indx & 0b010) >> 1
        model0 = (indx & 0b001)
        self.__sendAndRecv(0xA2,[0x0A,model2])
        self.__sendAndRecv(0xA2,[0x09,model1])
        self.__sendAndRecv(0xA2,[0x08,model0])

    def unselectChannelForUpdateVersion(self):
        # 固件更新完成，通过此取消使能通道
        self.__sendAndRecv(0xA2,[0x07,0x01])

    def powerOn(self,channel,enabled):
        # 3.3V输出上电，通道号：1-6
        subCmd = (0x0B,0x0C,0x0D,0x0E,0x0F,0x10)[channel-1]
        self.__sendAndRecv(0xA2,[subCmd,0x01 if enabled else 0x00])

    def readVoltage(self,channel):
        # 读取电压，返回电压值
        resCmd,resData = self.__sendAndRecv(0xA1,[channel-1],targetLen=10)
        if resData[0] != 0x00:raise Exception(u"读取%d槽位电压失败"%channel)
        return (resData[1]<<8) + resData[2]

    def resetEnable(self,channel,enabled):
        # 复位使能，将复位口拉高电平
        subCmd = (0x11,0x12,0x13,0x14,0x15,0x16)[channel-1]
        self.__sendAndRecv(0xA2,[subCmd,0x01 if enabled else 0x00])

    def reset(self,channel):
        # 复位，将复位口先拉高，再拉低
        subCmd = (0x1D,0x1E,0x1F,0x20,0x21,0x22)[channel-1]
        self.__sendAndRecv(0xA2,[subCmd,0x01])
        time.sleep(0.010)
        self.__sendAndRecv(0xA2,[subCmd,0x00])

    def dataClockEnable(self,channel,enabled):
        # 数据时钟使能
        subCmd = (0x17,0x18,0x19,0x1A,0x1B,0x1C)[channel-1]
        self.__sendAndRecv(0xA2,[subCmd,0x01 if enabled else 0x00])

    def checkStartBtn(self):
        # 检查开始按键
        resCmd,resData = self.__sendAndRecv(0xA5,[0x00])
        return resData[0] == 0x00

    def operateClap(self,ope):
        # 操作夹具，1-合上夹具，测试开始，2-打开夹具，测试结束
        subCmd = [0x00,0x00 if ope == 1 else 0x01]
        self.__sendAndRecv(0xA2,subCmd)
           

    downloadStateEnum = {0xE2:"CHECK_UID_ERR",0xE3:"PROG_LDROM_ERR",0xE4:"PROG_APROM_ERR",0xE5:"PROG_DATA_ERR",0xE6:"UDATE_CONFIG_ERR"}


    def triggerDownload(self,channel):
        # 触发版本下载，同步返回，下载失败抛出异常
        resCmd,resData = self.__sendAndRecv(0xA3,[channel-1],targetLen=9)
        if resData[0] !=0x00:
            raise Exception(u"槽位%d版本下载触发失败"%channel)
        time.sleep(4)
        for i in range(3):
            resCmd,resData = self.__sendAndRecv(0xA4,[channel-1],targetLen=13)
            downloadState = resData[channel-1]
            if downloadState == 0xC0:return #下载成功
            elif downloadState == 0xC1: # 等待下载
                time.sleep(2)
                continue
            elif downloadState in self.downloadStateEnum :
                raise Exception(u"槽位%d版本下载失败:%s"%(channel,self.downloadStateEnum[downloadState]))
            else:
                time.sleep(2)
                continue
        else:
            raise Exception(u"槽位%d版本下载失败，超时"%channel)



class VDBTrigger(AbstractAutoTrigger):
    INSTANCE = None
    # 集成IO板触发器
    def __init__(self):
        AbstractAutoTrigger.__init__(self)
        from hhplt.deviceresource import askForResource
        self.vdb = askForResource("VersionDownloadIOController",
                          ObuVersionDownloadBoard,downloadBoardSerialPort = PARAM["downloadBoardSerialPort"])
        self.isStarted = False

    def _checkIfStart(self):
        # return False
        if PARAM["clapOperate"] == "I":return False

        if self.vdb.checkStartBtn(): #开始测试了，合上夹具
            #time.sleep(0.2)
            self.isStarted = True
            return True
        else:
            time.sleep(0.1)
        return False

    def _checkIfStop(self):
        if self.isStarted:
            if self.vdb.checkStartBtn():
                self.isStarted = False
                return True
        return False





