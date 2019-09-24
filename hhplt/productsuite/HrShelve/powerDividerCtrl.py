#encoding:utf-8
"""
模块: 功分器测试工装板
用于测试过程中切换矢网仪与功分器端口的板子




功分板和工装的接线对应如下：

--------------------------------------
|         功分                      |
|  4    3    2    1    6    5       |
--------------------------------------
   |    |    |    |    |    |
   |    |    |    |    |    |
-------------------------------------
|  6    5    4    3    2    1       |
|       工装板                      |
-------------------------------------

@author:zws
"""
import serial

from hhplt.deviceresource import TestResource
from hhplt.testengine.exceptions import AbortTestException

PORT_MAP = {4:6,3:5,2:4,1:3,6:2,5:1}


class PowerDividerCtrl(TestResource):
    def __init__(self,param):
        self.param = param
        self.powerDividerCtrlCom = param["powerDividerCtrlCom"]
        self.boardSerial = None
        self.currentRsctl = 0

    def __fetchRsctl(self):
        self.currentRsctl += 1
        self.currentRsctl %= 0xFF
        return self.currentRsctl

    def initResource(self):
        #初始化资源
        self.boardSerial = serial.Serial(port=self.powerDividerCtrlCom,baudrate = 115200,timeout = 1)

    def retrive(self):
        #回收资源
        self.boardSerial.close()

    @staticmethod
    def __calcBcc(frame):
        return reduce(lambda x,y:x^y,frame,0)

    def switchToPort(self,port):
        # 切换至端口
        ctrlPort = PORT_MAP[port]
        frame = [0x55,0xaa,self.__fetchRsctl(),0x00,01,0xCD,ctrlPort]
        frame.append(self.__calcBcc(frame[2:]))
        self.boardSerial.flush()
        self.boardSerial.write(bytearray(frame))
        res = self.boardSerial.read(8)
        if ord(res[2]) != self.currentRsctl or ord(res[6]) != 0x00:   #切换失败
            raise AbortTestException(message = u'工装切换通道%d失败'%ctrlPort)
