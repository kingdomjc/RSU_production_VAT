#encoding:utf-8
import struct
import random
from utils import Utils
from rsuController import RsuController
from dataTypes import VirtualStationConfig,TransactionError

class ObuReader(object):
    def __init__(self, rsuController, config):
        self.rsu = rsuController
        self.config = config
    def checkObu(self, mac):
        firstByte = int(mac[0:2],16)
        if(firstByte >= 0xa0):
            raise TransactionError,"it is not a obu"
    def readRouteInfo(self):
        try:
            self.rsu.open()
            beaconId = "a4".decode("hex") + struct.pack(">I", random.randint(0, 1024*1024*16))[1:]
            currentTime = Utils.currentTime()
            res = self.rsu.initialization(beaconId, currentTime, 0, 1, "418729301a00290007", 0)
            macId = self.rsu.getCurrentMac()
            self.checkObu(macId)
            res = Utils.readRouteHead(self.rsu, 2, 6)
            print "esam head:"+res.data
            routeNum = int(res.data[38:38+2], 16)
            retRoute = Utils.readRouteInfo(self.rsu, 2, routeNum, 2, 6)
            print "esam normal route:"+retRoute
            virtualBorderRouteNum = int(res.data[44:44+2], 16)
            retRoute = Utils.readRouteInfo(self.rsu,2,virtualBorderRouteNum,6,338)
            print "esam virtual border route:"+retRoute
            res = Utils.readRouteHead(self.rsu, 1, 3)
            print "file 0008 head:"+res.data
            file08HeadBytes = res.data[8:8+6]
            select0008Cmd = "0700a40000020008"
            self.rsu.transferChannel(1,1,1,1,select0008Cmd)
            retRoute = Utils.readRouteInfo(self.rsu,1,int(file08HeadBytes[0:2],16),2,3)
            print "file 0008 route:"+retRoute
        finally:
            self.rsu.close()
    def testPsam(self):
        self.rsu.open()
        select3f00 = "0700a40000023f00"
        getChallenge = "050084000008"
        self.rsu.psamChannel(1,2,select3f00+getChallenge)
        self.rsu.close()
    def readVehicleInfo(self):
        self.rsu.open()
        beaconId = "a4".decode("hex") + struct.pack(">I", random.randint(0, 1024*1024*16))[1:]
        currentTime = Utils.currentTime()
        res = self.rsu.initialization(beaconId, currentTime, 0, 1, "418729301a00290007", 0)
        selectDf01Cmd = "0700a4000002df01"
        readVehicleInfoCmd = "0f00b400000a00000000000000000d00"
        self.rsu.transferChannel(1,1,2,2,selectDf01Cmd+readVehicleInfoCmd)
        self.rsu.close()

    def clearRouteInfo(self):
        try:
            self.rsu.open()
            beaconId = "a4".decode("hex") + struct.pack(">I", random.randint(0, 1024*1024*16))[1:]
            currentTime = Utils.currentTime()
            res = self.rsu.initialization(beaconId, currentTime, 0, 1, "418729301a00290007", 0)
            macId = self.rsu.getCurrentMac()
            self.checkObu(macId)
            iccSn = res.application[82:82+16]
            issuer = res.application[58:58+8]
            deliverkeyFactor = iccSn+issuer+issuer
            updateBinaryCmd = "0700a4000002df010b00d6840006000000000000"
            res = self.rsu.transferChannel(1,1,2,2,updateBinaryCmd)
            getRandomCmd = "0700a40000021001050084000008"
            res = self.rsu.transferChannel(1,1,1,2,getRandomCmd)
            randomNum = res.getApduBySn(2)
            deliveryKeyCmd = "15801a480110"+deliverkeyFactor
            res = self.rsu.psamChannel(self.config.obuWrite08PsamSlot, 1, deliveryKeyCmd)
            cipherDataCmd = "0d80fa000008"+randomNum
            res = self.rsu.psamChannel(self.config.obuWrite08PsamSlot, 1, cipherDataCmd)
            macCode = res.data[2:2+16]
            externalAuthCmd = "0d0082000108"+macCode
            res = self.rsu.transferChannel(1,1,1,1,externalAuthCmd)
            print res.data
            updateFile08Cmd = "0800d6880003000000"
            res = self.rsu.transferChannel(1,1,1,1,updateFile08Cmd)
            print res.data
        finally:
            self.rsu.close()
    def writeRouteFiles(self, ef04Head, file08Head):
        try:
            self.rsu.open()
            beaconId = "a4".decode("hex") + struct.pack(">I", random.randint(0, 1024*1024*16))[1:]
            currentTime = Utils.currentTime()
            res = self.rsu.initialization(beaconId, currentTime, 0, 1, "418729301a00290007", 0)
            macId = self.rsu.getCurrentMac()
            self.checkObu(macId)
            iccSn = res.application[82:82+16]
            issuer = res.application[58:58+8]
            deliverkeyFactor = iccSn+issuer+issuer
            updateBinaryCmd = "0700a4000002df010b00d6840006"+ef04Head
            res = self.rsu.transferChannel(1,1,2,2,updateBinaryCmd)
            getRandomCmd = "0700a40000021001050084000008"
            res = self.rsu.transferChannel(1,1,1,2,getRandomCmd)
            randomNum = res.getApduBySn(2)
            deliveryKeyCmd = "15801a480110"+deliverkeyFactor
            res = self.rsu.psamChannel(self.config.obuWrite08PsamSlot, 1, deliveryKeyCmd)
            cipherDataCmd = "0d80fa000008"+randomNum
            res = self.rsu.psamChannel(self.config.obuWrite08PsamSlot, 1, cipherDataCmd)
            macCode = res.data[2:2+16]
            externalAuthCmd = "0d0082000108"+macCode
            res = self.rsu.transferChannel(1,1,1,1,externalAuthCmd)
            print res.data
            updateFile08Cmd = "0800d6880003"+file08Head
            res = self.rsu.transferChannel(1,1,1,1,updateFile08Cmd)
            print res.data
        finally:
            self.rsu.close()
    def testBroadcastAid1(self):
        try:
            self.rsu.open()
            beaconId = "a4".decode("hex") + struct.pack(">I", random.randint(0, 1024*1024*16))[1:]
            currentTime = Utils.currentTime()
            res = self.rsu.initialization(beaconId, currentTime, 0, 1,"418729701a"+config.localRoute+"00290006" , 0)
            macId = self.rsu.getCurrentMac()
            self.checkObu(macId)
        finally:
            self.rsu.close()

# if __name__  == '__main__':
#     controller = RsuController("192.168.200.200", 3009)
#     config = VirtualStationConfig("a4","0600","0a00","link",1,0)
#     reader = ObuReader(controller, config)
#     #reader.readRouteInfo()
#     #reader.clearRouteInfo()
#     #reader.readVehicleInfo()
#     #reader.testPsam()
#     reader.testBroadcastAid1()