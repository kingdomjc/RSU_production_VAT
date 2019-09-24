#encoding:utf-8
from utils import Utils,DataParser
import struct
import random
from rsuController import RsuController
from dataTypes import VirtualStationConfig,TransactionError
from hhplt.testengine.testcase import uiLog

class CpcReader(object):
    def __init__(self, rsuController, config):
        self.rsu = rsuController
        self.stationConfig = config
    def analyzeVstInfo(self, vstInfo):
        self.df01Ef02 = vstInfo.df01_ef01
        self.cpcId = (vstInfo.mf_ef01)[18:18+16]
        self.provider = (vstInfo.mf_ef01)[2:2+8]
        self.randomNum = vstInfo.random_num
    def writeBroadcastFiles(self,routeFile,tollFile):
        try:
            self.rsu.open()
            beaconId = "a4".decode("hex") + struct.pack(">I", random.randint(0, 1024*1024*16))[1:]
            currentTime = Utils.currentTime()
            res = self.rsu.initialization(beaconId, currentTime, 0, 1, "418729301a00290007", 0)
            macId = self.rsu.getCurrentMac()
            self.checkCpc(macId)
            vstInfo = DataParser.parseCpcVstApplication(res.application)
            self.analyzeVstInfo(vstInfo)
            mac = Utils.calculateMac(self.rsu, self.cpcId, self.provider, self.stationConfig)
            descryption = Utils.calculateAuthDataFromMac(mac)
            externalAuthCmd = "0d0082000108"+descryption
            res = self.rsu.transferChannel(1, 1, 1, 1, externalAuthCmd)
            writeRouteCmd = "0900d6830004"+routeFile
            writeTollCmd = "0800d6840003"+tollFile
            res = self.rsu.transferChannel(1, 1, 1, 2, writeRouteCmd+writeTollCmd)
            self.rsu.eventReport()
        finally:
            self.rsu.close()
    def writeLinkFiles(self,routeFile,tollFile):
        try:
            self.rsu.open()
            beaconId = "a4".decode("hex") + struct.pack(">I", random.randint(0, 1024*1024*16))[1:]
            currentTime = Utils.currentTime()
            res = self.rsu.initialization(beaconId, currentTime, 0, 1, "418729301a00290007", 0)
            macId = self.rsu.getCurrentMac()
            self.checkCpc(macId)
            vstInfo = DataParser.parseCpcVstApplication(res.application)
            self.analyzeVstInfo(vstInfo)
            mac = Utils.calculateMac(self.rsu, self.cpcId, self.provider, self.stationConfig)
            descryption = Utils.calculateAuthDataFromMac(mac)
            externalAuthCmd = "0d0082000108"+descryption
            res = self.rsu.transferChannel(1, 1, 1, 1, externalAuthCmd)
            writeRouteCmd = "0900d6820004"+routeFile
            writeTollCmd = "0800d6840003"+tollFile
            res = self.rsu.transferChannel(1, 1, 1, 2, writeRouteCmd+writeTollCmd)
            self.rsu.eventReport()
        finally:
            self.rsu.close()
    def clearFileInfo(self,updateApdu):
        '''
        updateApdu: 0700d68200020000,0700d68300020000,0600d684000100
        '''
        try:
            self.rsu.open()
            beaconId = "a4".decode("hex") + struct.pack(">I", random.randint(0, 1024*1024*16))[1:]
            currentTime = Utils.currentTime()
            res = self.rsu.initialization(beaconId, currentTime, 0, 1, "418729301a00290007", 0)
            macId = self.rsu.getCurrentMac()
            self.checkCpc(macId)
            vstInfo = DataParser.parseCpcVstApplication(res.application)
            self.analyzeVstInfo(vstInfo)
            mac = Utils.calculateMac(self.rsu, self.cpcId, self.provider, self.stationConfig)
            descryption = Utils.calculateAuthDataFromMac(mac)
            externalAuthCmd = "0d0082000108"+descryption
            res = self.rsu.transferChannel(1, 1, 1, 1, externalAuthCmd)
            uiLog(res.data)
            res = self.rsu.transferChannel(1, 1, 1, 1, updateApdu)
            uiLog(res.data)
            self.rsu.eventReport()
        finally:
            self.rsu.close()
    def checkCpc(self, mac):
        firstByte = int(mac[0:2],16)
        if(firstByte < 0xa0):
            raise TransactionError,"it is not a cpc"
    def readLinkRouteFile(self):
        self.readAWholeFile(512, "ef02")
    def readBroadcastRouteFile(self):
        self.readAWholeFile(512, "ef03")
    def readTollInfoFile(self):
        self.readAWholeFile(512, "ef04")
    def readAWholeFile(self, size, fileName):
        self.rsu.open()
        beaconId = "a4".decode("hex") + struct.pack(">I", random.randint(0, 1024*1024*16))[1:]
        currentTime = Utils.currentTime()
        res = self.rsu.initialization(beaconId, currentTime, 0, 1, "418729301a00290007", 0)
        m = 83
        bytesNeedRead = size
        loop = bytesNeedRead/m
        remain = bytesNeedRead%m
        route = ""
        myOffset = 0
        selectFileCmd = "0700a4000002"+fileName
        self.rsu.transferChannel(1,1,1,1,selectFileCmd)
        for i in range(loop):
            readBinaryCmd = "0500b0"+hex(myOffset)[2:].zfill(4)+hex(m)[2:].zfill(2)
            res = self.rsu.transferChannel(1, 1, 1, 1, readBinaryCmd)
            _len = int(res.data[0:2], 16)
            route = route+res.data[2:(_len+1-2)*2]
            myOffset = myOffset+m
        if(remain > 0):
            readBinaryCmd = "0500b0"+hex(myOffset)[2:].zfill(4)+hex(remain)[2:].zfill(2)
            res = self.rsu.transferChannel(1, 1, 1, 1, readBinaryCmd)
            _len = int(res.data[0:2], 16)
            route = route+res.data[2:(_len+1-2)*2]
        self.rsu.eventReport()
        self.rsu.close()
        uiLog(route)

if __name__  == '__main__':
    controller = RsuController("192.168.200.200", 3009)
    config = VirtualStationConfig("a4","0600","0a00","link",1,0)
    reader = CpcReader(controller, config)
    #reader.clearFileInfo("0600d684000100")
    reader.readLinkeRouteFile()