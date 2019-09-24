#encoding:utf-8
'''
Created on 2016-8-1
GS11上海产线测试资源套装
包含如下的组件：

GS11VATSerial:
    GS11VAT版本下的普通串口，能够直接或间同上位机的RS232串口相连接并进行交互
        此前GS10是通过工装板间接与OBU通信，但大部分指令都是直接透传的

GS11ShDigitalBoardSwitcher:
    GS11上海产线新增的切换板，在数字单板测试中，用于协同串口通信，测试电流电压等；
    
GS11ShDigitalBoardFixture：
    GS11数字单板治具，基于IO板卡联动气缸夹具动作

GS11ShRadioFreqBoardFixture：
    GS11射频单板治具，基于IO板卡联动气缸夹具动作

GS11ShOverallFixture：
    GS11整机治具，基于IO板卡联动气缸夹具动作

@author: 张文硕
'''

from hhplt.deviceresource import TestResource,TestResourceInitException
from hhplt.testengine.testcase import uiLog,superUiLog
from hhplt.deviceresource import AbortTestException,TestItemFailException
from hhplt.deviceresource import LonggangIOBoard
from hhplt.parameters import PARAM
from threading import RLock

import os
import time
import serial
from hhplt import utils

class LinearSerialComm(TestResource):
    '''行式串口通信，入参是serial对象'''
    def __init__(self,param):
        self.serialPort = param
        self.ENDSIGNAL = '\r\n'
    
    def initResource(self):
        try:
            if self.serialPort.getPort() is None:
                self.serialPort.setPort(self.serialPortName)
            if not self.serialPort.isOpen():
                self.serialPort.open()
                time.sleep(1)
        except Exception,e:
            print e
            self.retrive()
            raise AbortTestException(message = u'计算机串口初始化失败，不能继续测试，请检查软硬件设置')
        
    def retrive(self):
        if self.serialPort.isOpen():
            self.serialPort.close()
            time.sleep(1)

    def synComm(self,request,noResponseFailWeight=10):
        '''同步通信，直接返回结果。发送和接收都是以换行(\r\n)为标志的，自动填入并筛除'''
        print "->",request
        self.serialPort.flushInput()
        self.send(request)
        response = self.receive()
        tmpResponse = None
        print "<-",response
        #如果串口回乱码，要处理一下
        try:
            response = response.decode('utf-8')
        except UnicodeDecodeError,e:
            response =u'[乱码]'
            
        if response == '':
            if tmpResponse is None:
                raise TestItemFailException(failWeight = noResponseFailWeight,message = u'串口无响应')
            else:
                return tmpResponse
        return response.rstrip()
    
    def send(self,request):
        '''发送'''
        if not request.endswith(self.ENDSIGNAL):
            request+=self.ENDSIGNAL
        try:
            self.serialPort.write(request)
        except Exception,e:
            print e
            raise AbortTestException(message = u'计算机串口异常，请检查硬件连接并重启软件')
        
    def receive(self):
        '''接收'''
        response = self.serialPort.readline(128)
        return response

class GS11VatSerial(TestResource):
    "GS11透传串口"
    def __init__(self,initParam):
        self.serialPortName = initParam["serialPortName"]
        self.lock = RLock()
    
    def initResource(self):
        try:
            self.lock.acquire()
            self.boardSerial = serial.Serial(port=self.serialPortName,baudrate = 38400,timeout = 2)
            self.linearSerialComm = LinearSerialComm(self.boardSerial)
        finally:
            self.lock.release()
    
    def retrive(self):
        self.boardSerial.close()
    
    def sendAndGet(self,request):
        '''发送并接收，判定逻辑完全由外部进行'''
        try:
            self.lock.acquire()
            return self.linearSerialComm.synComm(request)
        finally:
            self.lock.release()
    
    def assertSynComm(self,request,response = None,noResponseFailWeight=10,assertFailWeight=10):
        '''直接给出请求响应，自动判定串口通信值是否正确；如果response==None，则不判定响应'''
        try:
            self.lock.acquire()
            superUiLog(u"串口发送:"+request)
            realResponse = self.linearSerialComm.synComm(request)
            superUiLog(u"收到串口响应:"+realResponse)
            if response != None and realResponse != response:
                raise TestItemFailException(failWeight = assertFailWeight,message = u'%s命令串口响应错误'%(request))
            return True
        finally:
            self.lock.release()
    
    def assertAndGetParam(self,request,response,noResponseFailWeight=10,assertFailWeight=10):
        '''判定响应命令正确与否，并返回输出参数'''
        try:
            self.lock.acquire()
            superUiLog(u"串口发送:"+request)
            r = self.linearSerialComm.synComm(request)
            superUiLog(u"收到串口响应:"+r)
            if not r.startswith(response):
                raise TestItemFailException(failWeight = assertFailWeight,message = u'%s命令串口响应错误'%(request))
            else:
                return r[len(response):]
        finally:
            self.lock.release()
    
    def assertAndGetNumberParam(self,request,response,noResponseFailWeight=10,assertFailWeight=10):
        '''判定响应，并获得数字返回参数，在上面那个基础上'''
        try:
            self.lock.acquire()
            return float(self.assertAndGetParam(request, response, noResponseFailWeight, assertFailWeight))
        finally:
            self.lock.release()
    
    def asynSend(self,request):
        '''异步下达指令'''
        try:
            self.lock.acquire()
            self.linearSerialComm.send(request)
        finally:
            self.lock.release()
    
    def asynReceive(self):
        '''异步接收'''
        try:
            self.lock.acquire()
            return self.linearSerialComm.receive()
        finally:
            self.lock.release()
    
    def asynReceiveAndAssert(self,assert_response,noResponseFailWeight=10,assertFailWeight=10):
        '''异步接收并验证'''
        try:
            self.lock.acquire()
            response = self.linearSerialComm.receive()
            if response == '':
                raise TestItemFailException(failWeight = noResponseFailWeight,message = u'串口无响应')
            if assert_response not in response:
                raise TestItemFailException(failWeight = assertFailWeight,message = u'串口响应错误')
        finally:
            self.lock.release()


class GS11ShDigitalBoardSwitcher(TestResource):
    "GS11切换板，用于控制串口通断，测试电流等"
    def __init__(self,initParam):
        self.boardSerial = None
        self.baudrate = initParam["baudrate"]
        self.serialPortName = initParam["serialPort"]
        self.rsctl = 0
        self.serialLock = RLock()
    
    def initResource(self):
        self.boardSerial = serial.Serial(port=self.serialPortName,baudrate = self.baudrate ,timeout = 2)
    
    def retrive(self):
        self.boardSerial.close()
        
    def powerObu(self,slotNo,powerOn=True):
        fm = self.__sendAndRec(self.__buildFrame([0xa1,int(slotNo),1 if powerOn else 0]))
        if fm[0] != 0xb1:raise AbortTestException(message=u"IO切换板协议响应异常")
    
    def setSerialCom(self,slotNo,openSerial=True):
        fm = self.__sendAndRec(self.__buildFrame([0xa6,int(slotNo),1 if openSerial else 0]))
        if fm[0] != 0xb6:raise AbortTestException(message=u"IO切换板协议响应异常")
    
    def switchCurrentMode(self,slotNo,mode):
        fm = self.__sendAndRec(self.__buildFrame([0xa2,int(slotNo),mode]))
        if fm[0] != 0xb2:raise AbortTestException(message=u"IO切换板协议响应异常")
    
    def readCurrent(self,slotNo):
        fm = self.__sendAndRec(self.__buildFrame([0xa3,int(slotNo)]),recvLen=9)
        if fm[0] != 0xb3:raise AbortTestException(message=u"IO切换板协议响应异常")
        return (fm[1]<<8) + fm[2]
    
    def setIndicatorLight(self,slotNo,openOrClose=True):
        fm = self.__sendAndRec(self.__buildFrame([0xa4,int(slotNo),1 if openOrClose else 0]))
        if fm[0] != 0xb4:raise AbortTestException(message=u"IO切换板协议响应异常")

    def getLightState(self,slotNo,color):
        colorCode = {"red":0,"green":1}
        sensorCode = {"red":1,"green":1}
        fm = self.__sendAndRec(self.__buildFrame([0xa7,int(slotNo),sensorCode[color],colorCode[color],0x0a]),recvLen=12)
        if fm[0] != 0xb7:raise AbortTestException(message=u"声光检测板协议响应异常")
        res = (fm[4] << 8) + fm[5]
        return res

    def getSoundState(self,slotNo):
        fm = self.__sendAndRec(self.__buildFrame([0xa8,int(slotNo)]),recvLen=9)
        if fm[0] != 0xb8:raise AbortTestException(message=u"声光检测板协议响应异常")
        return fm[2] == 0

    def __sendAndRec(self,frame,recvLen = 8):
        try:
            self.serialLock.acquire()
            print "->","".join(["%.2x"%x for x in frame]) 
            self.boardSerial.write(frame)

            frameStart = 0
            recvFrame = ["\x55","\xAA"]
            restLen = recvLen - 2
            while True:
                if restLen == 0:break
                n = self.boardSerial.read()
                if n == '': return [0x00]
                if ord(n) == 0x55:frameStart = 1
                elif ord(n) == 0xAA and frameStart == 1:frameStart = 2
                elif frameStart == 2:
                    restLen -= 1
                    recvFrame.append(n)
            print "<-","".join(["%.2x"%ord(x) for x in recvFrame])
            if ord(recvFrame[0]) != 0x55 or ord(recvFrame[1]) != 0xaa:#只判断一下帧头，不管校验了；
                raise AbortTestException(message=u"IO切换板协议响应异常")
            else:
                ln = ord(recvFrame[4])
                data = [ord(x) for x in recvFrame[5:5+ln]]
                return data
        finally:
            self.serialLock.release()
    
    def __buildFrame(self,dataFrame,lens = None):
        #组帧
        self.rsctl += 1
        if self.rsctl > 7:self.rsctl = 0
        if lens is None:lens = len(dataFrame)
        fm = [0x55,0xaa,self.rsctl,0,lens]
        fm.extend(dataFrame)
        fm.append(self.__calcBbc(fm[2:]))
#        fm.append(0x00)
        return bytearray(fm)
    
    def __calcBbc(self,frame):
        #计算校验和
        bbc = 0
        for b in frame:bbc ^= b
        return bbc

class GS11NuLink(TestResource):
    "Nulink工具"
    def __init__(self,initParam):
        self.nulinkId = initParam["linkId"] if "linkId" in initParam else None
        self.cfg0Value = initParam["nulinkCfg0Value"]
        self.cfg1Value = initParam["nulinkCfg1Value"]
    
    def initResource(self):
        if self.nulinkId is None:
            dr = self.__nulinkCmd("-l")
            print dr
            self.nulinkId = dr.split("\n")[0][-10:]
        superUiLog(u"获取NuLinkID:"+self.nulinkId)
    
    def retrive(self):
        pass
    
    def __nulinkCmd(self,cmd):
        '''执行NuLink指令'''
        if self.nulinkId is None:self.nulinkId=""
        fullCmd = "NuLink.exe "+self.nulinkId+ " " +cmd
        superUiLog(u"执行NuLink指令:"+fullCmd)
        r = os.popen(fullCmd)
        dr = r.read()
        print dr
        return dr.strip()
    
    def initCfg(self):
        '''初始化CFG'''
        dr = self.__nulinkCmd("-w CFG0 %s"%self.cfg0Value)
        if "Finish write to CFG0" in dr:uiLog(u"写config0成功")
        else:raise TestItemFailException(failWeight=10,message=u"初始化config0失败")
        dr = self.__nulinkCmd("-w CFG1 %s"%self.cfg1Value)
        if "Finish write to CFG1" in dr:uiLog(u"写config1成功")
        else:raise TestItemFailException(failWeight=10,message=u"初始化config0失败")
    
    
    def downloadBoot(self,versionPathName,verify=True):
        #擦除版本文件
        uiLog(u"开始擦除Boot区")
        dr = self.__nulinkCmd("-e LDROM")
        if "Erase LDROM finish" in dr:
            uiLog(u"擦除Boot区完成，开始写入Boot")
        else:
            raise TestItemFailException(failWeight=10,message=u"Boot区擦除失败")
        #下载版本文件
        dr = self.__nulinkCmd("-w LDROM %s"%versionPathName)
        if "Write LDROM finish" in dr:
            uiLog(u"Boot区下载完成，开始校验")
        else:
            raise TestItemFailException(failWeight=10,message=u"Boot区写入失败")
        #校验版本下载
        if verify:
            dr = self.__nulinkCmd("-v LDROM %s"%versionPathName)
            if "Verify LDROM DATA success" in dr:
                uiLog(u"版本校验通过")
            else:
                raise TestItemFailException(failWeight=10,message=u"Boot区校验失败")
    
    def downloadVersion(self,versionPathName,verify=True):
        '''下载版本'''
        #擦除版本文件
        uiLog(u"开始擦除版本区")
        dr = self.__nulinkCmd("-e APROM")
        if "Erase APROM finish" in dr:
            uiLog(u"擦除版本区完成，开始写入版本")
        else:
            raise TestItemFailException(failWeight=10,message=u"版本区擦除失败")
        #下载版本文件
        dr = self.__nulinkCmd("-w APROM %s"%versionPathName)
        if "Write APROM finish" in dr:
            uiLog(u"版本信息下载完成，开始校验")
        else:
            raise TestItemFailException(failWeight=10,message=u"版本区写入失败")
        #校验版本下载
        if verify:
            dr = self.__nulinkCmd("-v APROM %s"%versionPathName)
            if "Verify APROM DATA success" in dr:
                uiLog(u"版本校验通过")
            else:
                raise TestItemFailException(failWeight=10,message=u"版本区校验失败")
    
    def writeToInfo(self,CONFIG_BUILD_INFO,CONFIG_RF_PARA):
        '''写入信息区，入参是两个信息段，是HEX字符串'''
        toWriteFileInHex = CONFIG_BUILD_INFO+"ff"*48+CONFIG_RF_PARA
        toWriteFileInByte = bytearray([int(toWriteFileInHex[h:h+2],16) for h in range(0,len(toWriteFileInHex),2)])
        hxfile = open("infoData.bin","wb")
        hxfile.write(toWriteFileInByte)
        hxfile.close()
        #擦除Info区
        uiLog(u"开始擦除信息区")
        dr = self.__nulinkCmd("-e DATAROM")
        if "Erase DATAROM finish" in dr:
            uiLog(u"擦除信息区成功")
        else:
            raise TestItemFailException(failWeight=10,message=u"信息区擦除失败")
        
        #写Info区
        uiLog(u"开始写入信息区内容")
        dr = self.__nulinkCmd("-w DATAROM infoData.bin")
        if "Write DATAROM finish" in dr:
            uiLog(u"信息区内容写入完成")
        else:
            raise TestItemFailException(failWeight=10,message=u"信息区写入失败:")
    
    def readInfo(self):
        '''读取信息区，返回整个信息区内容（128byte）的hex符号字符串，即256个字节'''
        TEMP_FILE = "infoData.bin"
        dr = self.__nulinkCmd("-r DATAROM %s"%TEMP_FILE)
        try:
            if "Write DATAROM to FILE: %s Finish"%TEMP_FILE in dr:
                f = open(TEMP_FILE,"rb")
                data = f.read(128)
                f.close()
                return utils.toHex(data)
            else:
                raise TestItemFailException(failWeight=10,message=u"信息区读出失败:")
        finally:
            if os.path.isfile(TEMP_FILE):os.remove(TEMP_FILE)
    
    def resetChip(self):
        '''复位芯片'''
        dr = self.__nulinkCmd("-reset")
        print dr
        if "Chip Reset finish" in dr:
            return
        else:
            raise TestItemFailException(failWeight=10,message=u"芯片复位失败")


    

if __name__ == "__main__":
    PARAM = {"gs11SwitcherSerialPort":"com21"}
    g = GS11ShDigitalBoardSwitcher(None)
    g.initResource()
    
#    g.powerObu("1",True)
#    g.powerObu("2",True)
#    g.setSerialCom("1", False)
#    g.setSerialCom("2", False)
    
#    g.switchCurrentMode("1", 0)
#    g.switchCurrentMode("2", 0)
    v = g.readCurrent("1")
    print v
    
    
#    for i in range(1,7):
#        g.powerObu(str(i), True)
#        g.setSerialCom(str(i), True)
#        g.setIndicatorLight(str(i), True)
#        g.switchCurrentMode(str(i), 0)
#        print 'current=',g.readCurrent(str(i))
#        time.sleep(1)
#        g.powerObu(str(i),False)
#        g.setSerialCom(str(i), False)
#        g.setIndicatorLight(str(i), False)
#        g.switchCurrentMode(str(i), 1)
#        print 'current=',g.readCurrent(str(i))





