#encoding:utf-8
import random
from hhplt.deviceresource import TestResource
from hhplt.testengine.testcase import uiLog

class CpcVstInfo(object):
    def __init__(self, indicator=None, mf_ef01=None, df01_ef03=None, df01_ef01=None, \
            df01_ef02=None, random_num=None, equipmentClassAndVersion=None, equipmentStatus=None):
        self.indicator = indicator
        self.mf_ef01 = mf_ef01 
        self.df01_ef03 = df01_ef03
        self.df01_ef01 = df01_ef01
        self.df01_ef02 = df01_ef02
        self.random_num = random_num
        self.equipmentClassAndVersion = equipmentClassAndVersion
        self.equipmentStatus = equipmentStatus
class ObuVstInfo(object):
    def __init__(self, sysInfo=None, file0015=None, file0019=None, equipmentClassAndVersion=None, obuStatus=None):
        self.sysInfo = sysInfo
        self.file0015 = file0015
        self.file0019 = file0019
        self.equipmentClassAndVersion = equipmentClassAndVersion
        self.obuStatus = obuStatus
class TransferChannelResponse(object):
    def __init__(self, ret=None, did=None, channelId=None, apduList=None, data=None, returnStatus=None):
        self.ret = ret
        self.did = did
        self.channelId = channelId
        self.apduList = apduList
        self.data = data
        self.returnStatus = returnStatus
    def getApduBySn(self, sn):
        if(sn<0 or sn>self.apduList):
            raise TransactionError,"sequence number error"
        else:
            startIndex = 0
            for i in range(sn):
                currentLen = int(self.data[startIndex:startIndex+2],16)
                currentData = self.data[startIndex+1*2:startIndex+(1+currentLen-2)*2]
                startIndex = startIndex+(currentLen+1)*2
            return currentData
class PsamChannelResponse(object):
    def __init__(self, ret=None, apduList=None, data=None):
        self.ret = ret
        self.apduList = apduList
        self.data = data
class InitializationResponse(object):
    def __init__(self, ret=None, status=None, channelProfile=None, appList=None, application=None, obuConfiguration=None):
        self.ret = ret 
        self.status = status 
        self.channelProfile = channelProfile
        self.appList = appList
        self.application = application
        self.obuConfiguration = obuConfiguration 
class GetSecureResponse(object):
    def __init__(self, ret=None, fid=None, did=None, length=None, fileData=None, authenticator=None, returnStatus=None):
        self.ret = ret
        self.fid = fid
        self.did = did
        self.length = length
        self.fileData = fileData
        self.authenticator = authenticator
        self.returnStatus = returnStatus
class PreReadInfoForWriteRoute(object):
    def __init__(self, ret=None, ef04First9Bytes=None, file0008First3Bytes=None, randomNum=None):
        self.ret = ret
        self.ef04First9Bytes = ef04First9Bytes
        self.file0008First3Bytes = file0008First3Bytes
        self.randomNum = randomNum
class VirtualStationConfig(TestResource):
    def __init__(self, param=None, deliveryKeyUsage="28", deliveryKeyId="41",\
                cpcPsamSlot=2,obuCappPsamSlot=1,obuDescripVehicleInfoPsamSlot=1,obuWrite08PsamSlot=1,singleRun=False):
        self.manufacturerId = param["manufacturerId"]
        self.localRoute = param["localRoute"]
        self.nextRoute = param["nextRoute"]
        self.linkMode = param["linkMode"]
        self.aid = param["aid"]
        self.cpcChannelId = param["cpcChannelId"]
        self.deliveryKeyUsage = deliveryKeyUsage
        self.deliveryKeyId = deliveryKeyId
        self.cpcPsamSlot = cpcPsamSlot
        self.obuCappPsamSlot = obuCappPsamSlot
        self.obuDescripVehicleInfoPsamSlot = obuDescripVehicleInfoPsamSlot
        self.obuWrite08PsamSlot = obuWrite08PsamSlot
        self.singleRun = singleRun
    def changeRouteInfo(self, targetRoute):
        routeBin = bin(int(targetRoute,16))[2:].zfill(16)
        hiByteBin = routeBin[0:8]
        loByteBin = routeBin[8:]
        loByteInt = int(loByteBin,2)
        if(loByteInt==10):
            loByteInt = 0
        else:
            loByteInt = loByteInt+1
        return hex(int(hiByteBin+bin(loByteInt)[2:].zfill(8),2))[2:].zfill(4)
    def changeLocalRoute(self):
        #self.localRoute = hex(int(bin(int(self.localRoute, 16))[2:].zfill(16)[0:7]+bin(random.randint(0,511))[2:].zfill(9), 2))[2:].zfill(4)
        self.localRoute = self.changeRouteInfo(self.localRoute)
    def changeNextRoute(self):
        #self.nextRoute = hex(int(bin(int(self.nextRoute, 16))[2:].zfill(16)[0:7]+bin(random.randint(0,511))[2:].zfill(9), 2))[2:].zfill(4)
        self.nextRoute = self.changeRouteInfo(self.nextRoute)
    def changeBothRoute(self):
        self.changeLocalRoute()
        self.changeNextRoute()
        uiLog(u"======================================= changing route",self.localRoute,self.nextRoute)

class TransactionError(BaseException):
    pass
class DeviceError(BaseException):
    pass
class CommunicationError(BaseException):
    pass
if __name__ == "__main__":
    pass
