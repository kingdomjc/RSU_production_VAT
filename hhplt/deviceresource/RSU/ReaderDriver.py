#encoding:utf-8
'''
Created on 2015-3-16
透传驱动
针对DLL的Python封装
跟随DLL的.h文件同步演进
但出入参都是hex符号的字符串，以简化上层的拼装工作
出参中的数字，都转换成标准int/long类型
针对Python语言的编码风格，所有出参指针均不包含在参数中，而是以函数返回值的方式返回

@author: user
'''

####################内部工具############################
def transToHexFromBytearray(dataarray):
    '''从bytearray转换成HEX'''
    return "".join(["%.2X"%ord(c) for c in dataarray])

    
def transToBytearrayFromHex(hexStr,length=None):
    '''从HEX字符串转换成bytearray'''
    if len(hexStr)%2 != 0:
        hexStr = '0'+hexStr
    if length is None:
        length = len(hexStr)
    elif len(hexStr)>length*2:
        hexStr = hexStr[:length*2]
    g = []
    for i in range(0,len(hexStr),2):
        g.append(int(hexStr[i]+hexStr[i+1],16))
    for i in range(len(hexStr),length,2): #超过的长度用0补齐
        g.append(0)
    return str(bytearray(g))
###################################################################

from ctypes import *
import os
dllPath = "\\".join(os.path.realpath(__file__).split("\\")[:-1])
dll = cdll.LoadLibrary(dllPath+"\\libEtcRsuDll.dll")
# dll =  windll.LoadLibrary(dllPath+"\\libEtcRsuDll.dll")

def RSU_Open(mode, dev, port):
    #入参：同国标；返回值：返回码
    return dll.RSU_Open(mode,dev,port)

def RSU_Close(fd):
    #入参：设备句柄；返回值：返回码
    return dll.RSU_Close(fd)

def RSU_INIT_rq(fd, Time, BSTInterval, RetryInterval,TxPower, PLLChannelID, TimeOut):
    #入参：同国标接口；返回值：返回码
    Time = c_char_p(transToBytearrayFromHex(Time,4))
    return dll.RSU_INIT_rq(fd, Time, BSTInterval, RetryInterval,TxPower, PLLChannelID, TimeOut)


def RSU_INIT_rs(fd,TimeOut):
    #入参：超时时间；返回值：返回码,RSUStatus,rLen,RSUinfo
    RSUStatus =  c_int(0)
    rlen =  c_int(0)
    RSUinfo = create_string_buffer(128)
    ret = dll.RSU_INIT_rs(fd, byref(RSUStatus), byref(rlen), byref(RSUinfo),TimeOut)
    return ret,RSUStatus.value,rlen.value,transToHexFromBytearray(RSUinfo.raw[:rlen.value])

def PSAM_Reset_rq(fd, PSAMSlot, baud, TimeOut):
    #入参：同国标；返回值：返回码
    return dll.PSAM_Reset_rq(fd, PSAMSlot, baud, TimeOut)

def PSAM_Reset_rs(fd, PSAMSlot, TimeOut):
    #入参：设备句柄、卡槽号、超时时间；返回值：返回码，rlen,Data
    rlen =  c_int(0)    
    Data = create_string_buffer(128)
    ret = dll.PSAM_Reset_rs(fd, PSAMSlot, byref(rlen), byref(Data), TimeOut)
    return ret,rlen.value,transToHexFromBytearray(Data.raw[:rlen.value])

def PSAM_CHANNEL_rq(fd, PSAMSlot, APDUList, APDU,TimeOut):
    #入参：同国标接口；返回值：返回码
    APDU = transToBytearrayFromHex(APDU)
    return dll.PSAM_CHANNEL_rq(fd, PSAMSlot, APDUList, APDU,TimeOut)

def PSAM_CHANNEL_rs(fd, PSAMSlot, TimeOut):
    #入参：设备句柄、卡槽号、超时时间；返回值：返回码、APDUList、Data
    APDUList =  c_int(0)    
    Data = create_string_buffer(128)
    ret = dll.PSAM_CHANNEL_rs(fd, PSAMSlot, byref(APDUList), byref(Data),TimeOut)
    return ret,APDUList.value,transToHexFromBytearray(Data.raw)

def RSU_Info_rq(fd, TimeOut):
    #暂时未实现
    pass

def RSU_Info_rs(fd, rlen, RSUinfo, TimeOut):
    #暂时未实现
    pass 

def RSUDoLog(IsWriteLog):
    dll.RSUDoLog(IsWriteLog)


def INITIALISATION_rq(fd, BeaconID, Time, Profile,
        MandApplicationlist, MandApplication, Profilelist,
        TimeOut):
    #入参：同国标；返回值：返回码
    BeaconID = transToBytearrayFromHex(BeaconID,4)
    Time = transToBytearrayFromHex(Time,4)
    MandApplication = transToBytearrayFromHex(MandApplication)
    return dll.INITIALISATION_rq(fd, BeaconID, Time, Profile,
        MandApplicationlist, MandApplication, Profilelist,
        TimeOut)

def INITIALISATION_rs(fd,TimeOut):
    #入参：设备句柄、超时时间；出参：返回码，ReturnStatus, Profile, Applicationlist, Application, ObuConfiguration
    ReturnStatus = c_int(0)    
    Profile = c_int(0)    
    Applicationlist =  c_int(0)    
    Application = create_string_buffer(128)
    ObuConfiguration = create_string_buffer(128)
    
    ret = dll.INITIALISATION_rs(fd, byref(ReturnStatus), byref(Profile),
        byref(Applicationlist), byref(Application), byref(ObuConfiguration), TimeOut)
    return ret,ReturnStatus.value, Profile.value, Applicationlist.value, transToHexFromBytearray(Application.raw), transToHexFromBytearray(ObuConfiguration.raw)

def GetSecure_rq(fd, accessCredentialsOp, mode, DID,
        AccessCredentials, keyIdForEncryptOp, FID, offset,
        length, RandRSU, KeyIdForAuthen, KeyIdForEncrypt,
        TimeOut):
    #入参：同国标；返回值：返回码
    AccessCredentials = transToBytearrayFromHex(AccessCredentials)
    RandRSU = transToBytearrayFromHex(RandRSU)
    return dll.GetSecure_rq(fd, accessCredentialsOp, mode, DID,
        AccessCredentials, keyIdForEncryptOp, FID, offset,
        length, RandRSU, KeyIdForAuthen, KeyIdForEncrypt,TimeOut)

def GetSecure_rs(fd,TimeOut):
    #入参：设备句柄，超时时间；返回值：返回码、DID, FID, length, File,authenticator, ReturnStatus
    DID = c_int(0)
    FID = c_int(0) 
    length = c_int(0) 
    File = create_string_buffer(128)
    authenticator = create_string_buffer(128)
    ReturnStatus = c_int(0)
    
    ret = dll.GetSecure_rs(fd, byref(DID), byref(FID), byref(length), byref(File),
        byref(authenticator), byref(ReturnStatus), TimeOut)
    return ret,DID.value, FID.value, length.value, transToHexFromBytearray(File.raw[:length.value]),transToHexFromBytearray(authenticator.raw[:8]), ReturnStatus.value

def TransferChannel_rq(fd, mode, DID, ChannelID, APDULIST,APDU, TimeOut):
    #入参：同国标；返回值：返回码
    APDU = transToBytearrayFromHex(APDU)
    return dll.TransferChannel_rq(fd, mode, DID, ChannelID, APDULIST,APDU, TimeOut)

def TransferChannel_rs(fd, TimeOut):
    #入参：设备句柄，超时时间；返回值：返回码,DID,ChannelID,APDULIST,Data,ReturnStatus
    DID = c_int(0)
    ChannelID = c_int(0)
    APDULIST = c_int(0)
    Data = create_string_buffer(256)
    ReturnStatus = c_int(0)
    ret = dll.TransferChannel_rs(fd, byref(DID), byref(ChannelID), byref(APDULIST), byref(Data), byref(ReturnStatus), TimeOut)
    return ret,DID.value,ChannelID.value,APDULIST.value,transToHexFromBytearray(Data.raw),ReturnStatus.value

def SetMMI_rq(fd, mode, DID, SetMMIPara, TimeOut):
    #入参：同国标；返回值：返回码
    return dll.SetMMI_rq(fd, mode, DID, SetMMIPara, TimeOut)

def SetMMI_rs(fd, TimeOut):
    #入参：设备句柄，超时时间，返回值：返回码，DID, ReturnStatus
    DID = c_int(0)
    ReturnStatus = c_int(0)

    ret = dll.SetMMI_rs(fd, byref(DID), byref(ReturnStatus), TimeOut)
    return ret,DID.value,ReturnStatus.value

def EVENT_REPORT_rq(fd, mode, DID, EventType, TimeOut):
    #入参：同国标；出参：返回码
    return dll.EVENT_REPORT_rq(fd, mode, DID, EventType, TimeOut)

def Prog_Comm_Send (fd, CMDType , Command,  slen, TimeOut):
    #暂未实现
    pass

def Prog_Comm_Rev (fd, DataType , Data,  rlen, TimeOut):
    #暂未实现
    pass




