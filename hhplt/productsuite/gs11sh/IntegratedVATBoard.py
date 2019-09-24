#encoding:utf-8
"""
模块:

@author:zws
"""
import socket
from threading import Thread, RLock

import binascii

import time
from hhplt.testengine.testcase import uiLog
from hhplt.deviceresource import TestResource, askForResource
from hhplt.parameters import PARAM
from hhplt.testengine.autoTrigger import AbstractAutoTrigger

import Fe2Rs232ObuTestor


class IntegratedVATBoard(TestResource,Thread):
    # 集成工装板。通过网口与上位机通信，调度所有（目前最多6个）OBU的测试指令

    class DeviceNoResponseException(Exception): pass

    class ObuNoResponseException(Exception):
        def __init__(self,errCode):
            self.errCode = errCode
            self.msg = {
                0x01:u"1-OBU测试功能失败",
                0x02:u"2-OBU测试命令错误",
                0x03:u"3-OBU返回超时",
                0x04:u"4-接收OBU返回MSG错误",
                0x05:u"5-主MCU接收从MCU信息错误",
                0x06:u"6-主MCU接收从MCU信息超时"
            }[self.errCode]


    def __init__(self,initParam):
        Thread.__init__(self)
        self.lock = RLock()
        self.currentRsctl = 0
        self.ip = initParam["integratedVatBoardIp"]
        self.port = initParam["integratedVatBoardPort"]
        self.con = None
        self.recvFrameBuffer = []   # 接收帧缓存
        self.bufferLock = RLock()

    def initResource(self):
        self.createConnect()
        self.start()

    def retrive(self):
        if self.con is not None:
            self.con.close()
        self.con = None

    def createConnect(self):
        try:
            self.lock.acquire()
            if self.con is None:
                con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                con.settimeout(2)
                con.connect((self.ip, self.port))
                self.con = con
        except Exception, e:
            print "create socket fail %s" % e
        finally:
            self.lock.release()

    def __sendFrame(self,frame):
        frameByteArray = bytearray(frame)
        print 'VATBoard->',binascii.hexlify(frameByteArray)
        try:
            if self.con is None:self.createConnect()
            self.con.sendall(frameByteArray)
        except Exception,e:
            print e
            if self.con is not None:
                self.con.close()
            self.con = None

    def sendAndRecv(self,frame):
        self.__sendFrame(frame)
        for i in range(5):
            time.sleep(0.2)
            self.bufferLock.acquire()
            try:
                recvFrame = filter(lambda f:f[2] == frame[2],self.recvFrameBuffer)
                if len(recvFrame) != 0:
                    recvFrame = recvFrame[0]
                    self.recvFrameBuffer.remove(recvFrame)
                    return recvFrame
            finally:
                self.bufferLock.release()
        raise IntegratedVATBoard.DeviceNoResponseException()


    def __processAckFrames(self):
        if self.con is None:self.createConnect()
        recvByte = self.con.recv(1)
        if recvByte == "\x55":
            recvResult = [0x55]
            recvByte = self.con.recv(1)
            if recvByte == "\xAA":
                recvResult.append(0xAA)
                rs = [ord(c) for c in self.con.recv(4)]
                length = rs[2]
                recvResult.extend(rs)
                rs = [ord(c) for c in self.con.recv(length+1)]
                recvResult.extend(rs)
                print "VATBoard<-",binascii.hexlify(bytearray(recvResult))
                # 至此，完整的一帧收到，验证BCC
                if self.__calcBcc(recvResult[2:-1]) == recvResult[-1]:
                    self.bufferLock.acquire()
                    self.recvFrameBuffer.append(recvResult)
                    self.bufferLock.release()
                else:
                    print 'BCC error'


    def run(self):
        while True:
            try:
                self.__processAckFrames()
            except Exception,e:
                #print e
                pass

    def __fetchRsctl(self):
        self.lock.acquire()
        try:
            self.currentRsctl += 1
            self.currentRsctl %= 0xFF
            return self.currentRsctl
        finally:
            self.lock.release()

    @staticmethod
    def __calcBcc(frame):
        return reduce(lambda x,y:x^y,frame,0)

    def buildFrame(self,cmd,data):
        # 构造命令帧
        frame = [0x55,0xaa,self.__fetchRsctl(),0x00,len(data),cmd]
        frame.extend(data)
        frame.append(self.__calcBcc(frame[2:]))
        return frame


    def obuTest(self,obuNum):
        # OBU测试入口
        return Fe2Rs232ObuTestor.Fe2Rs232ObuTestor(obuNum)
        # return self.SingleObuTestor(self,int(obuNum))

    def peripheralCtrl(self,channel):
        # 外设控制入口
        #class MockPeripheralCtrl:
        #    def __getattr__(self,itm):
        #        print itm
        #        return lambda p:p

        #return MockPeripheralCtrl()
        #临时打个桩
            
        return self.PeripheralCtrl(self,int(channel))


    class SingleObuTestor:
        # 单个OBU测试者
        def __init__(self,device,obuNum):
            self.device = device
            self.obuNum = obuNum
            self.testItem = 0
            self.parameters = []

        @staticmethod
        def __to2ByteInt(value):
            return [value>>8,value & 0xFF]

        @staticmethod
        def __toIntValueFrom4Byte(paramArray):
            # 由4字节转换为int值，4字节分别表示千百十个位
            return 1000*paramArray[0] + 100*paramArray[1] + 10*paramArray[2] + paramArray[3]

        def toCmdDataFrame(self):
            data = [self.obuNum,self.testItem]
            data.extend(self.parameters)
            return 0x10,data

        def sendAndRecv(self):
            cmd,data = self.toCmdDataFrame()
            frame = self.device.buildFrame(cmd,data)

            print "OBU->",binascii.hexlify(frame)
            recvFrame = self.device.sendAndRecv(frame)
            print "OBU<-",binascii.hexlify(recvFrame )

            recvCmd,recvData = recvFrame[5],recvFrame[6:-1]
            # 验证返回值是OBU测试结果
            if recvCmd != 0x10:raise IntegratedVATBoard.DeviceNoResponseException()
            # 验证被测号和指令返回
            state,recvObuNum,recvTestItem,recvParameters = recvData[0],recvData[1],recvData[2],recvData[3:]
            if recvObuNum != self.obuNum or recvTestItem != self.testItem:
                raise IntegratedVATBoard.DeviceNoResponseException()
            if state != 0x00:   #测试失败
                raise IntegratedVATBoard.ObuNoResponseException(state)
            return recvParameters

        def OBUCloseSendSingle(self):
            self.testItem = 0x01
            self.sendAndRecv()

        def ResetObu(self):
            self.testItem = 0x02
            self.sendAndRecv()

        def ReadTestFrameNum(self):
            self.testItem = 0x03
            r = self.sendAndRecv()
            return r[0]

        def TestBattPower(self):
            self.testItem = 0x04
            r = self.sendAndRecv()
            return self.__toIntValueFrom4Byte(r)

        def TestSolarPower(self):
            self.testItem = 0x05
            r = self.sendAndRecv()
            return self.__toIntValueFrom4Byte(r)

        def TestCapPower(self):
            self.testItem = 0x06
            r = self.sendAndRecv()
            return self.__toIntValueFrom4Byte(r)

        def TestESAM(self):
            self.testItem = 0x07
            r = self.sendAndRecv()
            return binascii.hexlify(bytearray(r))

        def TestHFChip(self):
            self.testItem = 0x08
            self.sendAndRecv()

        def TestHF(self,times):
            self.testItem = 0x09
            self.parameters = self.__to2ByteInt(times)
            r = self.sendAndRecv()
            return 0
            # return self.__toIntValueFrom4Byte(r)

        def TestUART(self):
            self.testItem = 0x0A
            self.sendAndRecv()

        def TestReset(self):
            self.testItem = 0x0B
            self.sendAndRecv()

        def TestBandWidth(self):
            self.testItem = 0x0C
            self.sendAndRecv()

        def TestLedLight(self):
            self.testItem = 0x0D
            self.sendAndRecv()

        def CloseLedLight(self):
            self.testItem = 0x0E
            self.sendAndRecv()

        def TestOLED(self):
            self.testItem = 0x0F
            self.sendAndRecv()

        def TestDirection(self):
            self.testItem = 0x10
            self.sendAndRecv()

        def IfObuWakeUp(self):
            self.testItem = 0x11
            self.sendAndRecv()

        def OBUEnterWakeUp(self):
            self.testItem = 0x12
            self.sendAndRecv()

        def OBUEnterSleep(self):
            self.testItem = 0x13
            self.sendAndRecv()

        def OBUSendSingle(self):
            self.testItem = 0x14
            self.sendAndRecv()

        def SetWakenSensi(self,gain,grade):
            self.testItem = 0x15
            self.parameters = [gain,grade]
            self.sendAndRecv()

        def TestRedLedPara(self,testTime):
            self.testItem = 0x16
            self.parameters = self.__to2ByteInt(testTime)
            self.sendAndRecv()

        def TestGreenLedPara(self,testTime):
            self.testItem = 0x17
            self.parameters = self.__to2ByteInt(testTime)
            self.sendAndRecv()

        def TestBeepPara(self,testTime):
            self.testItem = 0x18
            self.parameters = self.__to2ByteInt(testTime)
            self.sendAndRecv()

        def WriteWakeSensiPara(self,gain,grade):
            self.testItem = 0x15
            self.parameters = [gain,grade]
            r = self.sendAndRecv()
            return self.__toIntValueFrom4Byte(r)

        def Test5_8G(self):
            self.testItem = 0x20
            self.sendAndRecv()



    class PeripheralCtrl:   #外设控制
        def __init__(self,device,channelId):
            self.device = device
            self.channelId = channelId
            self.cmdType = 0
            self.parameter = None

        @staticmethod
        def __toIntValueFrom4Byte(paramArray):
            # 由4字节转换为int值，4字节分别表示千百十个位
            return 1000*paramArray[0] + 100*paramArray[1] + 10*paramArray[2] + paramArray[3]

        def __toCmdDataFrame(self):
            data = [self.cmdType,self.channelId]
            if self.parameter is not None:data.append(self.parameter)
            return 0x20,data

        def __sendAndRecv(self):
            cmd,data = self.__toCmdDataFrame()
            frame = self.device.buildFrame(cmd,data)
            recvFrame = self.device.sendAndRecv(frame)
            recvCmd,recvData = recvFrame[5],recvFrame[6:-1]
            # 验证返回值是OBU测试结果
            if recvCmd != 0x20:raise IntegratedVATBoard.DeviceNoResponseException()
            # 验证被测号和指令返回
            state,cmdType,channel,recvParameters = recvData[0],recvData[1],recvData[2],recvData[3:]
            if channel != self.channelId or cmdType != self.cmdType or state != 0x00:
                raise IntegratedVATBoard.DeviceNoResponseException()
            return recvParameters

        def readObuPowerOnVoltage(self,collectTimes):
            # 读取OBU板上电电压
            self.cmdType = 0x01
            self.parameter = collectTimes
            r = self.__sendAndRecv()
            return self.__toIntValueFrom4Byte(r)

        def readSleepVoltage(self,collectTimes):
            # 读取休眠电压
            self.cmdType = 0x02
            self.parameter = collectTimes
            r = self.__sendAndRecv()
            return self.__toIntValueFrom4Byte(r)

        def readObuCurrentVoltage(self,collectTimes):
            # 读取OBU当前电压
            self.cmdType = 0x04
            self.parameter = collectTimes
            r = self.__sendAndRecv()
            print"r=%s"%r
            return self.__toIntValueFrom4Byte(r)

        def checkGPIO(self):
            self.cmdType = 0x05
            r = self.__sendAndRecv()
            return r[0] == 0x01

        def channelSelect(self,channelType):
            #下载通道选择：0x01-版本下载，0x02-OBU通道，0x03-关闭，0x04-全部打开
            self.cmdType = 0x06
            self.parameter = channelType
            self.__sendAndRecv()

        def controlGPIO(self,state):
            # 控制外设继电器：0x01-闭合，0x02-断开
            self.cmdType = 0x07
            self.parameter = state
            self.__sendAndRecv()

        def obuPowerCtrl(self,state):
            # OBU电源控制：0x01-上电，0x02-休眠，0x03-断电
            self.cmdType = 0x08
            self.parameter = state
            self.__sendAndRecv()



class IntegratedVatTrigger(AbstractAutoTrigger):
    INSTANCE = None
    # 集成IO板触发器
    def __init__(self):
        AbstractAutoTrigger.__init__(self)
        self.ivb = getIVB()
        self.startChecker = self.ivb.peripheralCtrl(1)
        self.clapCtrl = self.ivb.peripheralCtrl(1)
        IntegratedVatTrigger.INSTANCE = self

    def _checkIfStart(self):
        # return False
        ifStart = not self.startChecker.checkGPIO()
        if ifStart: #开始测试了，合上夹具
            time.sleep(1)
            return True
        else:
            time.sleep(2)
        return False

    def _checkIfStop(self):
        return False

    def openClap(self):
        # 开夹具，停止测试
        self.clapCtrl.controlGPIO(0x02)

    def closeClap(self):
        # 合上夹具，开始测试
        for i in range(1,5,1):
            try:                
                self.clapCtrl.controlGPIO(0x01)
                return
            except IntegratedVATBoard.DeviceNoResponseException,e:
                uiLog(u"第%d次合夹具错误:%s"%(i,str(e)))
                time.sleep(1)
                
		    

def getIVB():
    # 获取集成工装板工具
    return askForResource("IntegratedVATBoard",IntegratedVATBoard,
                          integratedVatBoardIp = PARAM["integratedVatBoardIp"],
                          integratedVatBoardPort = PARAM["integratedVatBoardPort"])




if __name__ == '__main__':
    b = IntegratedVATBoard({"integratedVatBoardIp":"192.168.1.20","integratedVatBoardPort":5000})
    b.initResource()
    t=1
    print 'obuboardpower[%d]'%t,b.peripheralCtrl(t).obuPowerCtrl(0x01)
    print 'obu channel 0x02',b.peripheralCtrl(t).channelSelect(0x02)
    time.sleep(1)
    #print 'obu OBUCloseSendSingle[%d]'%t,b.obuTest(1).OBUCloseSendSingle()
    #print 'obu ResetObu[%d]'%t,b.obuTest(1).ResetObu()
    #print 'obu ReadTestFrameNum[%d]'%t,b.obuTest(1).ReadTestFrameNum()
    #print 'obu TestBattPower[%d]'%t,b.obuTest(1).TestBattPower()
    #print 'obu TestSolarPower[%d]'%t,b.obuTest(1).TestSolarPower()
    #print 'obu TestCapPower[%d]'%t,b.obuTest(1).TestCapPower()
    #print 'obu TestESAM[%d]'%t,b.obuTest(1).TestESAM()
    #print 'obu TestHFChip[%d]'%t,b.obuTest(1).TestHFChip()
    #print 'obu TestHF[%d]'%t,b.obuTest(1).TestHF(0005)  wrong
    #print 'obu TestUART[%d]'%t,b.obuTest(1).TestUART()
    #print 'obu TestReset[%d]'%t,b.obuTest(1).TestReset()
    #print 'obu TestBandWidth[%d]'%t,b.obuTest(1).TestBandWidth()
    #print 'obu TestLedLight[%d]'%t,b.obuTest(1).TestLedLight()
    #print 'obu CloseLedLight[%d]' % t, b.obuTest(1).CloseLedLight()
    #print 'obu TestOLED[%d]' % t, b.obuTest(1).TestOLED()
    print 'obu OBUEnterSleep[%d]' % t, b.obuTest(1).OBUEnterSleep()
    #print 'obu IfObuWakeUp[%d]' % t, b.obuTest(1).IfObuWakeUp()
    #print 'obu OBUEnterWakeUp[%d]' % t, b.obuTest(1).OBUEnterWakeUp()
    #print 'obu OBUSendSingle[%d]' % t, b.obuTest(1).OBUSendSingle()
    #print 'obu SetWakenSensi[%d]' % t, b.obuTest(1).SetWakenSensi()
    #print 'obu TestRedLedPara[%d]' % t, b.obuTest(1).TestRedLedPara()
    #print 'obu TestGreenLedPara[%d]' % t, b.obuTest(1).TestGreenLedPara()
    #print 'obu TestBeepPara[%d]' % t, b.obuTest(1).TestBeepPara()
    #print 'obu WriteWakeSensiPara[%d]' % t, b.obuTest(1).WriteWakeSensiPara()
    #print 'obu Test5_8G[%d]' % t, b.obuTest(1).Test5_8G()








    import os
    os._exit(0)
    # print 'testBattPower',b.obuTest(1).TestBattPower()
    # print 'readObuCurrentVoltage',b.peripheralCtrl(1).readObuCurrentVoltage(1)

    #print 'testHF',b.obuTest(1).TestHF(5)
