#encoding:utf-8
from utils import Utils,DataParser
from dataTypes import VirtualStationConfig,TransactionError
import time

class CpcTrade(object):
    def __init__(self, rsu, vstApplication, stationConfig):
        self.rsu = rsu
        self.vstApp = vstApplication
        self.toll = 0
        self.stationConfig = stationConfig
        self.routeData = ""
        self.maxRouteNum = 254
        self.isRouteFileFull = False
        self.isDuplicatedRoute = False
        self.isRouteOnePlaceLeft = False
        self.maxTollInfoNum = 50
        self.tollInfoLen = 10
        self.tradeMap = {"link11":self.link11TradeRun,"link21":self.link11TradeRun, "link10":self.link10TradeRun,"link20":self.link10TradeRun,\
                "broadcast11":self.broadcastTradeRun,"broadcast21":self.broadcastTradeRun,"broadcast10":self.broadcastTradeRun,"broadcast20":self.broadcastTradeRun}
    def writeBroadcastRoute(self):
        if(self.isRouteFileFull==True):
            return
        else:
            df01Ef03Head = self.df01Ef03
            totalNum = int(df01Ef03Head[0:2],16)
            updateHeadCmd = "0900d6830004"+hex(totalNum+1)[2:].zfill(2)+"01"+self.stationConfig.nextRoute
            offset = 4+(totalNum)*2
            updateRouteCmd = "0700d6"+hex(offset)[2:].zfill(4)+"02"+self.stationConfig.nextRoute
            self.rsu.transferChannel(1, 1, 1, 2, updateHeadCmd+updateRouteCmd)
    def isLocalRoute(self, routeInfo):
        return bin(int(self.stationConfig.localRoute, 16))[2:].zfill(16)[:6]==bin(int(routeInfo,16))[2:].zfill(16)[:6]
    def writeRouteInfoChannelId1(self):
        df01Ef02Head = self.df01Ef02[2:2+8]
        totalNum = int(df01Ef02Head[0:2],16)
        localRouteNum = int(df01Ef02Head[2:4],16)
        offset = 4+totalNum*2
        if(self.isRouteFileFull==True):
            return
        else:
            updateHeadCmd = ""
            updateRouteCmd = ""
            if(self.isRouteOnePlaceLeft==True):
                if(self.isDuplicatedRoute==True):
                    updateHeadCmd = "0900d6820004"+hex(totalNum+1)[2:].zfill(2)+"01"+self.stationConfig.nextRoute
                    updateRouteCmd = "0700d6"+hex(offset)[2:].zfill(4)+"02"+self.stationConfig.nextRoute
                else:
                    if(self.isLocalRoute(df01Ef02Head[4:8])):
                        localRouteNum = localRouteNum+1
                    else:
                        localRouteNum = 1
                    updateHeadCmd = "0900d6820004"+hex(totalNum+1)[2:].zfill(2)+hex(localRouteNum)[2:].zfill(2)+self.stationConfig.localRoute
                    updateRouteCmd = "0700d6"+hex(offset)[2:].zfill(4)+"02"+self.stationConfig.localRoute
            else:
                if(self.isDuplicatedRoute==True):
                    updateHeadCmd = "0900d6820004"+hex(totalNum+1)[2:].zfill(2)+"01"+self.stationConfig.nextRoute
                    updateRouteCmd = "0700d6"+hex(offset)[2:].zfill(4)+"02"+self.stationConfig.nextRoute
                else:
                    updateHeadCmd = "0900d6820004"+hex(totalNum+2)[2:].zfill(2)+"01"+self.stationConfig.nextRoute
                    updateRouteCmd = "0900d6"+hex(offset)[2:].zfill(4)+"04"+self.stationConfig.localRoute+self.stationConfig.nextRoute
            self.rsu.transferChannel(1, 1, 1, 2, updateHeadCmd+updateRouteCmd)
    def externalAuthForChannelId0FullRoute(self):
        externalAuthCmd = self.getExternalAuthCmd(self.randomNum)
        self.rsu.transferChannel(1, 1, 1, 1, externalAuthCmd)

    def writeRouteInfoChannelId0_1(self):
        #print "before calculate cpc mac ",int(round(time.time()*1000))
        mac = Utils.calculateMacWithoutGettingRandomNum(self.rsu, self.cpcId, self.provider, self.randomNum, self.stationConfig)
        tmpRoute = self.stationConfig.nextRoute if(self.isDuplicatedRoute==True) else self.stationConfig.localRoute
        res = self.rsu.transferChannel(1, 1, 0, 1, "13"+mac+tmpRoute+"01")
        if(res.returnStatus!=0):
            #external auth error or lock, need end the whole transaction
            if(res.returnStatus == 1 or res.returnStatus == 2):
                raise TransactionError,"cpc external auth error"
    def writeRouteInfoChannelId0_2(self):
        df01Ef02Head = self.df01Ef02[2:2+8]
        totalNum = int(df01Ef02Head[0:2],16)
        offset = 4+(totalNum+1)*2
        updateHeadCmd = "0900d6820004"+hex(totalNum+2)[2:].zfill(2)+"01"+self.stationConfig.nextRoute
        updateRouteCmd = "0700d6"+hex(offset)[2:].zfill(4)+"02"+self.stationConfig.nextRoute
        res = self.rsu.transferChannel(1, 1, 1, 2, updateHeadCmd+updateRouteCmd)
    def getRandomNumFromCpc(self):
        res = self.rsu.transferChannel(1,1,1,1,"050084000008")
        randomNum = res.data[2:2+16]
        return randomNum
    def generateWriteTollInfoCmd(self):
        if(self.tollInfoNum >= self.maxTollInfoNum):
            raise TransactionError, "toll record file is full"
        offset = hex(3 + self.tollInfoLen * self.tollInfoNum)[2:].zfill(4)
        tollInfoNumHexStr = hex(self.tollInfoNum + 1)[2:].zfill(2)
        updateBinaryHeadCmd = "0800d6840003"+tollInfoNumHexStr+self.stationConfig.localRoute
        updateBinaryCmd = "0f00d6"+offset+"0a"+self.stationConfig.localRoute+Utils.currentTimeHexStr()+"00000000"
        return updateBinaryHeadCmd+updateBinaryCmd
    def writeTollInfoWithExternalAuth(self):
        updateCmd = self.generateWriteTollInfoCmd()
        res = self.rsu.transferChannel(1, 1, 1, 3, updateCmd)
    def updateDf01Ef02ForChannelId0(self):
        readEf02Cmd = "0500b0820004"
        res = self.rsu.transferChannel(1,1,1,1,readEf02Cmd)
        self.df01Ef02 = res.data[0:10]
    def updateDf01Ef03ForBroadcast(self):
        readEf03Cmd = "0500b0830004"
        res = self.rsu.transferChannel(1,1,1,1,readEf03Cmd)
        self.df01Ef03 = res.data[0:10]
    def readTollInfoLocalProvinceRouteLink10(self):
        m = 80
        routeFileHead = self.df01Ef02[2:2+8]
        totalNum = int(routeFileHead[0:2],16)
        localProvinceNum = int(routeFileHead[2:4],16)
        offset = 4+(totalNum-localProvinceNum)*2
        bytesNeedRead = localProvinceNum*2
        loop = bytesNeedRead/m
        remain = bytesNeedRead%m
        selectCmd = "0700a4000002ef02"
        readTollInfoHeadCmd = "0500b0840008"
        for i in range(loop):
            if(i==0):
                readCmd = "0500b0"+hex(offset)[2:].zfill(4)+hex(m)[2:].zfill(2)
                res = self.rsu.transferChannel(1,1,1,3,readTollInfoHeadCmd+selectCmd+readCmd)
                self.tollInfoNum = int(res.data[2:4],16)
            else:
                readCmd = "0500b0"+hex(offset)[2:].zfill(4)+hex(m)[2:].zfill(2)
                res = self.rsu.transferChannel(1,1,1,1,readCmd)
            offset = offset + m
            #print res.data
        if(remain > 0):
            if(loop==0):
                readCmd = "0500b0"+hex(offset)[2:].zfill(4)+hex(remain)[2:].zfill(2)
                res = self.rsu.transferChannel(1,1,1,3,readTollInfoHeadCmd+selectCmd+readCmd)
                self.tollInfoNum = int(res.data[2:4],16)
            else:
                cmd = "0500b0"+hex(offset)[2:].zfill(4)+hex(remain)[2:].zfill(2)
                res = self.rsu.transferChannel(1,1,1,1,cmd)
            #print res.data
        if(loop==0 and remain==0):
            res = self.rsu.transferChannel(1,1,1,1,readTollInfoHeadCmd)
            self.tollInfoNum = int(res.getApduBySn(1)[0:2],16)
    def readTollInfoLocalProvinceRouteLink11(self):
        m = 80
        routeFileHead = self.df01Ef02[2:2+8]
        totalNum = int(routeFileHead[0:2],16)
        localProvinceNum = int(routeFileHead[2:4],16)
        offset = 4+(totalNum-localProvinceNum)*2
        bytesNeedRead = localProvinceNum*2
        loop = bytesNeedRead/m
        remain = bytesNeedRead%m
        selectCmd = "0700a4000002ef02"
        readTollInfoHeadCmd = "0500b0840008"
        externalAuthCmd = self.getExternalAuthCmd(self.randomNum)
        for i in range(loop):
            if(i==0):
                readCmd = "0500b0"+hex(offset)[2:].zfill(4)+hex(m)[2:].zfill(2)
                res = self.rsu.transferChannel(1,1,1,4,externalAuthCmd+readTollInfoHeadCmd+selectCmd+readCmd)
                self.tollInfoNum = int(res.getApduBySn(2)[0:2],16)
            else:
                readCmd = "0500b0"+hex(offset)[2:].zfill(4)+hex(m)[2:].zfill(2)
                res = self.rsu.transferChannel(1,1,1,1,readCmd)
            offset = offset + m
            #print res.data
        if(remain > 0):
            if(loop==0):
                readCmd = "0500b0"+hex(offset)[2:].zfill(4)+hex(remain)[2:].zfill(2)
                res = self.rsu.transferChannel(1,1,1,4,externalAuthCmd+readTollInfoHeadCmd+selectCmd+readCmd)
                self.tollInfoNum = int(res.getApduBySn(2)[0:2],16)
            else:
                cmd = "0500b0"+hex(offset)[2:].zfill(4)+hex(remain)[2:].zfill(2)
                res = self.rsu.transferChannel(1,1,1,1,cmd)
            #print res.data
        if(loop==0 and remain==0):
            res = self.rsu.transferChannel(1,1,1,2,externalAuthCmd+readTollInfoHeadCmd)
            self.tollInfoNum = int(res.getApduBySn(2)[0:2],16)
    def readLocalProvinceBroadcastRoute(self):
        m = 80
        readRouteHeadCmd = "0500b0830004"
        readTollInfoHeadCmd = "0500b0840008"
        getChallengeCmd = "050084000008"
        res = self.rsu.transferChannel(1,1,1,3,readRouteHeadCmd+readTollInfoHeadCmd+getChallengeCmd)
        routeFileHead = res.getApduBySn(1)
        self.df01Ef03 = routeFileHead
        self.tollInfoNum = int(res.getApduBySn(2)[0:2],16)
        self.randomNum = res.getApduBySn(3)
        totalNum = int(routeFileHead[0:2],16)
        if(totalNum >= self.maxRouteNum):
            self.isRouteFileFull = True
        localProvinceNum = int(routeFileHead[2:4],16)
        offset = 4+(totalNum-localProvinceNum)*2
        bytesNeedRead = localProvinceNum*2
        loop = bytesNeedRead/m
        remain = bytesNeedRead%m
        selectCmd = "0700a4000002ef03"
        externalAuthCmd = self.getExternalAuthCmd(self.randomNum)
        if(loop==0 and remain==0):
            res = self.rsu.transferChannel(1,1,1,1,externalAuthCmd)
        for i in range(loop):
            if(i==0):
                readCmd = "0500b0"+hex(offset)[2:].zfill(4)+hex(m)[2:].zfill(2)
                res = self.rsu.transferChannel(1,1,1,3,externalAuthCmd+selectCmd+readCmd)
            else:
                readCmd = "0500b0"+hex(offset)[2:].zfill(4)+hex(m)[2:].zfill(2)
                res = self.rsu.transferChannel(1,1,1,1,readCmd)
            offset = offset + m
            #print res.data
        if(remain > 0):
            if(loop==0):
                readCmd = "0500b0"+hex(offset)[2:].zfill(4)+hex(remain)[2:].zfill(2)
                res = self.rsu.transferChannel(1,1,1,3,externalAuthCmd+selectCmd+readCmd)
            else:
                cmd = "0500b0"+hex(offset)[2:].zfill(4)+hex(remain)[2:].zfill(2)
                res = self.rsu.transferChannel(1,1,1,1,cmd)
            #print res.data
    def readLocalProvinceRoute(self):
        m = 80
        routeFileHead = self.df01Ef02[2:2+8] if self.stationConfig.linkMode=="link" else self.df01Ef03[2:2+8]
        totalNum = int(routeFileHead[0:2],16)
        localProvinceNum = int(routeFileHead[2:4],16)
        offset = 4+(totalNum-localProvinceNum)*2
        bytesNeedRead = localProvinceNum*2
        loop = bytesNeedRead/m
        remain = bytesNeedRead%m
        fileName = "ef02" if self.stationConfig.linkMode=="link" else "ef03"
        selectCmd = "0700a4000002"+fileName
        self.rsu.transferChannel(1,1,1,1,selectCmd)
        for i in range(loop):
            readCmd = "0500b0"+hex(offset)[2:].zfill(4)+hex(m)[2:].zfill(2)
            res = self.rsu.transferChannel(1,1,1,1,readCmd)
            offset = offset + m
            #print res.data
        if(remain > 0):
            cmd = "0500b0"+hex(offset)[2:].zfill(4)+hex(remain)[2:].zfill(2)
            res = self.rsu.transferChannel(1,1,1,1,cmd)
            #print res.data
    def analyzeVstInfo(self, vstInfo):
        self.df01Ef02 = vstInfo.df01_ef02
        self.df01Ef03 = vstInfo.df01_ef03
        self.routeFileHead = self.df01Ef02[2:2+8] if self.stationConfig.linkMode=="link" else self.df01Ef03[2:2+8]
        self.totalNum = int(self.routeFileHead[0:2],16)
        self.lastRoute = self.routeFileHead[4:8]
        if(self.totalNum == self.maxRouteNum-1):
            self.isRouteOnePlaceLeft = True
        if(self.totalNum >= self.maxRouteNum):
            self.isRouteFileFull = True
        if(self.lastRoute == self.stationConfig.localRoute ):
            self.isDuplicatedRoute = True
        if(self.df01Ef03!=None):
            self.lastBroadcastRouteNum = int(self.df01Ef03[2:4],16)
        self.cpcId = (vstInfo.mf_ef01)[18:18+16]
        self.provider = (vstInfo.mf_ef01)[2:2+8]
        self.randomNum = vstInfo.random_num
    def link11TradeRun(self):
        '''
        link mode, aid1, channelid1
        '''
        vstInfo = DataParser.parseCpcVstApplication(self.vstApp)
        #print vstInfo.__dict__
        self.analyzeVstInfo(vstInfo)
        self.readTollInfoLocalProvinceRouteLink11()
        self.writeRouteInfoChannelId1()
        self.writeTollInfo()
        self.rsu.eventReport()
    def writeTollInfo(self):
        cmd = self.generateWriteTollInfoCmd()
        res = self.rsu.transferChannel(1, 1, 1, 2, cmd)
    def link10TradeRun(self):
        '''
        link mode, aid1, channelid0
        '''
        vstInfo = DataParser.parseCpcVstApplication(self.vstApp)
        #print vstInfo.__dict__
        self.analyzeVstInfo(vstInfo)
        if(self.isRouteFileFull==True):
            self.externalAuthForChannelId0FullRoute()
            self.readTollInfoLocalProvinceRouteLink10()
        else:
            if(self.isRouteOnePlaceLeft==True):
                self.writeRouteInfoChannelId0_1()
                self.readTollInfoLocalProvinceRouteLink10()
            else:
                if(self.isDuplicatedRoute==True):
                    self.writeRouteInfoChannelId0_1()
                    self.readTollInfoLocalProvinceRouteLink10()
                else:
                    self.writeRouteInfoChannelId0_1()
                    self.readTollInfoLocalProvinceRouteLink10()
                    self.writeRouteInfoChannelId0_2()
        self.writeTollInfo()
        self.rsu.eventReport()
    def broadcastTradeRun(self):
        vstInfo = DataParser.parseCpcVstApplication(self.vstApp)
        #print vstInfo.__dict__
        self.analyzeVstInfo(vstInfo)
        self.readLocalProvinceBroadcastRoute()
        self.writeBroadcastRoute()
        self.writeTollInfo()
        self.rsu.eventReport()
    def getExternalAuthCmd(self,randomNum):
        mac = Utils.calculateMacWithoutGettingRandomNum(self.rsu,self.cpcId,self.provider,randomNum,self.stationConfig)
        descryption = Utils.calculateAuthDataFromMac(mac)
        externalAuthCmd = "0d0082000108"+descryption
        return externalAuthCmd
    def externalAuthenticate(self):
        mac = Utils.calculateMac(self.rsu, self.cpcId, self.provider, self.stationConfig)
        descryption = Utils.calculateAuthDataFromMac(mac)
        externalAuthCmd = "0d0082000108"+descryption
        self.rsu.transferChannel(1,1,1,1,externalAuthCmd)
    def run(self):
        #print self.stationConfig.__dict__
        self.tradeMap[self.stationConfig.linkMode+hex(self.stationConfig.aid)[2:]+hex(self.stationConfig.cpcChannelId)[2:]]()