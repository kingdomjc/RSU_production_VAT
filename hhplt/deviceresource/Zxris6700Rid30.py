#encoding:utf-8
'''
Created on 2014-12-12
ZXRIS 6700 基于RID30的设备驱动
用于南京环保卡等工装环境

@author: zws
'''
from hhplt.deviceresource import TestResource,TestResourceInitException
from ctypes import *
import time

def toHexStr(dataarray):
    return "".join(["%.2X"%int(c) for c in dataarray])

def toByteArray(datastr):
    g = []
    for i in range(0,len(datastr),2):
        g.append(int(datastr[i]+datastr[i+1],16))
    return g
    

class InventoryResult(Structure):
    '''清点结果结构体'''
    _pack_ = 1
    _fields_ = [
                ("length",c_int),
                ("tagData",c_ubyte*2048)
                ]

class EPC1G2_TagID(Structure):
    '''EPC标签标识'''
    _pack_ = 1
    _fields_ = [
                ("tagDataLen",c_short),
                ("aucTagData",c_ubyte*32)
                ]

class EPC1G2_TagRead(Structure):
    '''EPC读参数'''
    _pack_ = 1
    _fields_ = [
                ("antennaID",c_short),
                ("memBank",c_short),
                ("dataLen",c_short),
                ("wordPointer",c_int),
                ("accessPassword",c_int),
                ("tTagID",EPC1G2_TagID)
                ]

class EPC1G2_TagWrite(Structure):
    '''写标签数据数据结构'''
    _pack_ = 1
    _fields_ = [
                ("antennaID",c_short),
                ("memBank",c_short),
                ("accessPassword",c_int),
                ("wordPointer",c_int),
                ("dataLen",c_short),
                ("data",c_ubyte*512),
                ("tagID",EPC1G2_TagID)
                ] 



class ReadOpResult(Structure):
    '''标签读取结果结构'''
    _pack_ = 1
    _fields_ = [
                ("result",c_int),
                ("antennaID",c_short),
                ("dataLen",c_short),
                ("readData",c_ubyte*512)
                ]

class Zxris6700_rid30(TestResource):
    def __init__(self,initParam):
        self.ip = initParam["readerIp"]
        self.port = initParam["readerPort"]
        self.rid_dll = windll.LoadLibrary("6700RID30.dll")
        self.access_password = initParam["accessPassword"]
    
    def initResource(self):
        self.c_fd = c_int(0)
        res = self.rid_dll.Connect(("%s:%d"%(self.ip,self.port)).encode(),byref(self.c_fd))
        if res != 0:
            #RID有时候脾气不好，所以如果失败，再试一次，再失败就不行了
            res = self.rid_dll.Connect(("%s:%d"%(self.ip,self.port)).encode(),byref(self.c_fd))
            if res != 0:
                print u'初始化6700失败，rtn=',res
                raise TestResourceInitException(u"初始化阅读器失败，请检查设置并重启软件")
    
    def retrive(self):
        self.rid_dll.Disconnect(self.c_fd)
    
    def inventry6CTag(self):
        '''清点6C标签，返回[EPC1,EPC2……]'''
        result = InventoryResult()
        res = self.rid_dll.EPC1G2_Inventory(self.c_fd,c_short(0),byref(result))
#        print 'inv res = ',res
        length = result.length
#        print "alllength:",length
        
        inventoryResultList = []
        
        tagIds = result.tagData[:length]
        i = 0
        while i < length:
#            print "-"*10
#            print tagIds[i]
            tagLen = tagIds[i]*2    #EPC中的长度单位是字，这里转换成字节
#            print "tagidlen:",tagLen
            tagId = tagIds[i+1:i+tagLen+1]
#            print repr(tagId)
            print toHexStr(tagId)
            i = i + tagLen + 1
            inventoryResultList.append(toHexStr(tagId))
        return inventoryResultList
    
    def read(self,epc,bank,length,offset=0):
        '''读取标签区'''
        readParam = EPC1G2_TagRead()
        readParam.antennaID = 0
        readParam.memBank = bank
        readParam.dataLen = length
        readParam.wordPointer = offset
        readParam.accessPassword = int(self.access_password,16)
               
        #这里非常奇怪，如果不指定EPC，则可以读；否则阅读器返回-1
#        tagIdArray = toByteArray(epc)
#        readParam.tTagID.tagDataLen = len(tagIdArray)/2
#        for i in range(len(tagIdArray)):
#            readParam.tTagID.aucTagData[i] = tagIdArray[i]

        readOpResult = ReadOpResult()
        
        res = self.rid_dll.EPC1G2_ReadTag(self.c_fd,byref(readParam),byref(readOpResult))
#        print 'read res=',res
        
        result = readOpResult.result
#        print 'read result=',result
        dataLen = readOpResult.dataLen
        dataArray = readOpResult.readData[:dataLen*2]
        return toHexStr(dataArray)
    
    def write(self,epc,bank,offset,writeData):
        '''写数据'''
        toWriteByteArray = toByteArray(writeData)
        
        writePara = EPC1G2_TagWrite()
        writePara.antennaID = 0
        writePara.memBank = bank
        writePara.accessPassword = int(self.access_password,16)
        writePara.wordPointer = offset
        writePara.dataLen = len(toWriteByteArray)/2 #转换成字
        for i in range(len(toWriteByteArray)):
            writePara.data[i] = toWriteByteArray[i]
        
        tagIdArray = toByteArray(epc)
        writePara.tagID.tagDataLen = len(tagIdArray)/2
        for i in range(len(tagIdArray)):
            writePara.tagID.aucTagData[i] = tagIdArray[i]
        
        writeResult = c_int()
        res = self.rid_dll.EPC1G2_WriteTag(self.c_fd,byref(writePara),byref(writeResult))
#        print 'write res=',res
        return res == 0 and writeResult.value == 0 