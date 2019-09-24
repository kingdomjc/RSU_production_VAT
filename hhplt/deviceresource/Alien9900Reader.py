#encoding:utf-8
'''
Created on 2014-12-26
Alien9900+超高频读写器驱动
用于超高频标签的读写测试
@author: zws
'''
from hhplt.deviceresource import TestResource,TestResourceInitException
from socket import *
import time

USERNAME = "alien"
PASSWORD = "password"

class Alien9900Reader(TestResource):
    def __init__(self,initParam):
        self.ip = initParam["readerIp"]
        self.port = initParam["readerPort"]
        self.access_password = initParam["accessPassword"]  #暂时用不上
    
    def initResource(self):
        self.comm = socket(AF_INET, SOCK_STREAM)
        self.comm.settimeout(0.2)
        try:
            self.comm.connect((self.ip,self.port))
        except:
            raise TestResourceInitException(u"初始化阅读器失败，请检查设置并重启软件")
        
        while True:
            try:
                time.sleep(0.1)
                rst = self.comm.recv(1024)
                if rst.endswith("Username>\x00"):
                    self.comm.send(USERNAME+"\n")
                elif rst.endswith("Password>\x00"):
                    self.comm.send(PASSWORD+"\n")
                elif not rst.endswith("Alien>\x00"):
                    raise TestResourceInitException(u"初始化阅读器失败，请检查设置并重启软件")
                else:
                    break
            except Exception,e:
                print e
                raise TestResourceInitException(u"阅读器连接失败，请检查设置并重启软件")
                
    def retrive(self):
        self.comm.close()
        del self.comm
    
    def __receive(self):
        try:
            rst = self.comm.recv(1024)
            return rst
        except:
            return ""
    
    def inventry6CTag(self):
        '''清点6C标签'''
        self.comm.send("t\r\n")
        
        for i in range(5):
            rst = self.__receive()
            if "Tag" in rst:
                break
            time.sleep(0.05)
        
        inventoryResultList = []
        
        lines = rst.split("\n")
        for line in lines:
            if line.startswith("Tag:"):
                tag = line.split(",")[0][4:].replace(" ","")
                inventoryResultList.append(tag)
        return inventoryResultList
        
    def read(self,epc,bank,length,offset=0):
        cmd = "g2read = %d %d %d\r\n"%(bank,offset,length)
        self.comm.send(cmd)
        for i in range(5):
            rst = self.__receive()
            if "G2Read" in rst:
                break
            time.sleep(0.1)
        startIndex = rst.index("G2Read = ")
        return rst[startIndex+8:].replace(" ","")[:length*4]
    
    def __toSpaceSplittedStr(self,data):
        byteArrayStr = []
        for i in range(0,len(data),2):
            b = data[i]+data[i+1]
            byteArrayStr.append(b)
        return " ".join(byteArrayStr)
    
    def write(self,epc,bank,offset,writeData):
        formattedData = self.__toSpaceSplittedStr(writeData)
        cmd = "g2write = %d %d %s\r\n"%(bank,offset,formattedData)
        self.comm.send(cmd)
        time.sleep(0.1)
        for i in range(5):
            rst = self.__receive()
            if "G2Write" in rst:
                break
            time.sleep(0.1)
        return "G2Write = Success!" in rst
        
        
        
        
        