#encoding:utf-8
'''
Created on 2019-04-29
OBU tc56
@author: lwl
'''
from hhplt.deviceresource import TestResource,TestResourceInitException
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
import socket
import struct

class Tc56Message:
    def __init__(self):
        self.buf=[]
        self.bytes=''
    def set(self,rsctl,cmd,data):
        self.buf = [0x55,0xaa,rsctl,0,0,cmd]
        self.buf[4]=len(data)
        self.buf=self.buf+data
        bcc= self.__calcBCC(self.buf)
        self.buf.append(bcc)

    # 获取消息字节流
    def getBytes(self):
        if len(self.buf)<9:
            return ''
        return struct.pack(str(len(self.buf)) + "B", *self.buf)
    #获取消息类型
    def getCmd(self):
        if len(self.buf)<9:
            return -1
        else:
            return self.buf[5]
    #按位获取消息体数据
    def getData(self,index):
        if len(self.buf)<9:
            return -1
        else:
            return self.buf[6+index]
    def __calcBCC(self,bytes):
        #计算校验和
        bbc = 0
        for b in bytes:bbc ^= b
        return bbc
    #添加字节流并截取一个完整的消息字节流，返回剩余的字节流
    def appendBytes(self,bytes):
        self.buf += struct.unpack(str(len(bytes)) + "B", bytes)
        # 截取55AA开头
        if not self.__get55AA():
            return ''
        if len(self.buf) < 9:  # 消息长度不能少于9
            return ''
        # 截取完整消息
        length = self.buf[4]+7
        if len(self.buf) < length:  # 消息不完整
            return ''
        # 截取剩余的字节流
        bytes = self.buf[length:]
         # 截取完整消息
        bcc = self.buf[length-1]
        self.buf = self.buf[0:length]
        if bcc != self.__calcBCC(self.buf[0:-1]):
            self.buf=[]
            print "空不空"
        return struct.pack(str(len(bytes)) + "B", *bytes)

    def isSucceed(self):    #返回消息结果是否成功
        return  True if 0 == self.buf[-2] else False
    #截取55AA开头字段，并删除无用字节
    def __get55AA(self):
        #截取55AA开头
        length = len(self.buf) - 1
        while length > 1:
            if 0x55 ==self.buf[0] and 0xAA == self.buf[1]:
                return True
            else:
                del (self.buf[0])
                length -= 1
        return False

#OBU_tc56设备
class OBU_tc56(TestResource):
    def __init__(self, initParam):
        self.ip=initParam["ip"]
        self.port=initParam["port"]
        self.msg = Tc56Message()
        self.bytes=''
    def initResource(self):
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.skt.connect((self.ip,self.port))
        except:
            raise AbortTestException(message = u'OBU服务端连接异常')

    def retrive(self):
        self.skt.close()
        self.bytes=''

    def send(self,rsctl,cmd,data):
        self.msg.set(rsctl,cmd,data)
        try:
            self.skt.send(self.msg.getBytes())
        except:
            raise AbortTestException(message = u'OBU服务端连接异常')

    def recv(self):
        try:
            self.bytes += self.skt.recv(1024)
            self.bytes = self.msg.appendBytes(self.bytes)
            return self.msg
        except:
            raise AbortTestException(message = u'OBU服务端连接异常')



