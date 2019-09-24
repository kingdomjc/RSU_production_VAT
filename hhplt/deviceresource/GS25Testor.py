# coding=utf8
'''
GS25测试驱动
侯哥编写，在此基础上有一些改动

'''

from ctypes import *
from os.path import abspath, dirname
import time
import os
import binascii
import random
import struct
from hhplt.deviceresource import TestResource,TestResourceInitException
from hhplt.parameters import PARAM


class GS25Exception(Exception):

    def __init__(self, err_str):
        super(GS25Exception, self).__init__()
        self.err_str = err_str

    def __str__(self):
        return self.err_str


class GS25(TestResource):
    def __init__(self,initParam):
        dll_path = "libEtcRsuDll.dll"
        self.dll = cdll.LoadLibrary(dll_path)
        self.commMode = None    #通信方式：USB/UART

    def initResource(self):
        self.fd = None
        self.buffer = create_string_buffer(2048)
    
    def switchToUsb(self):
        '''切换到USB通信-add by zhangwenshuo'''
        if self.commMode == "USB":
            return
        if self.fd is not None:
            self.close()
        self.open(2,0)
        self.commMode = "USB"
    
    def switchToUart(self):
        '''切换到UART通信-add by zhangwenshuo'''
        if self.commMode == "UART":return
        if self.fd is not None:
            self.close()
        self.open(0,PARAM["gs25SerialPort"].encode("ascii"))
        self.commMode = "UART"
        
    def retrive(self):
        if self.fd is not None:
            self.close()
            self.commMode = None

    def open(self, mode=0, dev=None):
        if dev is None:dev = self.serialPort
        if mode == 2:
            self.fd = self.dll.RSU_Open(2, None, None)
        else:
            self.fd = self.dll.RSU_Open(0, dev, None)
        if self.fd < 0:
            raise GS25Exception("open device return " + str(self.fd))

    def close(self):
        self.dll.RSU_Close(self.fd)
        self.fd = None

    def rsuInfo(self):
        self.dll.RSU_Info_rq(self.fd, 500)
        rLen = c_int(0)
        self.dll.RSU_Info_rs(self.fd, byref(rLen), byref(self.buffer), 500)
        return binascii.hexlify(self.buffer.raw[0:rLen.value])

    def rsuInit(self, time, bstInterval, retryInterval, txPower, channelId, timeout):
        timeHex = binascii.unhexlify(time)
        self.dll.RSU_INIT_rq(self.fd, timeHex, bstInterval, retryInterval, txPower, channelId, timeout)
        rsuStatus = c_int(0)
        rLen = c_int(0)
        ret = self.dll.RSU_INIT_rs(self.fd, byref(rsuStatus), byref(rLen), byref(self.buffer), 500)
        if ret != 0:
            raise GS25Exception("RSU_INIT_rs error! " + str(ret)) 
        ret = {}
        ret['status'] = rsuStatus.value
        ret['rsuInfo'] = binascii.hexlify(self.buffer.raw[0:rLen.value])
        return ret

    def beep(self):
        command = c_char('\x05')
        dataType = c_int(0)
        rLen = c_int(0)
        self.dll.Prog_Comm_Send(self.fd, 0xfd, byref(command), 1, 1000)

    def lightGreenLed(self):
        command = c_char('\x02')
        dataType = c_int(0)
        rLen = c_int(0)
        self.dll.Prog_Comm_Send(self.fd, 0xfd, byref(command), 1, 1000)

    def lightRedLed(self):
        command = c_char('\x01')
        dataType = c_int(0)
        rLen = c_int(0)
        self.dll.Prog_Comm_Send(self.fd, 0xfd, byref(command), 1, 1000)

    def resetPsam(self, sockId):
        rLen = c_int(0)
        ret = self.dll.PSAM_Reset_rq(self.fd, sockId, 115200, 1000)
        if ret != 0:
            raise GS25Exception("resetPsam error! " + str(ret))
        ret = self.dll.PSAM_Reset_rs(self.fd, sockId, byref(rLen), byref(self.buffer), 1000)
        if ret != 0:
            raise GS25Exception("resetPsam error! " + str(ret))

    def psamExchangeApdu(self, sockId, apduList, apdu):
        apduHex = binascii.unhexlify(apdu)
        ret = self.dll.PSAM_CHANNEL_rq(self.fd, sockId, apduList, apduHex, 1000)
        apduListRet = c_int(0)
        ret = self.dll.PSAM_CHANNEL_rs(self.fd, sockId, byref(apduListRet), byref(self.buffer), 2000)        
        ret = []
        pos = 0
        for x in range(apduListRet.value):
            apduLen = ord(self.buffer[pos])
            pos += 1
            ret.append(binascii.hexlify(self.buffer[pos:apduLen+pos]))
            pos += apduLen
        return ret


    def inventObu(self):
        beconId = int(random.random()*1000000)
        beconId = 195888
        beconId = struct.pack("I", beconId)
        time = '\x53\xFE\xC5\x9A'
        profile = 0 
        mandApplicationlist = 1 
        mandApplication = '\x41\x83\x29\x20\x20\x00\x2b'
        profilelist = 0
        self.dll.INITIALISATION_rq(self.fd, beconId, time, profile, mandApplicationlist, mandApplication, profilelist, 1000)
        c_status = c_int(0)
        c_profile = c_int(0)
        c_application_list = c_int(0)
        c_application = create_string_buffer(256)
        c_obu_configuration = create_string_buffer(256)        
        ret = self.dll.INITIALISATION_rs(self.fd, byref(c_status), byref(c_profile), \
                                            byref(c_application_list), byref(c_application), byref(c_obu_configuration), 3000)
        if ret != 0:
            raise GS25Exception("Invent Obu Fail! " + str(ret))
        ret = {}
        ret['status'] = c_status.value 
        ret['profile'] = c_profile.value 
        ret['applicationList'] = c_application_list.value 
        ret['application'] = binascii.hexlify(c_application.raw[0:128])
        ret['obuConfiguration'] = binascii.hexlify(c_obu_configuration.raw[0:7])
        return ret


    def getSecure(self):
        accessCredentialsOp = 0 
        mode = 1
        DID = 1
        AccessCredentials = ""
        keyIdForEncryptOp = 1
        FID = 1
        offset = 0
        length = 0x10
        RandRSU = "\xed\x50\x6a\x24\xc9\xad\x1d\x92"
        KeyIdForAuthen = 0
        KeyIdForEncrypt = 0
        timeout = 500        
        ret = self.dll.GetSecure_rq(self.fd, accessCredentialsOp, mode, DID, AccessCredentials, keyIdForEncryptOp,\
            FID, offset, length, RandRSU, KeyIdForAuthen, KeyIdForEncrypt, timeout)
        did = c_int(0)
        fid = c_int(0)
        length = c_int(0)
        pfile = create_string_buffer(128)
        authenticator = create_string_buffer(128)
        status = c_int(0)
        ret = self.dll.GetSecure_rs(self.fd, byref(did), byref(fid), byref(length), byref(pfile),\
                                        byref(authenticator), byref(status), timeout)
        if ret != 0:
            raise GS25Exception("getSecure fail! " + str(ret))
        if status.value != 0:
            raise GS25Exception("getSecure status not 0 " + str(status.value))
        ret = {}
        ret['did'] = did.value
        ret['fid'] = fid.value
        ret['length'] = length.value
        ret['file'] = binascii.hexlify(pfile.raw[0:length.value])
        ret['authenticator'] = binascii.hexlify(authenticator.raw[0:8])
        ret['status'] = status.value
        return ret

    def transferChannel(self, channelId,  apduList, apdu):
        apduHex = binascii.unhexlify(apdu)
        ret = self.dll.TransferChannel_rq(self.fd, 1, 1, channelId,  apduList, apduHex, 500)
        if ret != 0:
             raise GS25Exception("send transfer_channel fail %d " % ret)
        did = c_int(0)
        c_channelId = c_int(0)
        c_apduSize = c_int(0)
        c_status = c_int(0)
        ret = self.dll.TransferChannel_rs(self.fd, byref(did), byref(c_channelId), byref(c_apduSize),
                       byref(self.buffer), byref(c_status), 1000)
        if(ret != 0):
            raise GS25Exception("receive transfer_channel response fail %d " % ret)
        if(c_status.value != 0):
            raise GS25Exception("receive transfer_channel status error %d " % c_status.value)

        ret = []
        pos = 0
        for x in range(c_apduSize.value):
            apduLen = ord(self.buffer[pos])
            pos += 1
            ret.append(binascii.hexlify(self.buffer[pos:apduLen+pos]))
            pos += apduLen
        return ret


    def transferChannelEsam(self, apduList, apdu):
        return self.transferChannel(2, apduList, apdu)


    def transferChannelIcc(self, apduList, apdu):
        return self.transferChannel(1, apduList, apdu)

    def setMMI(self):
        ret = self.dll.SetMMI_rq(self.fd, 1, 1, 0, 500)
        if ret != 0:
             raise GS25Exception("send setmmi fail %d " % ret)
        did = c_int(0)
        status = c_int(0)
        ret = self.dll.SetMMI_rs(self.fd, byref(did), byref(status), 500)
        if(ret != 0):
            raise GS25Exception("receive setmmi fail %d " % ret)
        if(status.value != 0):
            raise GS25Exception("receive setmmi status error %d " % status.value)

    def eventReport(self):
        ret = self.dll.EVENT_REPORT_rq(self.fd, 0, 0, 0, 500)
        if(ret != 0):
            raise GS25Exception("send eventReport fail %d " % ret)

    def hfInvent(self):
        self.dll.HF_Card_Inventory_rq(self.fd, 500, 500)
        contextLen = c_int(0)
        status = c_int(0)
        ret = self.dll.HF_Card_Inventory_rs(self.fd, self.buffer, byref(contextLen), byref(status), 1000)
        if(ret != 0):
            raise GS25Exception("recv hf card inventory response " + str(ret))
        if status.value != 0:
            raise GS25Exception("recv hf card inventory response status not zero " + str(status.value))
        return binascii.hexlify(self.buffer.raw[0:contextLen.value])

    def closeHf(self):
        self.dll.HF_Close_RF_rq(self.fd)
        ret = self.dll.HF_Close_RF_rs(self.fd)
        if(ret != 0):
            raise GS25Exception("cloase hf fail " + str(ret))

    def hfExchangeApdu(self, apduList, apdu):
        apduHex = binascii.unhexlify(apdu)
        self.dll.HF_CPU_Card_Channel_rq(self.fd, apduList, apduHex, 500)
        c_apduList = c_int(0)
        c_status = c_int(0)
        ret = self.dll.HF_CPU_Card_Channel_rs(self.fd, byref(c_apduList), byref(self.buffer), byref(c_status), 500)
        if(ret != 0):
            raise GS25Exception("recv cpu card  response " + str(ret))

        ret = []
        pos = 0
        for x in range(c_apduList.value):
            apduLen = ord(self.buffer[pos])
            pos += 1
            ret.append(binascii.hexlify(self.buffer[pos:apduLen+pos]))
            pos += apduLen
        return ret 

    def M1CardAuth(self, mode, addr, key):
        keyHex = binascii.unhexlify(key)
        ret = self.dll.M1_Card_Auth_rq(self.fd, mode, addr, keyHex, 500)
        if ret != 0:
            raise GS25Exception("M1 Card send Auth fail " + str(ret))
        ret = self.dll.M1_Card_Auth_rs(self.fd, 500)
        if ret != 0:
            raise GS25Exception("M1 Card rcv Auth fail " + str(ret))

    def M1CardRead(self, addr):
        self.dll.M1_Card_Read_rq(self.fd, addr, 500)
        ret = self.dll.M1_Card_Read_rs(self.fd, self.buffer, 500)
        if ret != 0:
            raise GS25Exception("M1 Card read fail " + str(ret))
        return binascii.hexlify(self.buffer.raw[0:16])


    def M1CardWrite(self, addr, data):
        dataHex = binascii.unhexlify(data)
        self.dll.M1_Card_Write_rq(self.fd, addr, dataHex, 500)
        ret = self.dll.M1_Card_Write_rs(self.fd, 500)
        if ret != 0:
            raise GS25Exception("M1 Card write fail " + str(ret))

    def M1CardInc(self, addr, count):
        self.dll.M1_Card_Inc_rq(self.fd, addr, count, 500)
        ret = self.dll.M1_Card_Inc_rs(self.fd, 500)
        if ret != 0:
            raise GS25Exception("M1 Card inc fail " + str(ret))

    def M1CardDec(self, addr, count):
        self.dll.M1_Card_Dec_rq(self.fd, addr, count, 500)
        ret = self.dll.M1_Card_Dec_rs(self.fd, 500)
        if ret != 0:
            raise GS25Exception("M1 Card dec fail " + str(ret))

    def MIreadCardId(self):
        self.dll.MI_Read_CardId_rq(self.fd, 1000)
        ret = self.dll.MI_Read_CardId_rs(self.fd, byref(self.buffer), 1000)
        if ret != 0:
            raise GS25Exception("MI read CardId fail" + str(ret))
        return binascii.hexlify(self.buffer.raw[0:4])

    def writeDeviceSn(self, sn, crid):
        ''' first para is sn, second is crid'''
        snHex = binascii.unhexlify(sn)
        cridHex = binascii.unhexlify(crid)
        ret = self.dll.Write_Device_SN_rq(self.fd, snHex, cridHex, 500)
        ret = self.dll.Write_Device_SN_rs(self.fd, 500)
        if ret != 0:
            raise GS25Exception("write device sn fail " + str(ret))


    def readDeviceSn(self):
        ret = self.dll.Read_Device_SN_rq(self.fd, 500)
        cridBuffer = create_string_buffer(10)
        ret = self.dll.Read_Device_SN_rs(self.fd, byref(self.buffer), byref(cridBuffer), 500)
        if ret != 0:
            raise GS25Exception("read device sn fail " + str(ret))
        ret = []
        ret.append(binascii.hexlify(self.buffer.raw[0:5]))
        ret.append(binascii.hexlify(cridBuffer.raw[0:2]))
        return ret

