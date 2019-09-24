#encoding:utf-8
'''
Created on 2015-1-26
鑫宇XYS-1210型继电器板驱动
@author: zws
'''
from hhplt.deviceresource import TestResource,TestResourceInitException,askForResource
from threading import Thread,RLock
import time
import serial

TRIGGER_WIDTH = 0.5 #输出脉冲宽度

READ_ALL_INPUT_COMMAND = bytearray([0x01,0x02,0x00,0x00,0x00,0x08,0x79,0xCC])

def crc16(x):
    b = 0xA001
    a = 0xFFFF
    for byte in x:
        a = a^byte
        for i in range(8):
            last = a%2
            a = a>>1
            if last ==1: a = a^b
    aa = '0'*(6-len(hex(a)))+hex(a)[2:]
    ll,hh = int(aa[:2],16),int(aa[2:],16)
    return [hh,ll]

#开关量板行为如下：
#输入柱以X表示，使用X1-X8，初始输入为高，表示与地（P-）不导通，将Xn与P-导通，则输入为低；
#输出柱以Y表示，使用Y1-Y8，初始为继电器断开，输出高后，继电器合上，使用万用表可量到初始电阻为无穷大，导通后为0

class XinyuIOBoardDevice(TestResource,Thread):
    '''鑫宇开关量IO板设备'''
    def __init__(self,initParam):
        Thread.__init__(self)
        self.impl = initParam["impl"]
        self.ioBoardCom = initParam["ioBoardCom"]
        self.lock = RLock()
        self.runnable = False
        self.buttonTriggerStartTime = 0 #按钮触发开始时间，在时间窗口内，不再响应
        self.inputResult = [True]*12   #初始为高，12个高，当前只用前8个
            
    def initResource(self):
        try:
            self.lock.acquire()
            if not self.runnable:
                self.boardSerial = serial.Serial(port=self.ioBoardCom,baudrate = 9600,timeout = 5)
                self.runnable = True
                self.start()
        except:
            raise TestResourceInitException(u"初始化控制IO板失败，请检查设置并重启软件")
        finally:
            self.lock.release()
    
    def retrive(self):
        self.runnable = False
        self.boardSerial.close()

    def __readAllInput(self):
        '''读取全部输入量'''
        self.boardSerial.flushInput()
        self.boardSerial.write(READ_ALL_INPUT_COMMAND)
        response = self.boardSerial.read(size = 6)
        if response != "":
            res = response[3]
            self.__setResultToInputBuffer(res)
        
    def __setResultToInputBuffer(self,res):
        '''将结果保存到self.inputResult中，入参是一个字节的字符串，如\xFE'''
        resultByte = ord(res)
        mask = 0b00000001
        for i in range(9):
            self.inputResult[i+1] = bool(resultByte & mask)
            mask = mask << 1
    
    def outputSinglePort(self,address,output):
        '''单路输出，address为外接线柱地址，1-8，output为开关，False表示断开继电器，True表示导通'''
        cmd= [0x01,0x0f,0x00,address-1,0x00,0x01,0x01,0x01 if output else 0x00]
        crc = crc16(cmd)
        cmd.extend(crc)
        try:
            self.lock.acquire()
            self.boardSerial.flushInput()
            self.boardSerial.flushOutput()
            self.boardSerial.write(cmd)
            response = self.boardSerial.read(size=8)
            #暂时不关心返回
        finally:
            self.lock.release()
    
    def run(self):
        while self.runnable:
            time.sleep(0.3)
            try:
                self.lock.acquire()
                self.__readAllInput()
                self.impl.processInput()
            except:
                pass
            finally:
                self.lock.release()
    
    def triggerInPulse(self,channel,width=None):
        '''脉冲触发'''
        self.outputSinglePort(channel,True)
        time.sleep(TRIGGER_WIDTH if width is None else width)
        self.outputSinglePort(channel,False)
    
    
