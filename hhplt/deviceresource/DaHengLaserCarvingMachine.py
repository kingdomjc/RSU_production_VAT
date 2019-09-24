#encoding:utf-8
'''
Created on 2015-1-24
大恒镭雕机数据集成

本地打开一个Socket服务，等待镭雕机请求，请求后，发送给需要雕的数字

@author: zws
'''

from hhplt.deviceresource import TestResource
from hhplt.parameters import PARAM
from threading import RLock,Thread

import socket

class DHLaserCarvingMachine(TestResource,Thread):
    def __init__(self,initParam):
        self.lock = RLock()
        self.isCarved = False
        Thread.__init__(self)
        pass
    
    def initResource(self):
        self.serialCode = None
        self.listening = True
        self.start()
        
    def retrive(self):
        self.listening = False
   
    def run(self):
        self.__dshengCarvingProc()
        
    def __dshengCarvingProc(self):
        HOST = PARAM["carvingMachineHost"]
        PORT = int(PARAM["carvingMachinePort"])
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.listen(50)
        while self.listening:
            conn, addr = s.accept()
            #conn.settimeout(10)
            print 'Connected by', addr
            while self.listening:
                try:
                    data = conn.recv(1024)
                    if not data: break
                    if data == 'TCP:Give me string':
                        try:
                            self.lock.acquire()
                            conn.send(self.__getCarvingCode())
                            self.serialCode = None
                            self.isCarved = True
                        finally:
                            self.lock.release()
                except Exception,e:
                    print str(e)
                    conn.close()
                    break

    def __getCarvingCode(self):
        if self.serialCode is None:
            return " "
        else:
            return self.serialCode
    
    def clearCarveCode(self):
        try:
            self.lock.acquire()
            self.serialCode = None
        finally:
            self.lock.release()

    def toCarveCode(self,code):
        try:
            self.lock.acquire()
            self.serialCode = code
            self.isCarved = False   
        finally:
            self.lock.release()
            
    def carved(self):
        '''是否已经镭雕'''
        try:
            self.lock.acquire()
            return self.isCarved
        finally:
            self.lock.release()

