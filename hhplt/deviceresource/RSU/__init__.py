#encoding:utf-8
'''
RSU的Python驱动
V0.1.0 Alpha

<编码未完成>

Python封装提供两种方式：
1、使用    RSU.RSU类，已封装为同步方法，成对儿调用rq/rs
2、直接使用Rsu.ReaderDriver里面的透传方法。

入参中的命令串，使用hex符号字符串即可；所有国标出参都以返回值的方式返回。
'''

from ReaderDriver import *

class DeviceException(Exception):
    '''设备异常抛出'''
    def __init__(self,msg):
        self.msg = msg
        
    def __str__(self):
        return self.msg

class RSU:
    def __init__(self):
        self.fd = None;
        self.TimeOut = 1000
    
    def setTimeout(self,timeout):
        self.TimeOut = timeout
        
    def RSU_Open(self,mode,dev,port):
        fd = RSU_Open(mode,dev,port)
        if fd < 0 :
            raise DeviceException(u"设备打开失败")
        self.fd = fd
    
    def RSU_Close(self):
        if self.fd is None:
            raise DeviceException(u"设备未打开")
        RSU_Close(self.fd)
    
    
    def RSU_INIT(self,Time, BSTInterval, RetryInterval,TxPower, PLLChannelID,timeout = None):
        if timeout is None:
            timeout = self.TimeOut
        ret = RSU_INIT_rq(self.fd, Time, BSTInterval, RetryInterval,TxPower, PLLChannelID, timeout)
        if ret != 0:
            raise DeviceException(u"指令发送失败，返回值:%d"%ret)
        return RSU_INIT_rs(self.fd,timeout)
        
    def PSAM_Reset(self,PSAMSlot, baud,timeout = None):
        if timeout is None:
            timeout = self.TimeOut
        ret = PSAM_Reset_rq(self.fd, PSAMSlot, baud, timeout)
        if ret != 0:
            raise DeviceException(u"指令发送失败，返回值:%d"%ret)
        return PSAM_Reset_rs(self.fd,PSAMSlot,timeout)

    def PSAM_CHANNEL(self,PSAMSlot, APDUList, APDU,timeout=None):
        if timeout is None:
            timeout = self.TimeOut
        ret = PSAM_CHANNEL_rq(self.fd, PSAMSlot, APDUList, APDU,timeout)
        if ret != 0:
            raise DeviceException(u"指令发送失败，返回值:%d"%ret)
        return PSAM_CHANNEL_rs(self.fd, PSAMSlot, timeout)
        
    def RSUDoLog(self,IsWriteLog):
        RSUDoLog(IsWriteLog)
        
    def INITIALISATION(self,BeaconID, Time, Profile,MandApplicationlist, MandApplication, Profilelist,timeout=None):
        if timeout is None:
            timeout = self.TimeOut
        ret =INITIALISATION_rq(self.fd, BeaconID, Time, Profile,
            MandApplicationlist, MandApplication, Profilelist,
            timeout)
        if ret != 0:
            raise DeviceException(u"指令发送失败，返回值:%d"%ret)
        return INITIALISATION_rs(self.fd,timeout)

    def GetSecure(self,accessCredentialsOp, mode, DID,
        AccessCredentials, keyIdForEncryptOp, FID, offset,
        length, RandRSU, KeyIdForAuthen, KeyIdForEncrypt,timeout=None):
        if timeout is None:
            timeout = self.TimeOut
        ret = GetSecure_rq(self.fd, accessCredentialsOp, mode, DID,
            AccessCredentials, keyIdForEncryptOp, FID, offset,
            length, RandRSU, KeyIdForAuthen, KeyIdForEncrypt,
            timeout)
        if ret != 0:
            raise DeviceException(u"指令发送失败，返回值:%d"%ret)
        return GetSecure_rs(self.fd,timeout)
        
    def TransferChannel(self,mode, DID, ChannelID, APDULIST,APDU,timeout=None):
        if timeout is None:
            timeout = self.TimeOut
        ret = TransferChannel_rq(self.fd, mode, DID, ChannelID, APDULIST,APDU, timeout)
        if ret != 0:
            raise DeviceException(u"指令发送失败，返回值:%d"%ret)
        return TransferChannel_rs(self.fd, timeout)
    
    def SetMMI(self,mode, DID, SetMMIPara,timeout=None):
        if timeout is None:
            timeout = self.TimeOut
        ret = SetMMI_rq(self.fd, mode, DID, SetMMIPara, timeout)
        if ret != 0:
            raise DeviceException(u"指令发送失败，返回值:%d"%ret)
        return SetMMI_rs(self.fd,timeout)

    def EVENT_REPORT(self,mode, DID, EventType,timeout=None):
        if timeout is None:
            timeout = self.TimeOut
        return EVENT_REPORT_rq(self.fd, mode, DID, EventType, timeout)
        
        