#encoding:utf-8
'''
Created on 2015-5-6

基于ZXRIS 6700阅读器，RID50的Impinj标签操作指令
用于兰州标签的操作

@author: zws
'''
from hhplt.deviceresource import TestResource,TestResourceInitException
from ctypes import *
from hhplt.parameters import PARAM


def toHexStr(dataarray):
    return "".join(["%.2X"%int(c) for c in dataarray])

class Antenna(Structure):
    '''天线结构体'''
    _pack_ = 1
    _fields_ = [
                ("antenna",c_ubyte*4)
                ]

class TagInfo(Structure):
    '''标签信息'''
    _pack_ = 1
    _fields_ = [
               ("antennaID",c_short), 
               ("tagIDLen",c_short),
               ("tagID",c_ubyte*64)
                ]

class InventoryResult(Structure):
    '''清点结果结构体'''
    _pack_ = 1
    _fields_ = [
                ("num",c_int),
                ("tagInfo",TagInfo*2048)
                ]

class ISO_6C_TagID(Structure):
    '''6C标签TAGID'''
    _pack_ = 1
    _fields_ = [
                ('tagDataLen',c_int),   #标签数据长度，以字节为单位
                ('aucTagData',c_ubyte*64)  #变长EPC数据的第一个数据段
                ]
    
class TagMode(Structure):
    '''标签公私有模式结构体'''
    _pack_ = 1
    _fields_ = [
                ("antennaID",c_int),    #天线号    
                ("dataProfile",c_int),  #公私有转化方向，0-私转公，1-公转私，
                ("persistence",c_int),  #公私有转换性质，0-临时转换，1-永久转换
                ("accessPassword",c_ubyte*4),   #操作密码，4个字节
                ("tagID",ISO_6C_TagID)  #标签ID
                ]
    
class ISO_6C_TagRead(Structure):
    '''ISO18000-6-C读参数'''
    _pack_ = 1
    _fields_ = [
                ("antennaID",c_int),    #天线号
                ("memBank",c_int),  #0-密码区；1-EPC；3-User
                ("offset",c_int),   #写起始地址，不能为奇数
                ("length",c_int),   #长度，单位字节,不能为奇数
                ("accessPassword",c_ubyte*4),   #操作密码，4个字节
                ("tagID",ISO_6C_TagID)  #标签ID  
                ]

class ReadResult(Structure):
    '''ISO18000-6-C读结果'''
    _pack_ = 1
    _fields_ = [
                ("dataLen",c_int),  #数据长度，以字节为单位。
                ("readData",c_ubyte*512)    #读取结果
                ]

class ISO_6C_TagWrite(Structure):
    '''ISO18000-6-C写参数'''
    _pack_ = 1
    _fields_ = [
                ("antennaID",c_int),    #天线号
                ("memBank",c_int),  #0-密码区；1-EPC；3-User
                ("offset",c_int),   #写起始地址，不能为奇数
                ("length",c_int),   #长度，单位字节,不能为奇数
                ("accessPassword",c_ubyte*4),   #操作密码，4个字节
                ("data",c_ubyte*512),    #写内容
                ("tagID",ISO_6C_TagID)  #标签ID  
                ]

class ISO_6C_TagLock(Structure):
    _pack_ = 1
    _fields_ = [
                ("antennaID",c_int),    #天线号
                ("killBankOp",c_int),    #杀死密码区域锁定操作。
                ("accessBankOp",c_int), #操作密码区域锁定操作。
                ("epcBankOp",c_int),    #EPC区锁定操作
                ("tidBankOp",c_int),    # TID区锁定操作  
                ("userBankOp",c_int),   #USER区锁定操作。
                ("accessPassword",c_ubyte*4),   #操作密码，4个字节
                ("tagID",ISO_6C_TagID)  #标签ID  
                ]
    #注意：killBankOp、accessBankOp、epcBankOp、tidBankOp和userBankOp的
    #取值范围是[0,4]，其含义分别是：0：不操作；1：锁定；2：永久锁定3：永久解锁；4：解锁。


class TagModeQuery(Structure):
    _pack_ = 1
    _fields_ = [
                ("antennaID",c_int),    #天线号    
                ("accessPassword",c_ubyte*4),   #操作密码，4个字节
                ("tagID",ISO_6C_TagID)  #标签ID  
                ]

allAntenna = Antenna()  #清点用天线参数
allAntenna.antenna[0] = c_ubyte(1)
allAntenna.antenna[1] = c_ubyte(1)
allAntenna.antenna[2] = c_ubyte(0)
allAntenna.antenna[3] = c_ubyte(0)    #全天线检查，目前只启用1/2天线


class Zxris6700_rid50_impinj(TestResource):
    def __init__(self,initParam):
        self.ip = initParam["readerIp"]
        self.port = initParam["readerPort"]
        self.rid_dll = windll.LoadLibrary("6700RID40.dll")
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
        result = InventoryResult()  #清点结果容器
        res = self.rid_dll.Impinj_Invent(self.c_fd,byref(allAntenna),byref(result))
        return [toHexStr(result.tagInfo[i].tagID[:result.tagInfo[i].tagIDLen]) 
                for i in range(result.num)] if res == 0 else []
    
    def __setAntennaAndTagId(self,para,epc):
        '''设置标签操作参数中的天线、accesspassword和epc（天线下只会存在一个标签的）'''
        para.antennaID = PARAM["antennaId"]
        for i in range(4):
            para.accessPassword[i] = int(self.access_password[2*i:2*i+2],16)
        epcLen = len(epc)/2 #6700rid使用的单位是字节，入参epc是HEX符号
        para.tagID.tagDataLen = epcLen
        for i in range(epcLen):
            para.tagID.aucTagData[i] = int(epc[2*i:2*i+2],16)
    
    def read(self,epc,bank,length,offset=0):
        '''读取标签区'''
        readPara = ISO_6C_TagRead()
        readPara.memBank = bank
        readPara.offset = offset*2  #外面单位是字，6700要字节
        readPara.length = length*2  
        self.__setAntennaAndTagId(readPara, epc)
        readResult = ReadResult()   #读结果容器
        res = self.rid_dll.Impinj_Read(self.c_fd,byref(readPara),byref(readResult))
        return toHexStr(readResult.readData[:readResult.dataLen]) if res == 0 else None
        
    def write(self,epc,bank,offset,writeData):
        '''写数据'''
        writePara = ISO_6C_TagWrite()
        writePara.memBank = bank
        writePara.offset = offset*2  #外面单位是字，6700要字节
        writePara.length = len(writeData)/2
        self.__setAntennaAndTagId(writePara, epc)
        for i in range(len(writeData)/2):
            writePara.data[i] = int(writeData[i*2:i*2+2],16)
        return self.rid_dll.Impinj_Write(self.c_fd,byref(writePara)) == 0
    
    def lockKillPassword(self,epc):
        '''永久锁KillPassword'''
        lockPara = ISO_6C_TagLock()
        lockPara.killBankOp = 2
        lockPara.accessBankOp = 0
        lockPara.epcBankOp = 0
        lockPara.tidBankOp = 0
        lockPara.userBankOp = 0
        self.__setAntennaAndTagId(lockPara, epc)
        res = self.rid_dll.Impinj_Lock(self.c_fd,byref(lockPara))
        return res == 0

    def isQtStatePublic(self,epc):
        '''检查是否处于公有模式下'''
        qtState = c_int(0)
        tagModeQuery = TagModeQuery()
        self.__setAntennaAndTagId(tagModeQuery, epc)
        res = self.rid_dll.Impinj_GetMode(self.c_fd,byref(tagModeQuery),byref(qtState))
        return qtState.value == 1
    
    def qtToPrivate(self,epc):
        '''转到私有模式'''
        tagMode = TagMode()
        tagMode.dataProfile = 0
        tagMode.persistence = 1
        self.__setAntennaAndTagId(tagMode, epc)
        return self.rid_dll.Impinj_SetMode(self.c_fd,byref(tagMode)) == 0
    
    def qtToPublic(self,epc):
        '''转到公有模式'''
        tagMode = TagMode()
        tagMode.dataProfile = 1
        tagMode.persistence = 1
        self.__setAntennaAndTagId(tagMode, epc)
        return self.rid_dll.Impinj_SetMode(self.c_fd,byref(tagMode)) == 0
    
    