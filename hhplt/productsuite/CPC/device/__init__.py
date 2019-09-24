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
        self.TimeOut = 4000
    
    def setTimeout(self,timeout):
        self.TimeOut = timeout
        
    def RSU_Open(self,mode,dev,port):
        #print "OpenDllHandel"
        OpenDllHandel(mode)
        #print "OpenDllHandel11"
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
            raise DeviceException(u"init_rq 指令发送失败，返回值:%d"%ret)
        return RSU_INIT_rs(self.fd,timeout)
        
    def PSAM_Reset(self,PSAMSlot, baud,timeout = None):
        if timeout is None:
            timeout = self.TimeOut
        ret = PSAM_Reset_rq(self.fd, PSAMSlot, baud, timeout)
        if ret != 0:
            raise DeviceException(u"pasm reset_rq 指令发送失败，返回值:%d"%ret)
        return PSAM_Reset_rs(self.fd,PSAMSlot,timeout)

    def PSAM_CHANNEL(self,PSAMSlot, APDUList, APDU,timeout=None):
        if timeout is None:
            timeout = self.TimeOut
        ret = PSAM_CHANNEL_rq(self.fd, PSAMSlot, APDUList, APDU,timeout)
        if ret != 0:
            raise DeviceException(u"pasm cmd_rq 指令发送失败，返回值:%d"%ret)
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
            raise DeviceException(u"bst_rq 指令发送失败，返回值:%d"%ret)
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
            raise DeviceException(u"getSecure_rq 指令发送失败，返回值:%d"%ret)
        return GetSecure_rs(self.fd,timeout)
        
    def TransferChannel(self,mode, DID, ChannelID, APDULIST,APDU,timeout=None):
        if timeout is None:
            timeout = self.TimeOut
        ret = TransferChannel_rq(self.fd, mode, DID, ChannelID, APDULIST,APDU, timeout)
        if ret != 0:
            raise DeviceException(u"transferChannel_rq 指令发送失败，返回值:%d"%ret)
        return TransferChannel_rs(self.fd, timeout)
    
    def TransferChannelSetMMI(self,mode, DID, ChannelID, APDULIST,APDU,s_mode,s_DID,setMMIPar,timeout=None):
        if timeout is None:
            timeout = self.TimeOut
        ret = TransferChannelSetMMI_rq(self.fd, mode, DID, ChannelID, APDULIST,APDU, s_mode, s_DID, setMMIPar, timeout)
        if ret != 0:
            raise DeviceException(u"transferChannel_rq 指令发送失败，返回值:%d"%ret)
        return TransferChannelSetMMI_rs(self.fd, timeout)


    def SetMMI(self,mode, DID, SetMMIPara,timeout=None):
        if timeout is None:
            timeout = self.TimeOut
        ret = SetMMI_rq(self.fd, mode, DID, SetMMIPara, timeout)
        if ret != 0:
            raise DeviceException(u"setMMI_rq 指令发送失败，返回值:%d"%ret)
        return SetMMI_rs(self.fd,timeout)

    def EVENT_REPORT(self,mode, DID, EventType,timeout=None):
        if timeout is None:
            timeout = self.TimeOut
        return EVENT_REPORT_rq(self.fd, mode, DID, EventType, timeout)

    def HFActive(self,InenetoryTimeOut, timeout=None):
        if timeout is None:
            timeout = self.TimeOut
        ret = HF_card_inventory_rq(self.fd, InenetoryTimeOut, timeout)
        if ret != 0:
            raise DeviceException(u"HF_card_inventory_rq 指令发送失败，返回值:%d"%ret)
        return HF_card_inventory_rs(self.fd,timeout)
        
    def HFCmd(self,APDULIST,APDU, timeout=None):
        if timeout is None:
            timeout = self.TimeOut
        ret = HF_card_channel_rq(self.fd, APDULIST,APDU, timeout)
        if ret != 0:
            raise DeviceException(u"HFCmd_rq 指令发送失败，返回值:%d"%ret)
        return HF_card_channel_rs(self.fd,timeout)

    def RFTransferCmd(self,mode,APDU,timeout=None):
        if timeout is None:
            timeout = self.TimeOut
        ret = RF_Transfer_rq(self.fd,mode,APDU, timeout)
        if ret != 0:
            raise DeviceException(u"RF_Transfer_rq 指令发送失败，返回值:%d"%ret)
        return RF_Transfer_rs(self.fd, timeout)

    def HFCloseRF(self):
        # 关闭射频
        ret = HF_Close_RF_rq(self.fd)
        if ret != 0: raise DeviceException(u"HF_Close_RF_rq指令发送失败，返回值:%d"%ret)
        return HF_Close_RF_rs(self.fd)
