#encoding:utf-8
'''
Created on 2015-1-27
龙岗IO板 16I16O的驱动
@author: zws
'''

from hhplt.deviceresource import TestResource,TestResourceInitException,askForResource
from threading import Thread,RLock
import time
import serial

TRIGGER_WIDTH = 0.5 #输出脉冲宽度

def checkSum(frame):
    sum = 0
    for i in frame:
        if type(i) == str: 
            sum = sum + ord(i)
        else:
            sum = sum +i  
    return sum % 256

CMD_PROTOTYPE = [0x00,0x5A,0x61,0x00,0x01,0x00,0x10,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xCC]
#命令原型，长度16字节，Y7..Y0为[5]    Y15..Y8  为[6]  

READ_CMD = [0x00 ,0x5A ,0x61 ,0x00 ,0x07 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0xC2]

class LonggangIOBoardDevice(TestResource,Thread):
    '''龙岗开关量IO板设备'''
    def __init__(self,initParam):
        Thread.__init__(self)
        self.impl = initParam["impl"]
        self.ioBoardCom = initParam["ioBoardCom"]
        self.lock = RLock()
        self.runnable = False
        self.buttonTriggerStartTime = 0 #按钮触发开始时间，在时间窗口内，不再响应
        self.inputResult = [True]*17   #初始为高，12个高，当前只用前8个，虽然本板默认输入为低，但仍使用True来表示初始状态，以使上层兼容龙鑫的设备
    
    def initResource(self):
        try:
            self.lock.acquire()
            if not self.runnable:
                self.boardSerial = serial.Serial(port=self.ioBoardCom,baudrate = 9600,timeout = 1)
                self.boardSerial.setRTS(False)
                self.runnable = True
                self.start()
        except:
            raise TestResourceInitException(u"初始化控制IO板失败，请检查设置并重启软件")
        finally:
            self.lock.release()
    
    def retrive(self):
        self.runnable = False
        self.boardSerial.close()
    
    def outputSinglePort(self,address,output):
        '''单路输出，address为外接线柱地址，1-16，output为开关，False表示断开继电器，True表示导通'''
        cmd = [0x00,0x5A,0x61,0x00,0x01 if output else 0x02,
               0x00,0x00,
               0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
               0x00]
        if address >=0 and address <8:
            cmd[5] = 0b00000001 << address
        elif address >=8 and address <16:
            cmd[6] = 0b00000001 << (address-8)
        cmd[15] = (checkSum(cmd))
        try:
            self.lock.acquire()
            self.boardSerial.write(bytearray(cmd))
            inputStatus = self.boardSerial.read(16)
        finally:
            self.lock.release()

    def outputMultiPort(self,address,output):
        '''多路输出，address为外接线柱地址，1-16，output为开关，False表示断开继电器，True表示导通'''
        cmd = [0x00,0x5A,0x61,0x00,0x01 if output else 0x02,
               0x00,0x00,
               0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
               0x00]
        for ad in address:
            if ad >=0 and ad <8:
                cmd[5] |= (0b00000001 << ad)
            elif ad >=8 and ad <16:
                cmd[6] |= (0b00000001 << (ad-8))
        cmd[15] = (checkSum(cmd))
        try:
            self.lock.acquire()
            self.boardSerial.write(bytearray(cmd))
            inputStatus = self.boardSerial.read(16)
        finally:
            self.lock.release()

    def triggerInPulse(self,address,width=None):
        '''单路输出，address为外接线柱地址'''
        self.outputSinglePort(address,True)
        time.sleep(TRIGGER_WIDTH if width is None else width)
        self.outputSinglePort(address,False)


    def run(self):
        last = None
        while self.runnable:
            try:
                try:
                    self.lock.acquire()
                    self.boardSerial.write(bytearray("\x00\x5A\x61\x00\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xC2"))
                    inputStatus = self.boardSerial.read(16)
                finally:
                    self.lock.release()

                if self.__checkSum(inputStatus):
                    self.__readAllInput(inputStatus)
                    cnt =  " | ".join(map(lambda x:str(x),self.inputResult))
                    if cnt != last:
                        last = cnt
                        print cnt
                    self.impl.processInput()
                elif len(inputStatus) != 0:
                    print 'check sum error'
            except Exception,e:
                print e


    def __checkSum(self,inputStatus):
        if len(inputStatus) == 0 :
            return False
        return checkSum(inputStatus[:-1]) == ord(inputStatus[-1])
    
    def __readAllInput(self,inputStatus):
        mask = 0b00000001
        is_07 = ord(inputStatus[7])
        for i in range(8):
            self.inputResult[i] = not bool(is_07 & mask)
            mask = mask << 1
            
        mask = 0b00000001
        is_815 = ord(inputStatus[8])
        for i in range(8,16):
            self.inputResult[i] = not bool(is_815 & mask)
            mask = mask << 1


    def __getitem__(self, x):
        return not self.inputResult[x]

    def __setitem__(self,y,value):
        self.outputSinglePort(y,value)

    