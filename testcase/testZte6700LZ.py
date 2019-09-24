#encoding:utf-8
'''
Created on 2014-12-11
ZTE 6700 RID40 调试用例
@author: user
'''
from hhplt.deviceresource import TestResource
from ctypes import *
import time
from hhplt.deviceresource.Zxris6700Rid30 import *

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


c_fd = c_int(0) #设备句柄
allAntenna = Antenna()  #天线参数
allAntenna.antenna[0] = c_ubyte(1)
allAntenna.antenna[1] = c_ubyte(1)
allAntenna.antenna[2] = c_ubyte(0)
allAntenna.antenna[3] = c_ubyte(0)    #全天线检查，目前只启用1/2天线

result = InventoryResult()  #清点结果容器
readResult = ReadResult()   #读结果容器

def inventory():
    #清点
    global result
    res = dll.Impinj_Invent(c_fd,byref(allAntenna),byref(result))
    print 'inv res=',res,'num=',result.num,'idLen = ',result.tagInfo[0].tagIDLen,'data=',toHexStr(result.tagInfo[0].tagID)

def isQtStatePublic():
    #获得当前的公私有状态，如果是公有模式，返回true，私有模式返回false
    qtState = c_int(0)
    tagModeQuery = TagModeQuery()
    tagModeQuery.antennaID = 1
    for i in range(4):
        tagModeQuery.accessPassword[i] = 0
    tagModeQuery.tagID.tagDataLen = 12
    for i in range(12):
        tagModeQuery.tagID.aucTagData[i] = result.tagInfo[0].tagID[i]
    res = dll.Impinj_GetMode(c_fd,byref(tagModeQuery),byref(qtState))
    print 'getQtState res = ',res,"state = ",qtState
    return qtState.value == 1
    

def changeToPrivate():
    #转换成私有模式
    if isQtStatePublic():
        tagMode = TagMode()
        tagMode.antennaID = 1
        tagMode.dataProfile = 0
        tagMode.persistence = 1
        for i in range(4):
            tagMode.accessPassword[i] = 0
        tagMode.tagID.tagDataLen = 12
        for i in range(12):
            tagMode.tagID.aucTagData[i] = result.tagInfo[0].tagID[i]
        
        res = dll.Impinj_SetMode(c_fd,byref(tagMode))
        print 'setmode to private res = ',res
    else:
        print 'already private'

def changeToPublic():
    #转成共公有模式
    if not isQtStatePublic():
        tagMode = TagMode()
        tagMode.antennaID = 1
        tagMode.dataProfile = 1
        tagMode.persistence = 1
        for i in range(4):
            tagMode.accessPassword[i] = 0
        tagMode.tagID.tagDataLen = 12
        for i in range(12):
            tagMode.tagID.aucTagData[i] = result.tagInfo[0].tagID[i]
        res = dll.Impinj_SetMode(c_fd,byref(tagMode))
        print 'setmode to public res = ',res
    else:
        print "already public"
        

def readUser():
    #读USER区
    readPara = ISO_6C_TagRead()
    readPara.antennaID = 1
    readPara.memBank = 3
    readPara.offset = 0
    readPara.length = 64
    for i in range(4):
        readPara.accessPassword[i] = 0
    readPara.tagID.tagDataLen = 12
    for i in range(12):
        readPara.tagID.aucTagData[i] = result.tagInfo[0].tagID[i]
    res = dll.Impinj_Read(c_fd,byref(readPara),byref(readResult))
    print 'read whole user res = ',res,'readlen=',readResult.dataLen,'data=',toHexStr(readResult.readData)
    
def readTid():
    #读TID区
    readPara = ISO_6C_TagRead()
    readPara.antennaID = 1
    readPara.memBank = 2
    readPara.offset = 0
    readPara.length = 12
    for i in range(4):
        readPara.accessPassword[i] = 0
    readPara.tagID.tagDataLen = 12
    for i in range(12):
        readPara.tagID.aucTagData[i] = result.tagInfo[0].tagID[i]
    res = dll.Impinj_Read(c_fd,byref(readPara),byref(readResult))
    print 'read tid res = ',res,'readlen=',readResult.dataLen,'data=',toHexStr(readResult.readData)
        
        
def readKillPassword():
    readPara = ISO_6C_TagRead()
    readPara.antennaID = 1
    readPara.memBank = 0
    readPara.offset = 0
    readPara.length = 4
    for i in range(4):
        readPara.accessPassword[i] = 0
    readPara.tagID.tagDataLen = 12
    for i in range(12):
        readPara.tagID.aucTagData[i] = result.tagInfo[0].tagID[i]
    res = dll.Impinj_Read(c_fd,byref(readPara),byref(readResult))
    print 'read kill password res = ',res,'readlen=',readResult.dataLen,'data=',toHexStr(readResult.readData)

def writeUser():
    #写USER区
    writePara = ISO_6C_TagWrite()
    writePara.antennaID = 1
    writePara.memBank = 3
    writePara.offset = 0
    writePara.length = 64
    for i in range(4):
        writePara.accessPassword[i] = 0
    for i in range(64):
        writePara.data[i] = i%128
    
    writePara.tagID.tagDataLen = 12
    for i in range(12):
        writePara.tagID.aucTagData[i] = result.tagInfo[0].tagID[i]
    res = dll.Impinj_Write(c_fd,byref(writePara)) 
    print 'write user res = ',res

def writeEpc():
    #写EPC
    writePara = ISO_6C_TagWrite()
    writePara.antennaID = 1
    writePara.memBank = 1
    writePara.offset = 4
    writePara.length = 12
    for i in range(4):
        writePara.accessPassword[i] = 0
    for i in range(12):
        writePara.data[i] = (i+8)%128
    
    writePara.tagID.tagDataLen = 12
    for i in range(12):
        writePara.tagID.aucTagData[i] = result.tagInfo[0].tagID[i]
    res = dll.Impinj_Write(c_fd,byref(writePara))
    print 'write epc res = ',res


def clearReserved():
    #清空Reserved区
    writePara = ISO_6C_TagWrite()
    writePara.antennaID = 1
    writePara.memBank = 0
    writePara.offset = 0
    writePara.length = 8
    for i in range(4):
        writePara.accessPassword[i] = 0
    for i in range(8):
        writePara.data[i] = 0
    
    writePara.tagID.tagDataLen = 12
    for i in range(12):
        writePara.tagID.aucTagData[i] = result.tagInfo[0].tagID[i]
    res = dll.Impinj_Write(c_fd,byref(writePara))
    print 'write reserved res = ',res
    
    
    
def lockKillPwd():
    #锁KILL PASSWORD区
    lockPara = ISO_6C_TagLock()
    lockPara.antennaID = 1
    lockPara.killBankOp = 2
    lockPara.accessBankOp = 0
    lockPara.epcBankOp = 0
    lockPara.tidBankOp = 0
    lockPara.userBankOp = 0
    
    for i in range(4):
        lockPara.accessPassword[i] = 0
    lockPara.tagID.tagDataLen = 12
    for i in range(12):
        lockPara.tagID.aucTagData[i] = result.tagInfo[0].tagID[i]
    res = dll.Impinj_Lock(c_fd,byref(lockPara))
    print 'lock killpsd res = ',res
    
def tryToWriteKillPsd():
    '''尝试些kill password，用于检查是否被锁'''
    writePara = ISO_6C_TagWrite()
    writePara.antennaID = 1
    writePara.memBank = 0
    writePara.offset = 0
    writePara.length = 4
    for i in range(4):
        writePara.accessPassword[i] = 0
    for i in range(8):
        writePara.data[i] = 0
    
    writePara.tagID.tagDataLen = 12
    for i in range(12):
        writePara.tagID.aucTagData[i] = result.tagInfo[0].tagID[i]
    res = dll.Impinj_Write(c_fd,byref(writePara))
    print 'write reserved res = ',res
dll = windll.LoadLibrary("6700RID40.dll")
res = dll.Connect(("%s:%d"%("10.86.20.50",5084)).encode(),byref(c_fd))
print 'res=',res,'fd:',c_fd

inventory()
readKillPassword()
#changeToPrivate()
#inventory()
#writeEpc()
#inventory()
#changeToPublic()
#inventory()
#writeEpc()
#inventory()
#readTid()
#writeUser()
#readUser()
#inventory()
#clearReserved()
#lockKillPwd()
#tryToWriteKillPsd()
dll.Disconnect(c_fd)





