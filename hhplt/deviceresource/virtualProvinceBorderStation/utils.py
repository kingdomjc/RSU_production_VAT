#encoding:utf-8
import time
import struct
import random
from dataTypes import PreReadInfoForWriteRoute,CpcVstInfo,ObuVstInfo,DeviceError,TransactionError
from hhplt.testengine.testcase import uiLog

class Utils(object):
    @staticmethod
    def getReadableCurrentTime():
        return time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    @staticmethod
    def getPsamTerminalId(rsu, slot):
        select3f00Cmd = "0700a40000023f00"
        readTerminalId = "0500b0960006"
        enterDf01 = "0700a4000002df01"
        res = rsu.psamChannel(slot, 3, select3f00Cmd+readTerminalId+enterDf01)
        return res.data[54:54+12]
    @staticmethod
    def readRouteHead(rsu, channelId, headSize):
        fid = "df01" if channelId==2 else "1001"
        selectDf01Cmd = "0700a4000002" + fid
        fsi = "84" if channelId==2 else "88"
        readDf01Ef04HeadCmd = "0500b0"+fsi+"00"+hex(headSize)[2:].zfill(2)
        res = rsu.transferChannel(1, 1, channelId, 2, selectDf01Cmd+readDf01Ef04HeadCmd)
        return res
    @staticmethod
    def calculateRouteFileOffset(routeNum, routeSize, offset):
        return hex(offset+routeNum*routeSize)[2:].zfill(4)
    @staticmethod
    def readRouteInfo(rsu, channelId, currentRouteNum, routeSize, offset):
        m = 83
        bytesNeedRead = currentRouteNum*routeSize
        loop = bytesNeedRead/m
        remain = bytesNeedRead%m
        route = ""
        myOffset = offset
        for i in range(loop):
            readBinaryCmd = "0500b0"+hex(myOffset)[2:].zfill(4)+hex(m)[2:].zfill(2)
            res = rsu.transferChannel(1, 1, channelId, 1, readBinaryCmd)
            _len = int(res.data[0:2], 16)
            route = route+res.data[2:(_len+1-2)*2]
            myOffset = myOffset+m
        if(remain > 0):
            readBinaryCmd = "0500b0"+hex(myOffset)[2:].zfill(4)+hex(remain)[2:].zfill(2)
            res = rsu.transferChannel(1, 1, channelId, 1, readBinaryCmd)
            _len = int(res.data[0:2], 16)
            route = route+res.data[2:(_len+1-2)*2]
        return route
    @staticmethod
    def calculateAuthDataFromMac(mac):
        macH = mac[:16]
        macL = mac[16:]
        descryption = ""
        for i in range(8):
            dataH = int(macH[i*2:(i+1)*2], 16)
            dataL = int(macL[i*2:(i+1)*2], 16)
            descryption = descryption + hex(dataH^dataL)[2:].zfill(2)
        return descryption
    @staticmethod
    def calculateObuMac(rsu, psamSlot, factor):
        randomNum = Utils.getRandomNumFromIcc(rsu)
        deliveryKeyCmd = "15801a480110"+factor
        cipherDataCmd =  "0d80fa000008"+randomNum
        res = rsu.psamChannel(psamSlot, 2, deliveryKeyCmd+cipherDataCmd)
        return res.data[8:8+16]
    @staticmethod
    def calculateObuMacWithoutGettingRandom(rsu, psamSlot, factor, randomNum):
        deliveryKeyCmd = "15801a480110"+factor
        cipherDataCmd =  "0d80fa000008"+randomNum
        res = rsu.psamChannel(psamSlot, 2, deliveryKeyCmd+cipherDataCmd)
        return res.data[8:8+16]
    @staticmethod
    def calculateMacWithoutGettingRandomNum(rsu, cpcId, provider, randomNum, stationConfig):
        #print "before convert --------------", int(round(time.time()*1000))
        deliveryLevel = (int(stationConfig.deliveryKeyUsage, 16) & 0xe0)>>5
        #deliveryLevel = int(bin(int(stationConfig.deliveryKeyUsage, 16))[2:].zfill(8)[0:3], 2)
        #print "after convert --------------", int(round(time.time()*1000))
        if(deliveryLevel == 1):
            cmdLc = "08"
            cmdLen = "0d"
        elif(deliveryLevel == 2):
            cmdLc = "10"
            cmdLen = "15"
            cpcId = cpcId+provider+provider
        else: 
            raise TransactionError, "not surpported delivery level"
        delieryKeyCmd = cmdLen+"801a"+stationConfig.deliveryKeyUsage+stationConfig.deliveryKeyId+cmdLc+cpcId
        ciphserDataCmd = "1580fa000010"+randomNum+"0000000000000000"
        res = rsu.psamChannel(stationConfig.cpcPsamSlot, 2, delieryKeyCmd+ciphserDataCmd)
        return res.data[8:8+32]
    @staticmethod
    def calculateMac(rsu, cpcId, provider, stationConfig):
        randomNum = Utils.getRandomNumFromCpcWithSelectFile(rsu)
        return Utils.calculateMacWithoutGettingRandomNum(rsu, cpcId, provider, randomNum, stationConfig)
    @staticmethod
    def getRandomNumFromCpcWithSelectFile(rsu):
        res = rsu.transferChannel(1,1,1,2,"0700a4000002df01050084000008")
        randomNum = res.data[38:38+16]
        return randomNum
    @staticmethod
    def getRandomNumFromIcc(rsu):
        res = rsu.transferChannel(1,1,1,1,"050084000008")
        randomNum = res.data[2:2+16]
        return randomNum
    @staticmethod
    def currentTime():
        return struct.pack(">I",int(time.time()))
    @staticmethod
    def currentTimeHexStr():
        return struct.pack(">I",int(time.time())).encode("hex")
    @staticmethod
    def getBeaconId(manufacturerId):
        return manufacturerId.decode("hex") + struct.pack(">I", random.randint(0, 1024*1024*16))[1:]

class DataParser(object):
    @staticmethod
    def checkIccStatus(obuStatus):
        binStr = bin(int(obuStatus, 16))[2:].zfill(16)
        iccPresent = binStr[0:1]
        if(iccPresent=="1"):
            return False
        iccType = binStr[1:4]
        iccStatus = binStr[4:5]
        obuLocked = binStr[5:6]
        obuTempered = binStr[6:7]
        obuBattery = binStr[7:8]
        return True
    @staticmethod
    def checkChannelResponse(response):
        objName = type(response).__name__
        if(response.ret != 0):
            raise DeviceError, objName + "error"
        lastLen = 0
        for i in range(response.apduList):
            index = lastLen
            apduLen = int(response.data[index:index+2], 16)
            index = index + 2
            status = response.data[index:index+apduLen*2][-4:]
            uiLog(status)
            lastLen = lastLen +(apduLen+1)*2
            if(status != "9000"):
                raise TransactionError, objName+"error: "+status
    @staticmethod
    def parsePreReadInfoForWriteRoute(rawRes):
        preRead = PreReadInfoForWriteRoute()
        index = 30
        apdu1Len = int(rawRes[index:index+2], 16)
        index = index+2
        apdu1 = rawRes[index:index+apdu1Len*2]
        index = index + apdu1Len*2
        apdu2Len = int(rawRes[index:index+2], 16)
        index = index + 2
        apdu2 = rawRes[index:index+apdu2Len*2]
        index = index + apdu2Len*2 + 7*2
        apdu3Len = int(rawRes[index:index+2], 16)
        index = index + 2
        apdu3 = rawRes[index:index+apdu3Len*2]
        index = index + apdu3Len*2
        apdu4Len = int(rawRes[index:index+2], 16)
        index = index + 2
        apdu4 = rawRes[index:index+apdu4Len*2]
        preRead.ef04First9Bytes = apdu2[:-4]
        preRead.file0008First3Bytes = apdu3[:-4]
        preRead.randomNum = apdu4[:-4]
        preRead.ret = 0
        return preRead
    @staticmethod
    def parseCpcVstApplication(vstApp):
        cpcVstInfo = CpcVstInfo()
        currentIndex = 0
        indicator = vstApp[:2]
        cpcVstInfo.indicator = indicator
        binIndicator = bin(int(indicator, 16))[2:]
        currentIndex = currentIndex + 2
        indicatorMap = {0:"mf_ef01", 1:"df01_ef03", 2:"df01_ef01", 3:"df01_ef02", 4:"random_num"}
        for i in range(5):
            if(binIndicator[i] == '1'):
                start = currentIndex
                if(indicatorMap[i] != "random_num"):
                    currentIndex = currentIndex + (int(vstApp[currentIndex:currentIndex+2], 16) + 1)*2
                else:
                    currentIndex = currentIndex + 8*2
                setattr(cpcVstInfo, indicatorMap[i], vstApp[start:currentIndex])
        cpcVstInfo.equipmentClassAndVersion = vstApp[currentIndex:currentIndex+2]
        currentIndex = currentIndex + 2
        cpcVstInfo.equipmentStatus = vstApp[currentIndex:currentIndex+4]
        return cpcVstInfo
    @staticmethod
    def parseObuVstApplication(vstApp, obuConfiguration):
        index = 4
        sysInfo = vstApp[index:index+26*2]
        index = index + 26*2 + 2 
        file0015 = vstApp[index:index+41*2]
        index = index + 41*2
        file0019 = vstApp[index:index+4*2]
        index = 0 
        equipmentClassAndVersion = obuConfiguration[index:index+2]
        #print equipmentClassAndVersion
        index = index + 2
        obuStatus = obuConfiguration[index:index+2*2]
        #print obuStatus
        return  ObuVstInfo(sysInfo, file0015, file0019, equipmentClassAndVersion, obuStatus) 
if __name__ == "__main__":
    t = Utils.getReadableCurrentTime()
    uiLog(t)