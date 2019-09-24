#encoding:utf-8
from utils import Utils,DataParser
from dataTypes import VirtualStationConfig,TransactionError
import time

class ObuTrade(object):
    def __init__(self, rsu, vstApplication, obuConfiguration, stationConfig, spare=3):
        self.rsu = rsu
        self.vstApp = vstApplication
        self.obuConfiguration = obuConfiguration
        self.stationConfig = stationConfig
        self.spare = spare
        self.tradeMap = {"link":self.linkRun, "broadcast":self.broadcastRun}
        self.isEf04RouteFull = False 
        self.isEf04RouteOnePlaceLeft = False
        self.isEf04RouteDuplicated = False
        self.isEf04VirtualBorderRouteFull = False
        self.isEf04virtualborderRouteOnePlaceLeft = False
        self.isEf04VirtualBorderRouteDuplicated = False
    def getUpdateRouteHeadFirst3Cmd(self):
        if(self.isEf04RouteFull):
            return None
        else:
            cmd = "0800d6840003"
            if(self.isEf04RouteOnePlaceLeft):
                if(self.isEf04RouteDuplicated):
                    cmd = cmd + hex(self.routeNum+1)[2:].zfill(2)+self.stationConfig.nextRoute
                else:
                    cmd = cmd + hex(self.routeNum+1)[2:].zfill(2)+self.stationConfig.localRoute
            else:
                if(self.isEf04RouteDuplicated):
                    cmd = cmd + hex(self.routeNum+1)[2:].zfill(2)+self.stationConfig.nextRoute
                else:
                    cmd = cmd + hex(self.routeNum+2)[2:].zfill(2)+self.stationConfig.nextRoute
        return cmd
    def getUpdateRouteHead4_6Cmd(self):
        if(self.isEf04VirtualBorderRouteFull or self.isEf04VirtualBorderRouteDuplicated):
            return None
        else:
            cmd = "0800d6840303"
            cmd = cmd + hex(self.virtualBorderRouteNum+1)[2:].zfill(2)+self.stationConfig.localRoute
        return cmd
    def getUpdateRouteCmd(self):
        if(self.isEf04RouteFull):
            return None
        else:
            cmd = "00d6"
            if(self.isEf04RouteOnePlaceLeft):
                if(self.isEf04RouteDuplicated):
                    cmd = "07" + cmd + Utils.calculateRouteFileOffset(self.routeNum, 2, 6)+"02"+self.stationConfig.nextRoute
                else:
                    cmd = "07" + cmd + Utils.calculateRouteFileOffset(self.routeNum, 2, 6)+"02"+self.stationConfig.localRoute
            else:
                if(self.isEf04RouteDuplicated):
                    cmd = "07" + cmd + Utils.calculateRouteFileOffset(self.routeNum, 2, 6)+"02"+self.stationConfig.nextRoute
                else:
                    cmd = "09" + cmd + Utils.calculateRouteFileOffset(self.routeNum, 2, 6)+"04"+self.stationConfig.localRoute+self.stationConfig.nextRoute
        return cmd

    def getUpdateVirtualBorderRouteCmd(self):
        if self.isEf04VirtualBorderRouteFull or self.isEf04VirtualBorderRouteDuplicated:
            return None
        else:
            return "0b00d6" + Utils.calculateRouteFileOffset(self.virtualBorderRouteNum, 6, 338)+"06"+self.stationConfig.localRoute+Utils.currentTimeHexStr()

    def readEf04RouteInfo(self):
        res = Utils.readRouteHead(self.rsu, 2, 6)
        print res.data
        maxRouteNum = 166
        maxVirtualBorderNum = 29
        ef04Head = res.getApduBySn(2)
        self.routeNum = int(ef04Head[0:2], 16)
        if self.routeNum == (maxRouteNum - 1):
            self.isEf04RouteOnePlaceLeft = True
        elif self.routeNum >= maxRouteNum:
            self.isEf04RouteFull = True
        lastRoute = ef04Head[2:2+4]
        if lastRoute == self.stationConfig.localRoute:
            self.isEf04RouteDuplicated = True
        self.virtualBorderRouteNum = int(ef04Head[6:6+2], 16)
        if self.virtualBorderRouteNum == maxVirtualBorderNum-1:
            self.isEf04virtualborderRouteOnePlaceLeft = True
        elif self.virtualBorderRouteNum >= maxVirtualBorderNum:
            self.isEf04VirtualBorderRouteFull = True
        lastVirtualBorderRoute = ef04Head[8:8+4]
        if lastVirtualBorderRoute == self.stationConfig.localRoute:
            self.isEf04VirtualBorderRouteDuplicated = True
        retRoute = Utils.readRouteInfo(self.rsu, 2, self.routeNum, 2, 6)
        return retRoute

    def writeEf04RouteInfo(self):
        cmd1 = self.getUpdateRouteHeadFirst3Cmd()
        cmd2 = self.getUpdateRouteCmd()
        cmd3 = self.getUpdateRouteHead4_6Cmd()
        cmd4 = self.getUpdateVirtualBorderRouteCmd()
        if (cmd1 is None) and (cmd3 is None):
            return
        else:
            if cmd1 is None:
                self.rsu.transferChannel(1, 1, 2, 2, cmd3+cmd4)
            elif cmd3 is None:
                self.rsu.transferChannel(1, 1, 2, 2, cmd1+cmd2)
            else:
                self.rsu.transferChannel(1, 1, 2, 4, cmd1+cmd2+cmd3+cmd4)
    def readFile08AndFile15(self):
        readFile08Cmd = "0500b0880006"
        readFile15Cmd = "0500b0950029"
        res = self.rsu.transferChannel(1,1,1,2,readFile08Cmd+readFile15Cmd)
        return res.data[2:2+6],res.data[20:82]
    def write08RouteInfo(self):
        maxRouteNum = 62
        #selectCmd = "0700a40000021001"
        readHeadCmd = "0500b0880003"
        getChallengeCmd = "050084000008"
        #res = self.rsu.transferChannel(1, 1, 1, 3, selectCmd+readHeadCmd+getChallengeCmd)
        res = self.rsu.transferChannel(1, 1, 1, 2, readHeadCmd+getChallengeCmd)
        tmpRandomNum = res.getApduBySn(2)
        file08HeadBytes = res.getApduBySn(1)
        currentNum = int(file08HeadBytes[0:2], 16)
        if(currentNum >= maxRouteNum):
            mac = Utils.calculateObuMacWithoutGettingRandom(self.rsu, self.stationConfig.obuWrite08PsamSlot,self.iccDeliveryFactor,tmpRandomNum)
            externalAuthCmd = "0d0082000108"+mac
            self.rsu.transferChannel(1,1,1,1,externalAuthCmd)
            return
        else:
            if(currentNum == maxRouteNum-1):
                if(file08HeadBytes[2:]==self.stationConfig.localRoute):
                    updateHeadCmd = "0800d6880003"+hex(currentNum+1)[2:].zfill(2)+self.stationConfig.nextRoute
                    updateRouteCmd = "0700d6" + Utils.calculateRouteFileOffset(currentNum, 2, 3) + "02"+self.stationConfig.nextRoute
                else:
                    updateHeadCmd = "0800d6880003"+hex(currentNum+1)[2:].zfill(2)+self.stationConfig.localRoute
                    updateRouteCmd = "0700d6" + Utils.calculateRouteFileOffset(currentNum, 2, 3) + "02"+self.stationConfig.localRoute
            else:
                if(file08HeadBytes[2:]==self.stationConfig.localRoute):
                    updateHeadCmd = "0800d6880003"+hex(currentNum+1)[2:].zfill(2)+self.stationConfig.nextRoute
                    updateRouteCmd = "0700d6" + Utils.calculateRouteFileOffset(currentNum, 2, 3) + "02"+self.stationConfig.nextRoute
                else:
                    updateHeadCmd = "0800d6880003"+hex(currentNum+2)[2:].zfill(2)+self.stationConfig.nextRoute
                    updateRouteCmd = "0900d6" + Utils.calculateRouteFileOffset(currentNum, 2, 3) + "04"+self.stationConfig.localRoute+self.stationConfig.nextRoute
            mac = Utils.calculateObuMacWithoutGettingRandom(self.rsu, self.stationConfig.obuWrite08PsamSlot,self.iccDeliveryFactor,tmpRandomNum)
            externalAuthCmd = "0d0082000108"+mac
            self.rsu.transferChannel(1,1,1,3,externalAuthCmd+updateHeadCmd+updateRouteCmd)
    def initCappForPurchase(self):
        initCappPurchaseCmd = "10805003020b" +"01" + "00000000"+ self.obuPsamTerminalId
        res = self.rsu.transferChannel(1,1,1,1,initCappPurchaseCmd)
        self.remainMoney = res.data[2:2+8]
        self.tradeSn = res.data[10:10+4]
        self.creditLine = res.data[14:14+6]
        self.algorythmVersion = res.data[20:22]
        self.keyId = res.data[22:24]
        self.cappRandom1 = res.data[24:24+8]
        self.tradeTime = Utils.getReadableCurrentTime()
        calcMac1Cmd = "2a8070000024"+self.cappRandom1+self.tradeSn+"00000000"+"09"+self.tradeTime+self.algorythmVersion+self.keyId+self.iccDeliveryFactor+"08"
        res = self.rsu.psamChannel(self.stationConfig.obuCappPsamSlot,1,calcMac1Cmd)
        self.terminalTradeSn = res.data[2:2+8]
        self.mac1 = res.data[10:10+8]
    def updateCappDataCache(self):
        timeStr = Utils.currentTimeHexStr()
        vehicleType = self.vehicleInfo[28:30]
        vehiclePlateNo = self.vehicleInfo[:24]
        print "---------",timeStr,vehicleType,vehiclePlateNo
        updateCappDataCacheCmd = "3080dcaac82baa29000026043133"+timeStr+vehicleType+"0301010100000007218400099902"+vehiclePlateNo+"00000000"
        self.rsu.transferChannel(1,1,1,1,updateCappDataCacheCmd)
    def debitForCappPurchase(self):
        debitForCappPurchaseCmd = "14805401000f"+self.terminalTradeSn+self.tradeTime+self.mac1
        self.rsu.transferChannel(1,1,1,1,debitForCappPurchaseCmd)
    def updateCappDataCacheAndDebitForCappPurchase(self):
        timeStr = Utils.currentTimeHexStr()
        vehicleType = self.vehicleInfo[28:30]
        vehiclePlateNo = self.vehicleInfo[:24]
        updateCappDataCacheCmd = "3080dcaac82baa29000026043133"+timeStr+vehicleType+"0301010100000007218400099902"+vehiclePlateNo+"00000000"
        debitForCappPurchaseCmd = "14805401000f"+self.terminalTradeSn+self.tradeTime+self.mac1
        self.rsu.transferChannel(1,1,1,2,updateCappDataCacheCmd + debitForCappPurchaseCmd)
    def iccCappPurchase(self):
        self.obuPsamTerminalId = Utils.getPsamTerminalId(self.rsu, self.stationConfig.obuCappPsamSlot)
        self.initCappForPurchase()
        self.updateCappDataCacheAndDebitForCappPurchase()
    def getPlainVehicleInfo(self):
        getSecureRes = self.rsu.getSecure(0, 1, 1, "0000000000000000", 1, 1, 0, 16,"0000000000000000", 0, 0)
        print "get secure",getSecureRes.__dict__
        vehicleInfo = getSecureRes.fileData[:getSecureRes.length*2]
        deliveryFactor = self.contractSn + self.releaseId + self.releaseId
        deliveryKeyCmd = "15801a590310"+deliveryFactor
        cipherDataCmd = "2580fa800020" + vehicleInfo
        cipherDataRes = self.rsu.psamChannel(self.stationConfig.obuDescripVehicleInfoPsamSlot, 2, deliveryKeyCmd+cipherDataCmd)
        vehicleInfoLen = int(cipherDataRes.data[6:8],16)-2-9
        self.vehicleInfo = cipherDataRes.data[26:26+vehicleInfoLen*2]
        print "vehicle info",self.vehicleInfo
    def clearRouteInfo(self):
        clear08RouteCmd = "0800d6880003000000"
        self.rsu.transferChannel(1,1,1,1,clear08RouteCmd)
        clearEf04RouteCmd = "0800d6840003000000"  
        self.rsu.transferChannel(1,1,2,1,clearEf04RouteCmd )
    def linkRun(self):
        self.getPlainVehicleInfo()
        routeInfo = self.readEf04RouteInfo()
        self.writeEf04RouteInfo()
        if(DataParser.checkIccStatus(self.obuStatus)):
            self.write08RouteInfo()
            self.iccCappPurchase()
            self.clearRouteInfo()
        self.rsu.setMmi(1,1,0)
        self.rsu.eventReport()
    def broadcastRun(self):
        self.linkRun()
    def read0015(self):
        select1001Cmd = "0700a40000021001"
        read0015Cmd = "0500b0950029"
        res = self.rsu.transferChannel(1,1,1,2,select1001Cmd+read0015Cmd)
        return res.data[8:8+41*2]
    def run(self):
        vstInfo = DataParser.parseObuVstApplication(self.vstApp, self.obuConfiguration)
        self.contractSn = vstInfo.sysInfo[20:20+16]
        self.releaseId = vstInfo.sysInfo[:8]
        self.obuStatus = vstInfo.obuStatus
        self.iccSn = vstInfo.file0015[24:24+8*2]
        self.issuerId = vstInfo.file0015[0:8]
        self.iccDeliveryFactor = self.iccSn+self.issuerId+self.issuerId
        print "--------------------------",self.iccDeliveryFactor
        self.tradeMap[self.stationConfig.linkMode]()
