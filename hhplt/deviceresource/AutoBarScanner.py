#encoding:utf-8
'''
Created on 2014-11-14
条码枪头

@author: 张文硕
'''
from hhplt.parameters import PARAM
import serial
from hhplt.deviceresource import TestResource,TestResourceInitException

MINDEO_SCAN_COMMAND = bytearray([0x03,0x53,0x80,0xff,0x2a,0x00])

#针对民德MINDEO FS 580AT型条码枪头。
#设置如下：
#1、USB虚拟串口模式，应安装配套驱动(P17)
#2、单次触发模式(P21)
#3、解码数据格式-原始格式(P16)
#4、流量控制-ACK/NAK(P15)
class MindeoAutoBarScanner(TestResource):
    def __init__(self,initParam):
        self.barScannerCom = initParam["barScannerCom"]
        
    def initResource(self):
        try:
            self.scannerSerial = serial.Serial(port=self.barScannerCom,baudrate = 9600,timeout = 5)
        except:
            raise TestResourceInitException(u"初始化自动扫描枪失败，请检查设置并重启软件")
    
    def retrive(self):
        self.scannerSerial.close()

    def scan(self):
        '''扫描并获得结果，5秒后仍无结果，则返回None'''
        self.scannerSerial.flushInput()
        self.scannerSerial.write(MINDEO_SCAN_COMMAND)
        result = self.scannerSerial.readline()
        ack = result[0:5]   #暂时用不上
        data = result[5:]
        return data if data !="" else None

#KEYENCE串口扫描枪头
class KeyenceAutoBarScanner(TestResource):
    def __init__(self,initParam):
        self.barScannerCom = initParam["barScannerCom"]
        
    def initResource(self):
        try:
            self.scannerSerial = serial.Serial(port=self.barScannerCom,
                                               baudrate = 9600,
                                               bytesize = 7,
                                               parity = serial.PARITY_EVEN,
                                               stopbits=1,
                                               timeout = 5)
        except:
            raise TestResourceInitException(u"初始化自动扫描枪失败，请检查设置并重启软件")
    
    def retrive(self):
        self.scannerSerial.close()

    def scan(self):
        '''扫描并获得结果，5秒后仍无结果，则返回None'''
        self.scannerSerial.flushInput()
        self.scannerSerial.write("LON\r")
        
        result = []
        while True:
            c = self.scannerSerial.read()
            if c == '':
                self.scannerSerial.write("LOFF\r")
                return None
            elif c == '\x0d':
                break
            else:
                result.append(c)
        return "".join(result)+"\n"


