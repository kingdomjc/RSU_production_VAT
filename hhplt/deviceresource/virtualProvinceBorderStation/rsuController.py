#encoding:utf-8
from ctypes import CDLL,c_int,create_string_buffer,byref
from dataTypes import PsamChannelResponse,InitializationResponse,GetSecureResponse,TransferChannelResponse
from hhplt.deviceresource import TestResource
from hhplt.testengine.testcase import uiLog
from utils import DataParser
from dataTypes import DeviceError,CommunicationError
import time
from os.path import abspath, dirname
import os
from ctypes import *

class RsuController(TestResource):
    def __init__(self, param=None):
        dll_path = abspath(dirname(__file__)) + os.sep + "libEtcRsuDll.dll"
        #self.dll = CDLL("libEtcRsuDll.dll")
        self.dll = cdll.LoadLibrary(dll_path)
        self.ip = param["ipaddr"].encode("utf8")
        self.port = param["post"]
    def checkReturn(self, ret, methodName):
        if(ret != 0):
            raise CommunicationError, methodName+"error"
    def open(self):
        self.fd = self.dll.RSU_Open(1, self.ip, self.port)
        if(self.fd > 0):
            uiLog(u"open rsu success")
        else:
            raise DeviceError,"open rsu error"
    def close(self):
        ret = self.dll.RSU_Close(self.fd)
        self.__printReturn(ret, "close rsu")
        if(ret != 0):
            raise DeviceError,"close rsu error"
    def psamReset(self, slot, timeout=2000):
        ret = self.dll.PSAM_Reset_rq(self.fd, slot, 0, timeout)
        self.__printReturn(ret, "reset psam request")
        self.checkReturn(ret, "psamReset")
        rlen = c_int(-1)
        data = create_string_buffer(256)
        ret = self.dll.PSAM_Reset_rs(self.fd, slot, byref(rlen), byref(data), timeout)
        self.__printReturn(ret, "reset psam response")
        self.checkReturn(ret, "psamReset")
        return ret, rlen.value, data.raw.encode("hex")
    def psamChannel(self, slot, apduList, apdu, timeout=2000):
        res = PsamChannelResponse()
        ret = self.dll.PSAM_CHANNEL_rq(self.fd, slot, apduList, apdu.decode("hex"), timeout)
        self.__printReturn(ret, "psam channel request")
        self.checkReturn(ret, "psamChannel")
        apduNum = c_int(-1)
        data = create_string_buffer(256)
        ret = self.dll.PSAM_CHANNEL_rs(self.fd, slot, byref(apduNum), byref(data), timeout)
        self.__printReturn(ret, "psam channel response")
        self.checkReturn(ret, "psamChannel")
        res.ret = ret
        res.apduList = apduNum.value
        res.data = data.raw.encode("hex")
        DataParser.checkChannelResponse(res)
        return res
    def initialization(self, beaconId, time, profile, mandApplicationList, mandApplication, profileList, timeout=2000):
        ret = self.dll.INITIALISATION_rq(self.fd, beaconId, time, profile, mandApplicationList, mandApplication.decode("hex"), profileList, timeout)
        self.__printReturn(ret, "bst request")
        self.checkReturn(ret, "initialization")
        status = c_int(-1)
        channelProfile = c_int(-1)
        appList = c_int(-1)
        application = create_string_buffer(128)
        obuConfiguration = create_string_buffer(16)
        ret = self.dll.INITIALISATION_rs(self.fd, byref(status), byref(channelProfile), byref(appList), byref(application), byref(obuConfiguration), timeout)
        self.__printReturn(ret, "bst response")
        self.checkReturn(ret, "initialization")
        return InitializationResponse(ret, status.value, channelProfile.value, appList.value, application.raw.encode("hex"), obuConfiguration.raw.encode("hex")[0:6])
    def getSecure(self, accessCredentialsOp, mode, did, accessCredentials, keyIdForEncryptOp, fid, offset, length, randRsu, keyIdForAuthen, keyIdForEncrypt, timeout=2000):
        ret = self.dll.GetSecure_rq(self.fd, accessCredentialsOp, mode, did, accessCredentials.decode("hex"), keyIdForEncryptOp, fid, offset, length, randRsu.decode("hex"), keyIdForAuthen, keyIdForEncrypt, timeout)
        self.__printReturn(ret, "get secure request")
        self.checkReturn(ret, "getSecure")
        FID = c_int(-1)
        DID = c_int(-1)
        _length = c_int(-1)
        File = create_string_buffer(128)
        authenticator = create_string_buffer(128)
        ReturnStatus = c_int(-1)
        ret = self.dll.GetSecure_rs(self.fd, byref(DID), byref(FID), byref(_length), byref(File), byref(authenticator), byref(ReturnStatus), timeout)
        self.__printReturn(ret, "get secure response")
        self.checkReturn(ret, "getSecure")
        return GetSecureResponse(ret, FID.value, DID.value, _length.value, File.raw.encode("hex"), authenticator.raw.encode("hex"), ReturnStatus.value)
    def transferChannel(self, mode, did, channelId, apduList, apdu, timeout=2000):
        response = TransferChannelResponse()
        ret = self.dll.TransferChannel_rq(self.fd, mode, did, channelId, apduList, apdu.decode("hex"), timeout)
        self.__printReturn(ret, "transer channel request")
        self.checkReturn(ret, "transferChannel")
        DID = c_int(-1)
        c_channel_id = c_int(-1)
        APDUList = c_int(-1)
        Data = create_string_buffer(128)
        ReturnStatus = c_int(-1)
        ret = self.dll.TransferChannel_rs(self.fd, byref(DID), byref(c_channel_id), byref(APDUList), byref(Data), byref(ReturnStatus), timeout)
        self.__printReturn(ret, "transfer channel response")
        self.checkReturn(ret, "transferChannel")
        response.ret = ret
        response.did = DID.value
        response.channelId = c_channel_id.value
        response.apduList = APDUList.value
        response.data = Data.raw.encode("hex")
        response.returnStatus = ReturnStatus.value
        DataParser.checkChannelResponse(response)
        return response
    def transferChannelRoute1(self, timeout=2000):
        ''' 
        read ef04 first 9 bytes
        read 0008 first 3 bytes
        get 8 bytes random num from user card
        '''
        self.dll.TransferChannel_route_rq1(self.fd)
        data = create_string_buffer(128)
        self.dll.TransferChannel_route_rs1(self.fd, byref(data))
        return data.raw.encode("hex")
    def setMmi(self, mode, did, para, timeout=2000):
        ret = self.dll.SetMMI_rq(self.fd, mode, did, para, timeout)
        self.__printReturn(ret, "set mmi request")
        self.checkReturn(ret, "setMmi")
        rsDid = c_int(-1)
        status = c_int(-1)
        ret = self.dll.SetMMI_rs(self.fd, byref(rsDid), byref(status), timeout)
        self.__printReturn(ret,"set mmi response")
        self.checkReturn(ret, "setMmi")
    def eventReport(self, mode=0, did=0, eventType=0, timeout=2000):
        self.dll.EVENT_REPORT_rq(self.fd, mode, did, eventType, timeout)
    def getCurrentMac(self):
        mac = create_string_buffer(4)
        ret = self.dll.getCurrentMac(self.fd, byref(mac))
        self.__printReturn(ret, "get current mac")
        self.checkReturn(ret,"getCurrentMac")
        return mac.raw.encode("hex")
    def __printReturn(self, ret, message):
        if(ret == 0):
            uiLog(message + u" success")
        else:
            uiLog(message + u" failed")