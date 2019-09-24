#encoding:utf-8
'''
Created on 2014-12-12

GS15测试设备
基于ZXRIS 6700 RID 30

@author: user
'''
from hhplt.testengine.server import serverParam as SP
from hhplt.deviceresource import TestResource

from threading import Thread,RLock
from hhplt.deviceresource import askForResource
from hhplt.testengine.autoTrigger import AbstractAutoTrigger
from hhplt.parameters import PARAM


MEM_BANK_RESERVED = 0
MEM_BANK_EPC = 1
MEM_BANK_TID = 2
MEM_BANK_USER = 3

class GS15ReaderDevice(TestResource):
    def __init__(self,param):
        if PARAM["readerType"] == "zte6700rid30":
            from hhplt.deviceresource import Zxris6700Rid30
            self.reader = Zxris6700Rid30.Zxris6700_rid30(param)
        elif PARAM["readerType"] == "alien9900":
            from hhplt.deviceresource import Alien9900Reader
            self.reader = Alien9900Reader.Alien9900Reader(param)
        elif PARAM["readerType"] == "zxris6700Rid50Impinj":
            from hhplt.deviceresource import Zxris6700Rid50Impinj
            self.reader = Zxris6700Rid50Impinj.Zxris6700_rid50_impinj(param)
            
        self.lock = RLock()
        self.runnable = False
        self.lastTid = None #上一次读到的TID
        self.lastEpc = None #上次读到的EPC
        self.nowTid = None  #本次读到的TID
        self.nowEpc = None  #本次清点到的EPC
    
    def initResource(self):
        self.reader.initResource()
    
    def retrive(self):
        self.reader.retrive()
    
    def inventory(self):
        try:
            self.lock.acquire()
            self.lastEpc = self.nowEpc
            self.nowEpc = self.reader.inventry6CTag()
            return self.nowEpc
        finally:
            self.lock.release()
    
    def readTid(self):
        try:
            self.lock.acquire()
            self.lastTid = self.nowTid
            self.nowTid = self.reader.read(self.__getNowSingleEpc(), MEM_BANK_TID, PARAM["gs15tidLength"], 0)
            return self.nowTid
        finally:
            self.lock.release()
    
    def __getNowSingleEpc(self):
        return self.nowEpc[0] if self.nowEpc is not None else ""
    
    def readUser(self,length,offset):
        try:
            self.lock.acquire()
            wholeUser = self.reader.read(self.__getNowSingleEpc(), MEM_BANK_USER,length,offset)
            return wholeUser
        finally:
            self.lock.release()
    
    def readWholeUser(self):
        try:
            self.lock.acquire()
            wholeUser = self.reader.read(self.__getNowSingleEpc(), MEM_BANK_USER, PARAM["gs15userLength"], 0)
            return wholeUser
        finally:
            self.lock.release()
    
    def writeToEpc(self,data):
        try:
            self.lock.acquire()
            result = self.reader.write(self.__getNowSingleEpc(), MEM_BANK_EPC,2,data)
            return result
        finally:
            self.lock.release()
    
    def writeToUser(self,data,offset = 0):
        try:
            self.lock.acquire()
            result = self.reader.write(self.__getNowSingleEpc(), MEM_BANK_USER,offset,data)
            return result
        finally:
            self.lock.release()
    
    #以下接口是为兰州电子车牌工装测试新增的，目前可能仅由Zxris6700Rid50Impinj支持，其余阅读器为测试，上层慎用
    def clearKillPassword(self):
        '''清空密码区,成功返回true，失败返回false'''
        try:
            self.lock.acquire()
            result = self.reader.write(self.__getNowSingleEpc(),MEM_BANK_RESERVED,0,"00000000")
            return result == 0
        finally:
            self.lock.release()
    
    def getKillPassword(self):
        '''获得密码区的值，返回密码区hex字串，失败返回None'''
        try:
            self.lock.acquire()
            password = self.reader.read(self.__getNowSingleEpc(), MEM_BANK_RESERVED, 2, 0)
            return password
        finally:
            self.lock.release()
            
    def permanentLockKillPassword(self):
        '''永久锁定密码区'''
        try:
            self.lock.acquire()
            return self.reader.lockKillPassword(self.__getNowSingleEpc())
        finally:
            self.lock.release()
        
    def qtToPrivate(self):
        '''转换到私有模式'''
        try:
            self.lock.acquire()
            if self.reader.isQtStatePublic(self.__getNowSingleEpc()):
                res = self.reader.qtToPrivate(self.__getNowSingleEpc())
                self.inventory()    #如果真正发生了转换，要重新清点一次
                return res
            else:
                return True
        finally:
            self.lock.release()
    
    def qtToPublic(self):
        '''转换到公有模式'''
        try:
            self.lock.acquire()
            if not self.reader.isQtStatePublic(self.__getNowSingleEpc()):
                res = self.reader.qtToPublic(self.__getNowSingleEpc())
                self.inventory()
                return res
            else:
                return True
        finally:
            self.lock.release()
        
    def writeToTid(self,data,offset=6):
        '''写TID区，data数据（HEX字符串），offset偏移（字）'''
        try:
            self.lock.acquire()
            result = self.reader.write(self.__getNowSingleEpc(),MEM_BANK_TID,offset,data)
            return result
        finally:
            self.lock.release()

class TagInventoryTrigger(AbstractAutoTrigger):
    def __init__(self):
        AbstractAutoTrigger.__init__(self)
        self.readerDevice = askForResource("GS15ReaderDevice", GS15ReaderDevice,
                          readerIp=PARAM["gs15ReaderIp"],
                          readerPort = PARAM["gs15ReaderPort"],
                          accessPassword = PARAM["gs15accessPassword"]
                          )
        self.nowTid = None
        self.nowEpc = None
#        self.noTagStopped = True
    
    def _checkIfStart(self):
        ir = self.readerDevice.inventory()
        if len(ir) == 1:
            nowEpc = ir[0]
            if self.nowEpc != nowEpc:
                return True
            else:
                nowTid = self.readerDevice.readTid()
                if nowTid != "" and nowTid != self.nowTid:
                    return True
        return False
        
    def _checkIfStop(self):
        ir = self.readerDevice.inventory()
        if len(ir) == 0:
            self.noTagStopped = True
            return True
        elif len(ir) != 1:
            self.noTagStopped = False
            return True
        elif ir[0] != self.nowEpc:
            self.noTagStopped = False
            return True
        else:
            nowTid = self.readerDevice.readTid()
            if nowTid != "" and nowTid != self.nowTid:
                return True
        return False
    
    
    
    
        
        