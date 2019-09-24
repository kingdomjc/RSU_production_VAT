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
#from trade.container import GLOBAL

GLOBAL = {}

from ctypes import *
import os
dllPath = "\\".join(os.path.realpath(__file__).split("\\")[:-1])

#发卡器 dll使用
#dll = cdll.LoadLibrary(dllPath+"\\libEtcRsuDll-f.dll")
#stdcall 接口 RSU dll使用
#dll = windll.LoadLibrary(dllPath+"\\libEtcRsuDll-r.dll")

def OpenDllHandel(mode):
    if 1 == mode:
        GLOBAL["dllhandel"] = windll.LoadLibrary(dllPath+"\\libEtcRsuDll-r.dll")
    else:
        GLOBAL["dllhandel"] = cdll.LoadLibrary(dllPath+"\\libEtcRsuDll-f.dll")

def RSU_Open(mode, dev, port):
    #入参：同国标；返回值：返回码
    return GLOBAL["dllhandel"].RSU_Open(mode,dev,port)

def RSU_Close(fd):
    #入参：设备句柄；返回值：返回码
    return GLOBAL["dllhandel"].RSU_Close(fd)

def RSU_INIT_rq(fd, Time, BSTInterval, RetryInterval,TxPower, PLLChannelID, TimeOut):
    #入参：同国标接口；返回值：返回码
    #Time = c_char_p(transToBytearrayFromHex(Time,4))
    Time = transToBytearrayFromHex(Time,4)
    return GLOBAL["dllhandel"].RSU_INIT_rq(fd, Time, BSTInterval, RetryInterval, TxPower, PLLChannelID, TimeOut)


def RSU_INIT_rs(fd,TimeOut):
    #入参：超时时间；返回值：返回码,RSUStatus,rLen,RSUinfo
    RSUStatus =  c_int(0)
    rlen =  c_int(0)
    RSUinfo = create_string_buffer(128)
    ret = GLOBAL["dllhandel"].RSU_INIT_rs(fd, byref(RSUStatus), byref(rlen), byref(RSUinfo),TimeOut)
    return ret,RSUStatus.value,rlen.value,transToHexFromBytearray(RSUinfo.raw[:rlen.value])

def PSAM_Reset_rq(fd, PSAMSlot, baud, TimeOut):
    #入参：同国标；返回值：返回码
    return GLOBAL["dllhandel"].PSAM_Reset_rq(fd, PSAMSlot, baud, TimeOut)

def PSAM_Reset_rs(fd, PSAMSlot, TimeOut):
    #入参：设备句柄、卡槽号、超时时间；返回值：返回码，rlen,Data
    rlen =  c_int(0)    
    Data = create_string_buffer(128)
    ret = GLOBAL["dllhandel"].PSAM_Reset_rs(fd, PSAMSlot, byref(rlen), byref(Data), TimeOut)
    return ret,rlen.value,transToHexFromBytearray(Data.raw[:rlen.value])

def PSAM_CHANNEL_rq(fd, PSAMSlot, APDUList, APDU,TimeOut):
    #入参：同国标接口；返回值：返回码
    APDU = transToBytearrayFromHex(APDU)
    return GLOBAL["dllhandel"].PSAM_CHANNEL_rq(fd, PSAMSlot, APDUList, APDU,TimeOut)

def PSAM_CHANNEL_rs(fd, PSAMSlot, TimeOut):
    #入参：设备句柄、卡槽号、超时时间；返回值：返回码、APDUList、Data
    APDUList =  c_int(0)    
    Data = create_string_buffer(128)
    ret = GLOBAL["dllhandel"].PSAM_CHANNEL_rs(fd, PSAMSlot, byref(APDUList), byref(Data),TimeOut)
    return ret,APDUList.value,transToHexFromBytearray(Data.raw)

def RSU_Info_rq(fd, TimeOut):
    #暂时未实现
    pass

def RSU_Info_rs(fd, rlen, RSUinfo, TimeOut):
    #暂时未实现
    pass 

def RSUDoLog(IsWriteLog):
    GLOBAL["dllhandel"].RSUDoLog(IsWriteLog)


def INITIALISATION_rq(fd, BeaconID, Time, Profile,
        MandApplicationlist, MandApplication, Profilelist,
        TimeOut):
    #入参：同国标；返回值：返回码
    BeaconID = transToBytearrayFromHex(BeaconID,4)
    Time = transToBytearrayFromHex(Time,4)
    MandApplication = transToBytearrayFromHex(MandApplication)
    return GLOBAL["dllhandel"].INITIALISATION_rq(fd, BeaconID, Time, Profile,
        MandApplicationlist, MandApplication, Profilelist,
        TimeOut)

def INITIALISATION_rs(fd,TimeOut):
    #入参：设备句柄、超时时间；出参：返回码，ReturnStatus, Profile, Applicationlist, Application, ObuConfiguration
    ReturnStatus = c_int(0)    
    Profile = c_int(0)    
    Applicationlist =  c_int(0)    
    Application = create_string_buffer(128)
    ObuConfiguration = create_string_buffer(128)
    
    ret = GLOBAL["dllhandel"].INITIALISATION_rs(fd, byref(ReturnStatus), byref(Profile),
        byref(Applicationlist), byref(Application), byref(ObuConfiguration), TimeOut)
    return ret,ReturnStatus.value, Profile.value, Applicationlist.value, transToHexFromBytearray(Application.raw), transToHexFromBytearray(ObuConfiguration.raw)

def GetSecure_rq(fd, accessCredentialsOp, mode, DID,
        AccessCredentials, keyIdForEncryptOp, FID, offset,
        length, RandRSU, KeyIdForAuthen, KeyIdForEncrypt,
        TimeOut):
    #入参：同国标；返回值：返回码
    AccessCredentials = transToBytearrayFromHex(AccessCredentials)
    RandRSU = transToBytearrayFromHex(RandRSU)
    return GLOBAL["dllhandel"].GetSecure_rq(fd, accessCredentialsOp, mode, DID,
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
    
    ret = GLOBAL["dllhandel"].GetSecure_rs(fd, byref(DID), byref(FID), byref(length), byref(File),
        byref(authenticator), byref(ReturnStatus), TimeOut)
    return ret,DID.value, FID.value, length.value, transToHexFromBytearray(File.raw[:length.value]),transToHexFromBytearray(authenticator.raw[:8]), ReturnStatus.value

def TransferChannel_rq(fd, mode, DID, ChannelID, APDULIST,APDU, TimeOut):
    #入参：同国标；返回值：返回码
    APDU = transToBytearrayFromHex(APDU)
    return GLOBAL["dllhandel"].TransferChannel_rq(fd, mode, DID, ChannelID, APDULIST,APDU, TimeOut)

def TransferChannel_rs(fd, TimeOut):
    #入参：设备句柄，超时时间；返回值：返回码,DID,ChannelID,APDULIST,Data,ReturnStatus
    DID = c_int(0)
    ChannelID = c_int(0)
    APDULIST = c_int(0)
    Data = create_string_buffer(256)
    ReturnStatus = c_int(0)
    ret = GLOBAL["dllhandel"].TransferChannel_rs(fd, byref(DID), byref(ChannelID), byref(APDULIST), byref(Data), byref(ReturnStatus), TimeOut)
    return ret,DID.value,ChannelID.value,APDULIST.value,transToHexFromBytearray(Data.raw),ReturnStatus.value

def TransferChannelSetMMI_rq(fd, mode, DID, ChannelID, APDULIST,APDU, s_mode, s_DID, setMMIPar, TimeOut):
    #入参：同国标；返回值：返回码
    APDU = transToBytearrayFromHex(APDU)
    return GLOBAL["dllhandel"].TransferChannelSetMMI_rq(fd, mode, DID, ChannelID, APDULIST,APDU,  s_mode, s_DID, setMMIPar,TimeOut)

def TransferChannelSetMMI_rs(fd, TimeOut):
    #入参：设备句柄，超时时间；返回值：返回码,DID,ChannelID,APDULIST,Data,ReturnStatus
    DID = c_int(0)
    ChannelID = c_int(0)
    APDULIST = c_int(0)
    Data = create_string_buffer(256)
    ReturnStatus = c_int(0)
    s_DID = c_int(0)
    s_ReturnStatus = c_int(0)
    ret = GLOBAL["dllhandel"].TransferChannelSetMMI_rs(fd, byref(DID), byref(ChannelID), byref(APDULIST), byref(Data), byref(ReturnStatus), byref(s_DID), byref(s_ReturnStatus), TimeOut)
    return ret,DID.value,ChannelID.value,APDULIST.value,transToHexFromBytearray(Data.raw),ReturnStatus.value,s_DID.value,s_ReturnStatus.value

def SetMMI_rq(fd, mode, DID, SetMMIPara, TimeOut):
    #入参：同国标；返回值：返回码
    return GLOBAL["dllhandel"].SetMMI_rq(fd, mode, DID, SetMMIPara, TimeOut)

def SetMMI_rs(fd, TimeOut):
    #入参：设备句柄，超时时间，返回值：返回码，DID, ReturnStatus
    DID = c_int(0)
    ReturnStatus = c_int(0)

    ret = GLOBAL["dllhandel"].SetMMI_rs(fd, byref(DID), byref(ReturnStatus), TimeOut)
    return ret,DID.value,ReturnStatus.value

def EVENT_REPORT_rq(fd, mode, DID, EventType, TimeOut):
    #入参：同国标；出参：返回码
    return GLOBAL["dllhandel"].EVENT_REPORT_rq(fd, mode, DID, EventType, TimeOut)

def Prog_Comm_Send (fd, CMDType , Command,  slen, TimeOut):
    #暂未实现
    pass

def Prog_Comm_Rev (fd, DataType , Data,  rlen, TimeOut):
    #暂未实现
    pass

def HF_card_inventory_rq(fd, InenetoryTimeOut, TimeOut):
    #入参：同国标；返回值：返回码
    return GLOBAL["dllhandel"].HF_Card_Inventory_rq(fd, InenetoryTimeOut, TimeOut)

def HF_card_inventory_rs(fd, TimeOut):
    contextLength = c_int(0)
    context = create_string_buffer(256)
    ReturnStatus = c_int(0)
    ret = GLOBAL["dllhandel"].HF_Card_Inventory_rs(fd, byref(context), byref(contextLength), byref(ReturnStatus), TimeOut)
    return ret,contextLength.value,transToHexFromBytearray(context.raw),ReturnStatus.value

def HF_card_channel_rq(fd, APDULIST, APDU, TimeOut):
    #入参：同国标；返回值：返回码
    APDU = transToBytearrayFromHex(APDU)
    return GLOBAL["dllhandel"].HF_CPU_Card_Channel_rq(fd, APDULIST, APDU, TimeOut)

def HF_card_channel_rs(fd, TimeOut):
    APDULIST = c_int(0)
    Data = create_string_buffer(512)
    ReturnStatus = c_int(0)
    ret = GLOBAL["dllhandel"].HF_CPU_Card_Channel_rs(fd, byref(APDULIST), byref(Data), byref(ReturnStatus), TimeOut)
    return ret,APDULIST.value,transToHexFromBytearray(Data.raw),ReturnStatus.value

def RF_Transfer_rq(fd, mode, APDU, TimeOut):
    #入参：同国标；返回值：返回码
    APDU = transToBytearrayFromHex(APDU)
    return GLOBAL["dllhandel"].RfTransferCmd_rq(fd, mode, APDU, TimeOut)

def RF_Transfer_rs(fd, TimeOut):
    #入参：设备句柄，超时时间；返回值：返回码,DID,ChannelID,APDULIST,Data,ReturnStatus
    Data = create_string_buffer(256)
    ret = GLOBAL["dllhandel"].RfTransferCmd_rs(fd, byref(Data), TimeOut)
    return ret,transToHexFromBytearray(Data.raw)

def HF_Close_RF_rq(fd):
    # 关闭高频射频
    return GLOBAL["dllhandel"].HF_Close_RF_rq(fd)

def HF_Close_RF_rs(fd):
    return GLOBAL["dllhandel"].HF_Close_RF_rs(fd)

