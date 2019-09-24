#encoding:utf-8
'''
Created on 2015-1-27
龙岗IO板8I8O的驱动
@author: zws
'''

from hhplt.deviceresource import TestResource,TestResourceInitException
from threading import Thread,RLock
import time
import serial

CMD_PROTOTYPE = [0x00,0x5A,0x56,0x00,None,None,0x00,0x00,None]

class Longgang8I8OBoardDevice(TestResource,Thread):
    
    def __init__(self,initParam):
        Thread.__init__(self)
        self.ioBoardCom = initParam["ioBoardCom"]
        self.serialPortLock = RLock()
        self.runnable = False
        self.buttonTriggerStartTime = 0 #按钮触发开始时间，在时间窗口内，不再响应
        self.inputBuffer = {}   #输入缓存，key:X编号，从0到7；value，通为True，断为False
    
    def initResource(self):
        try:
            self.serialPortLock.acquire()
            if not self.runnable:
                self.boardSerial = serial.Serial(port=self.ioBoardCom,baudrate = 9600,timeout = 2)
                self.boardSerial.setRTS(False)
                self.runnable = True
                self.start()
        except:
            raise TestResourceInitException(u"初始化控制IO板失败，请检查设置并重启软件")
        finally:
            self.serialPortLock.release()
    
    def retrive(self):
        self.runnable = False
        self.boardSerial.close()
        
    def run(self):
        while True:
            try:    
                self.__readAndFillBuffer()
            except Exception,e:
                print e
            finally:
                time.sleep(0.01)
        
    def __readAndFillBuffer(self):
        '''读取IO板的所有输入（X）状态并缓存'''
        self.serialPortLock.acquire()
        try:
            self.boardSerial.write(bytearray([0x00,0x5A,0x56,0x00,0x07,0x00,0x00,0x00,0xB7]))
            rd = self.boardSerial.read(9)
        finally:
            self.serialPortLock.release()
        if rd == "":return
        if self.checkSum(rd[:-1]) != ord(rd[-1]):
            print 'RS485 CHECK SUM ERROR'
            return
#        print "".join(["%.2X"%ord(c) for c in rd])
        if rd is not None:
            mask = 0b00000001
            is_07 = ord(rd[7])
            for i in range(8):
                self.inputBuffer[i] = not bool(is_07 & mask)
                mask = mask << 1
#        print ",".join([("H" if x else "L") for x in self.inputBuffer])
         
            
    def __getitem__(self,x):
        '''获取输入的值，x为X（输入）编号，0到7'''
        try:
            #self.serialPortLock.acquire()
            return self.inputBuffer[x] if x in self.inputBuffer else False
        finally:
            #self.serialPortLock.release()
            pass
    
    def __setitem__(self,y,value):
        '''输出控制，y为Y(输出)编号，0-7，value为True表示通，False表示断'''
        cmd = [x for x in CMD_PROTOTYPE]
        cmd[4] = 0x01 if value else 0x02   #命令：打开
        cmd[5] = y+1  #IO编号1-8
        cmd[8] = self.checkSum(cmd[:-1])
        cmdArray = bytearray(cmd)
        self.serialPortLock.acquire()
        try:
            self.boardSerial.write(cmdArray)
            self.boardSerial.read(9)
        finally:
            self.serialPortLock.release()
        
    def pulseTrigger(self,port):
        '''脉冲触发'''
        self[port] = True
        time.sleep(0.5)
        self[port] = False
        
    def checkSum(self,frame):
        '''计算校验和'''
        csum = 0
        for i in frame:
            if type(i) == str:csum += ord(i)
            else:csum += i  
        return csum % 256    
        
        
if __name__ == '__main__':
    dv = Longgang8I8OBoardDevice({"ioBoardCom":"com3"})
    dv.initResource()
    
    while True:
        time.sleep(1)
        st = []
        for i in range(8):
            st.append(str(dv[i]))
        print ",".join(st)
            
#    while True:
#        for i in range(8):
#            time.sleep(1)
#            dv[i] = True
#            time.sleep(1)
#            dv[i] = False
    
        

        
        
        
        