#encoding:utf-8
"""
模块: CPC卡测试发卡器

提供入口（开卡）、出口（关卡）、读路径、读系统信息等功能
"""
import random
import time

from hhplt.deviceresource import TestResource
from device import RSU
from hhplt.productsuite.CPC.macutil import transCpcIdToMac
from hhplt.testengine.exceptions import TestItemFailException, AbortTestException
from hhplt.testengine.testcase import uiLog


def timestamp_datatime(value):
    timeInt = int(value, 16)
    format = '%Y-%m-%d %H:%M'
    #format = '%Y-%m-%d %H:%M:%S'
    #value 为时间戳值,如:1460073600.0
    timeInt = time.localtime(timeInt)
    dt = time.strftime(format,timeInt)
    return dt




GLOBAL = {}
bst_res_map = {}

class CpcTraderIssuer(TestResource):

    def __init__(self,param):
        self.dll = None
        self.reader = RSU()
        self.param = param

    def initResource(self):
        self.reader.RSU_Open(2,None,None)
        pass

    def retrive(self):
        self.reader.RSU_Close()

    def __record(self,cmd,msg):
        uiLog(u"%s:%s" % (cmd,msg))

    def HFCloseRF(self):
        # 关闭射频
        self.reader.HFCloseRF()

    def cpcHfActive(self):
        # 高频唤醒，
        self.__record('cpcHfactive.rq', u'send')
        ret,dataLength,Data,ReturnStatus = self.reader.HFActive(200)
        uiLog("cpcHfactive.rp: ret=%d,dataLength=%d,Data=%s,ReturnStatus=%d"%(ret,dataLength,Data,ReturnStatus))
        if ret !=0:
            self.__record('cpcHfactive.rp', u'接收异常 error code = %d'%(ret))
            raise TestItemFailException(failWeight = 10,message = u'高频唤醒失败')

    def cpcHFSelectDf01(self):
        # 选取DF01文件
        # APDU = "0700A40000021001"
        APDU = "0700A4000002df01"
        self.__record('cpcHFSelectDf01.rq', u'send')
        ret, APDULIST, Data, ReturnStatus = self.reader.HFCmd(1, APDU)
        uiLog("cpcHFSelectDf01.rp: ret=%dAPDULIST=%d,Data=%s,ReturnStatus=%d" % (ret, APDULIST, Data, ReturnStatus))
        if ret != 0:
            self.__record('cpcHFSelectDf01.rp', u'接收异常 error code = %d' % (ret))
            raise TestItemFailException(failWeight = 10,message = u'cpcHFSelectDf01异常:ret=%d'%ret)
        if ReturnStatus != 0:
            self.__record('cpcHFSelectDf01.rp', u'ReturnStatus error code = %d' % ReturnStatus)
            raise TestItemFailException(failWeight = 10,message = u'cpcHFSelectDf01异常:ReturnStatus=%d'%ReturnStatus)
        self.__record('cpcHFSelectDf01.rp', u'success')


    def cpcHFReadRouteInfo(self, routeIndex):
        # 读取路径信息
        routeFile = "83" if 0 == routeIndex else "82"
        readRouteCmds = [
            "0500b0" + routeFile + "0067",
            "0500b0" + routeFile + "6760",
            "0500b0" + routeFile + "C738",
            "0500b0" + routeFile + "FF7a" ]

        Datas = []
        for i in range(1,5):
            APDU = readRouteCmds[i-1]
            ret,APDULIST,UnitData,ReturnStatus = self.reader.HFCmd(1, APDU)
            if ret != 0 or ReturnStatus != 0:
                raise TestItemFailException(failWeight = 10,message = u'读取路径信息失败(CMD=%s),ret=%d,ReturnStatus=%d'%(APDU,ret,ReturnStatus))
            #uiLog(u"路径信息Data%d:%s"%(i,UnitData))
            Datas.append(UnitData)

        Data = Datas[0][2:208] + Datas[1][2:194] + Datas[2][2:114] + Datas[3][2:246]
        uiLog("cpcHFReadRouteInfo.rp:Data=%s"%Data)
        routeNum = int(Data[0:2],16)
        if routeNum > 0:
            uiLog(u"路径信息个数：%d"%routeNum)
            #strLog = u"最新路径信息：%s\n"%(Data[2:14])
            lastRoute = Data[2:14]
            strTime = timestamp_datatime(lastRoute[4:])
            uiLog(u"最新路径信息：%s---%s"%(lastRoute, strTime))
            Num = 62 if routeNum>62 else routeNum
            for i in range(0,Num):
                lastRoute = Data[14+i*12:14+i*12+12]
                strTime = timestamp_datatime(lastRoute[4:])
                strLog = u"路径信息%d:%s---%s"%(i+1,lastRoute, strTime)
                uiLog(strLog)
            self.__record('cpcHFReadRouteInfo.rp', u'success')
        else:
            raise TestItemFailException(failWeight = 10,message = u'没有路径信息')
        return Data

    def cpcHFReadSysInfo(self):
        # 读CPC系统信息
        APDU = "0500b081001e"
        self.__record('cpcHFReadSysInfo.rq', u'send')
        ret, APDULIST, Data, ReturnStatus = self.reader.HFCmd(1, APDU)
        uiLog("cpcHFReadSysInfo.rp: ret=%dAPDULIST=%d,Data=%s,ReturnStatus=%d" % (ret, APDULIST, Data, ReturnStatus))
        if ret != 0 or ReturnStatus != 0:
            self.__record('cpcHFReadSysInfo.rp', u'接收异常 error code = %d' % ret)
            raise TestItemFailException(failWeight = 10,message = u'cpcHFReadSysInfo.rp,ret =%d,ReturnStatus=%d'%(ret,ReturnStatus))
        self.__record('cpcHFReadSysInfo.rp', u'success')
        cpcArea = Data[2:10]
        GLOBAL["cpcarea"] = cpcArea
        cpcId = Data[18:34]
        # 卡号、CPCID、版本号、合同签署日期、合同过期日期
        cardNo,cpcId,versionId,signDate,expireDate = Data[2:18], Data[18:34], Data[34:36], Data[36:44], Data[44:52]
        uiLog(u"卡号:%s、CPCID:%s、版本号:%s、合同签署日期:%s、合同过期日期:%s"%(cardNo,cpcId,versionId,signDate,expireDate))
        return {"cpcArea": cpcArea,"cardNo":cardNo,"cpcId":cpcId,"versionId":versionId,"signDate":signDate,"expireDate":expireDate}

    def cpcReadSn(self):
        # 射频方式读取SN
        APDU = "0580F6000304"
        ret, APDULIST, Data, ReturnStatus = self.reader.HFCmd(1,APDU)
        uiLog("cpcReadSn.rp: ret=%d,APDULIST=%d,Data=%s,ReturnStatus=%d" % (ret, APDULIST, Data, ReturnStatus))
        if ret != 0 or ReturnStatus != 0:
            self.__record('cpcReadSn.rp', u'接收异常 error code = %d' % ret)
            raise TestItemFailException(failWeight = 10,message = u'cpcReadSn.rp,ret =%d,ReturnStatus=%d'%(ret,ReturnStatus))
        rtnApduLen = int(Data[:2],16)
        rtnApduCode = Data[2:][rtnApduLen*2-4:rtnApduLen*2]
        rtnApduData = Data[2:][:rtnApduLen*2-4]
        if rtnApduCode != "9000":
            raise TestItemFailException(failWeight = 10,message = u'cpcReadSn.rp,rtnApdu:%s'%Data)
        return rtnApduData

    def iccHFSelectDf01(self):
        APDU = "0700A40000021001"
        self.__record('iccHFSelectDf01.rq', u'send')
        ret, APDULIST, Data, ReturnStatus = self.reader.HFCmd(1, APDU)
        uiLog("iccHFSelectDf01.rp: ret=%dAPDULIST=%d,Data=%s,ReturnStatus=%d" %  (ret, APDULIST, Data, ReturnStatus))
        if ret != 0 or ReturnStatus != 0:
            self.__record('iccHFSelectDf01.rp', u'接收异常 error code = %d' % (ret))
            raise TestItemFailException(failWeight = 10,message = u'iccHFSelectDf01异常:ret=%d,ReturnStatus=%d'%(ret,ReturnStatus))
        self.__record('cpcHFSelectDf01.rp', u'success')



    def activePasm(self,psamSoftId):
        #复位PSAM
        self.__record('active psam_rq', 'send')
        ret, rlen, Data = self.reader.PSAM_Reset(psamSoftId, 0)
        uiLog('activePasm: ret=%d,len=%d,data=%s' % (ret, rlen, Data))
        if ret != 0:
            self.__record('active psam_rp', u'通信异常 error code = %d' % ret)
            raise AbortTestException(message = u"复位PSAM失败")
        self.__record('active psam_rp', 'success')

    def selectPsamDf01(self,psamSoftId ):
        # 选择PSAM的DF01文件
        APDU = "0700A4000002DF01"
        self.reader.setTimeout(5000)
        self.__record('psam selectDf01.rq', u'send')
        ret, APDUList, Data = self.reader.PSAM_CHANNEL(psamSoftId, 1, APDU)
        uiLog("selectDf01:ret=%d,APDUList=%d,Data=%s" % (ret, APDUList, Data))
        if ret != 0:
            self.__record('psam selectDf01.rp', u'通信异常error code =%d' % (ret))
            raise TestItemFailException(failWeight = 10,message = u'psam selectDf01.rp,ret =%d'%ret)
        self.__record('psam selectDf01.rp', u'success')


    def cpcHFReadBaseInfo(self):
        # 读取CPC状态
        APDU = "0500b0820020"
        self.__record('cpcHFReadBaseInfo.rq', u'send')
        ret, APDULIST, Data, ReturnStatus = self.reader.HFCmd(1, APDU)
        uiLog("cpcHFReadBaseInfo.rp: ret=%dAPDULIST=%d,Data=%s,ReturnStatus=%d" % (ret, APDULIST, Data, ReturnStatus))
        if ret != 0 or ReturnStatus != 0:
            self.__record('cpcHFReadBaseInfo.rp', u'接收异常 error code = %d' % (ret))
            raise TestItemFailException(failWeight = 10,message = u'cpcHFReadBaseInfo.rp,ret =%d,ReturnStatus=%d'%(ret,ReturnStatus))
        self.__record('cpcHFReadBaseInfo.rp', u'success')
        powerInfo = Data[2:4]
        RfpowerFlag = Data[4:6]
        powerInfo = int(powerInfo , 16)
        powerFlag = (powerInfo & 0x80) >> 7
        powerRatio = powerInfo & 0x7f
        uiLog(u"CPC状态:"+Data)
        uiLog(u"剩余电量百分之%d(%s)" % (powerRatio,(u"电量低" if powerFlag == 0x01 else u"电量正常")))
        RfpowerFlag = int(RfpowerFlag, 16)
        uiLog(u"cpc卡射频处于%s状态"%(u"上电" if RfpowerFlag == 1 else u"断电"))
        return {"RfpowerFlag":RfpowerFlag,"powerRatio":powerRatio}

    def deliverKey(self,psamSoftId,cpcId):
        # 分散密钥
        # 捷德测试PSAM 28 41
        # 交通部提供捷德SM4 PSAM
        # lc = "10"
        # p1p2 = "4844"
        # APDU = "15"+"801A" + p1p2 + lc + cpcId + GLOBAL["cpcarea"] + GLOBAL["cpcarea"]
        # 我们自己的测试卡
        lc = "08"
        p1p2 = "4844"
        APDU = "0d" + "801A" + p1p2 + lc + cpcId
        print "delverkey:" + APDU
        self.__record('deliverkey.rq', 'send')
        ret, APDUList, Data = self.reader.PSAM_CHANNEL(psamSoftId, 1, APDU)
        uiLog("deliverkey.rp: ret=%d,APDUList=%d,Data=%s" % (ret, APDUList, Data))
        apduLength = int(Data[:2], 16)
        if Data[2:][apduLength * 2 - 4:apduLength * 2] != "9000":
            self.__record('deliverkey.rp', u'psam error code =%d' % (int(Data[:2], 16)))
            raise TestItemFailException(failWeight = 10,message = u'分散密钥失败:psam error code =%d' % (int(Data[:2], 16)))
        if ret != 0:
            self.__record('deliverkey.rp', u'通信异常error code =%d' % ret)
            raise TestItemFailException(failWeight = 10,message = u'分散密钥失败:通信异常error code =%d' % ret)
        self.__record('deliverkey.rp', 'success')

    def cpcHFGetRand(self):
        # 获得随机数
        APDU = "050084000008"
        self.__record('cpcHFGetRand.rq', u'send')
        ret, APDULIST, Data, ReturnStatus = self.reader.HFCmd(1, APDU)
        uiLog("cpcHFGetRand.rp: ret=%dAPDULIST=%d,Data=%s,ReturnStatus=%d" % (ret, APDULIST, Data, ReturnStatus))
        if ret != 0:
            self.__record('cpcHFGetRand.rp', u'通信异常error code =%d' % (ret))
            raise TestItemFailException(failWeight = 10,message = u'获取随机数失败:通信异常error code =%d' % ret)
        self.__record('cpcHFGetRand.rp', u'success')
        rand = Data[2:18]
        return rand


    def psamGenerateMac(self,psamSoftId,rand):
        # PSAM生成MAC
        lc = "10"
        # APDU = "15"+"80FA0000" + lc + GLOBAL["rand"][0:8] + "00000000"+ "0000000000000000"
        APDU = "15" + "80FA0000" + lc + rand[0:16] + "0000000000000000"
        print "cpcHFgeneratMac:" + APDU
        self.__record('psamgeneratMac.rq', 'send')
        ret, APDUList, Data = self.reader.PSAM_CHANNEL(psamSoftId, 1, APDU)
        strLog = "psamgeneratMac.rp: ret=%d,APDUList=%d,Data=%s" % (ret, APDUList, Data)
        uiLog(strLog)
        apduLength = int(Data[:2], 16)
        if Data[2:][apduLength * 2 - 4:apduLength * 2] != "9000":
            self.__record('psamgeneratMac.rp', u'psam error code =%d' % (int(Data[:2], 16)))
            raise AbortTestException(message = u"PSAM生成MAC失败:ret code is %s" % Data[-4:])
        if ret != 0:
            self.__record('psamgeneratMac.rp', u'通信异常error code =%d' % (ret))
            raise AbortTestException(message = u"PSAM生成MAC失败:ret=%d"%ret)
        self.__record('psamgeneratMac.rp', 'success')
        cpc_mac = Data[2:34]
        uiLog(u"生成MAC:%s"%cpc_mac)
        return cpc_mac

    def cpcHFexternalAuth(self,cpc_mac):
        # 外部认证
        authData = [ord(c) for c in cpc_mac.decode("hex")]
        authorData = [ authData[i] ^ authData[i + 8] for i in range(0,8) ]
        arthDatastr = str(bytearray(authorData[0:8])).encode("hex")

        APDU = "13" + "0082000108" + arthDatastr
        print "cpcHFexternalAuth:" + APDU
        self.__record('cpcHFexternalAuth.rq', 'send')
        ret, APDULIST, Data, ReturnStatus = self.reader.HFCmd(1, APDU)
        uiLog("cpcHFexternalAuth.rp: ret=%dAPDULIST=%d,Data=%s,ReturnStatus=%d" % (ret, APDULIST, Data, ReturnStatus))

        apduLength = int(Data[:2], 16)
        if Data[2:][apduLength * 2 - 4:apduLength * 2] != "9000":
            self.__record('cpcHFexternalAuth.rp', u'error code =%d' % (int(Data[:2], 16)))
            raise TestItemFailException(failWeight = 10,message = u'认证失败:cpcHFexternalAuth,error code=%s' % Data[-4:])
        if ret != 0:
            self.__record('cpcHFexternalAuth.rp', u'通信异常error code =%d' % (ret))
            raise TestItemFailException(failWeight = 10,message = u'认证失败:cpcHFexternalAuth,error code=%d' % ret)
        self.__record('cpcHFexternalAuth.rp', 'success')

    def cpcHFWriteEntryInfo(self,cardState):
        # 写入口信息
        cmdLen = "06"
        wLen = "01"
        strtime = "%8x" % (time.time())
        APDU = cmdLen + "00d68117" + wLen + cardState
        print "cpcHFWriteEntryInfo:" + APDU
        self.__record('cpcHFWriteEntryInfo.rq', u'send')
        ret, APDULIST, Data, ReturnStatus = self.reader.HFCmd(1, APDU)
        uiLog("cpcHFWriteEntryInfo.rp: ret=%dAPDULIST=%d,Data=%s,ReturnStatus=%d" %  (ret, APDULIST, Data, ReturnStatus))
        if ret != 0 or ReturnStatus != 0:
            self.__record('cpcHFWriteEntryInfo.rp', u'接收异常 error code = %d' % (ret))
            raise TestItemFailException(failWeight = 10,message = u'写入口信息失败:cpcHFWriteEntryInfo,ret=%d,ReturnStatus=%d' % (ret,ReturnStatus))
        self.__record('cpcHFWriteEntryInfo.rp', u'success')

    def cpcHFClearRouteInfo(self, routeIndex):
        # 清除路径信息
        routeFile = "83" if 0 == routeIndex else "82"
        cmdLen = "65"
        cmdFileLen = "60"
        cmdFile = "000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000000"
        APDU = cmdLen + "00d6" + routeFile + "00" + cmdFileLen + cmdFile
        self.__record('cpcHFClearRouteInfo.rq', u'send')
        ret, APDULIST, Data, ReturnStatus = self.reader.HFCmd(1, APDU)
        uiLog("cpcHFClearRouteInfo.rp: ret=%dAPDULIST=%d,Data=%s,ReturnStatus=%d" % (ret, APDULIST, Data, ReturnStatus))
        if ret != 0 or ReturnStatus != 0:
            self.__record('cpcHFClearRouteInfo.rp', u'接收异常 error code = %d' % (ret))
            raise TestItemFailException(failWeight = 10,message = u'清除路径信息失败:cpcHFClearRouteInfo,ret=%d,ReturnStatus=%d' % (ret,ReturnStatus))

    def integrateCpcWriteEntryInfo(self,psamSoftId):
        # 集成入口交易过程
        etcTrade = self
        etcTrade.activePasm(0)
        etcTrade.selectPsamDf01(0)

        etcTrade.cpcHfActive()
        cpcSysInfo = etcTrade.cpcHFReadSysInfo()
        cpcId = cpcSysInfo["cpcId"]

        etcTrade.deliverKey(psamSoftId,cpcId)
        etcTrade.cpcHFSelectDf01()
        rand = etcTrade.cpcHFGetRand()
        cpc_mac = etcTrade.psamGenerateMac(psamSoftId,rand)

        etcTrade.cpcHFexternalAuth(cpc_mac)
        etcTrade.cpcHFWriteEntryInfo("02")


    def integrateCpcClearRoutInfo(self,psamSlot,routeIndex):
        # 集成删除路径信息，入参:cpcID,PSAM卡槽号
        self.cpcHfActive()
        cpcSysInfo = self.cpcHFReadSysInfo()
        cpcId = cpcSysInfo["cpcId"]
        self.activePasm(psamSlot)
        self.selectPsamDf01(psamSlot)
        self.deliverKey(psamSlot,cpcId)
        self.cpcHFSelectDf01()
        rand = self.cpcHFGetRand()
        cpc_mac = self.psamGenerateMac(psamSlot,rand)
        self.cpcHFexternalAuth(cpc_mac)
        self.cpcHFClearRouteInfo(routeIndex)


    def integrateCpcSignRoute(self,psamSlotId,cpcId):
        # 集成标识路径
        self.activePasm(psamSlotId)
        self.selectPsamDf01(psamSlotId)
        targetMac = transCpcIdToMac(cpcId)
        self.cpc_bst_aid1(1,targetMac = targetMac)
        self.deliverKey(psamSlotId,cpcId)
        self.generatMac(psamSlotId)
        self.cpc_write_route_file_authen()
        self.endAppProc()
        return self.route_info.upper()

    def endAppProc(self):
        self.__record(u'end app', u'send')
        ret = self.reader.EVENT_REPORT(0, 1, 0)
        if ret != 0:
            self.__record(u'end app', u'数据异常 error code = %d' % (ret))
            return "end app ret not 0!\r\n"
        return None

    def cpc_write_route_file_authen(self):
        self.__record(u'cpc_write_route_file_authen.rq', u'send')
        # print "write cpc 03 file = %s,flie len = %x"%(esam04File, esam04FlieLen)
        cmdlen = "13"
        keyID = "01"
        sleepInterval = "00"
        rand = random.randint(0, 1000)
        route_info = "%04x" % rand
        APDU = cmdlen + GLOBAL["cpc_mac"] + self.route_info + sleepInterval
        print "APDU:\r\n" + APDU
        ret, DID, ChannelID, APDULIST, Data, ReturnStatus = self.reader.TransferChannel(1, 1, 0, 1, APDU)
        strLog = "cpc_write_route_file_authen.rp: ret=%d,DID=%d,ChannelID=%d,APDULIST=%d\n,Data=%s\n,ReturnStatus=%d\r\n" % \
                 (ret, DID, ChannelID, APDULIST, Data, ReturnStatus)
        uiLog(strLog)
        # if ret != 0 :raise CommandExecuteException("readIccInfo.rp ret not 0\r\n")
        if ret != 0 or ReturnStatus != 0:
            self.__record('cpc_write_route_file_authen.rq', u'接收异常 error code = %d' % ret)
            self.__record('cpc_write_route_file_authen.rp', u'ReturnStatus error code = %d' % ReturnStatus)
            return u"cpc_write_route_file.rp ReturnStatus not 0\r\n"
        self.__record('cpc_write_route_file_authen.rp', u'success')
        uiLog(strLog)
        return None

    def generatMac(self,psamSoftId ):
        lc = "10"
        # print "rand" + GLOBAL["rand"][0:16]
        # GLOBAL["rand"] = "5eaae735a2d6f322"
        print "rand:" + GLOBAL["rand"][0:16]
        # APDU = "15"+"80FA0000" + lc + GLOBAL["rand"][0:8] + "000000000000000000000000"
        APDU = "15" + "80FA0000" + lc + GLOBAL["rand"][0:16] + "000000000000000000000000"
        print "generatMac:" + APDU
        self.__record('generatMac.rq', 'send')
        ret, APDUList, Data = self.reader.PSAM_CHANNEL(psamSoftId, 1, APDU)
        strLog = "generatMac.rp: ret=%d,APDUList=%d,Data=%s\r\n" % (ret, APDUList, Data)
        uiLog(strLog)
        print Data[2:20]
        apduLength = int(Data[:2], 16)
        if Data[2:][apduLength * 2 - 4:apduLength * 2] != "9000":
            self.__record('generatMac.rp', u'psam error code =%d' % (int(Data[:2], 16)))
            return "generatMac.rp: ret code is %s\r\n" % Data[-4:]
        if ret != 0:
            self.__record('generatMac.rp', u'通信异常error code =%d' % (ret))
            return "generatMac.rp:ret not 0\r\n"
        self.__record('generatMac.rp', 'success')
        GLOBAL["cpc_mac"] = Data[2:34]
        print "cpc_mac:" + GLOBAL["cpc_mac"]

    def cpc_get_route_info(self):
        rand = random.randint(0, 1000)
        return "%04x" % rand

    def cpc_get_beacon_id(self):
        rand = random.randint(0, 1000)
        return "A600%04d" % rand

    def cpc_bst_aid1(self, tradeMode,targetMac = None):
        self.route_info = self.cpc_get_route_info()
        beaconId = self.cpc_get_beacon_id()

        Time = str(time.time())
        # Time = "00000002"
        Profile = 0
        MandApplicationlist = 1
        sysLen = "1a"
        ef01Offset = "00"
        ef01Len = "29"
        ef03Offset = "00"
        ef03Len = "07"
        if tradeMode == 0:
            bstOpt = "50"
            # MandApplication = "418729" + bstOpt + sysLen + self.route_info + ef03Offset + ef03Len
            MandApplication = "418729" + '70' + '1E' + '0010' + '0014' + '0004'  # debug 41(AID_1)  87 29 70 1E 0010 0014 0004 00
        else:
            # bstOpt = "10"
            # MandApplication = "418729"+ bstOpt + sysLen + ef03Offset + ef03Len
            bstOpt = "30"
            MandApplication = "418729" + bstOpt + sysLen + ef01Offset + ef01Len + ef03Offset + ef03Len
        Profilelist = 0
        for x in range(3):
            self.__record('cpc_bst_aid1', u'send')
            ret, ReturnStatus, Profile, Applicationlist, Application, ObuConfiguration = \
                self.reader.INITIALISATION(beaconId , Time, Profile, MandApplicationlist, MandApplication, Profilelist, 3000)
            strLog = "vst: ret=%d,ReturnStatus=%d, Profile=%d, Applicationlist=%d\n,Application=%s\n,ObuConfiguration=%s\r\n" % \
                     (ret, ReturnStatus, Profile, Applicationlist, Application, ObuConfiguration)
            uiLog(strLog)

            if ret != 0 or ReturnStatus != 0:
                self.__record('vst', u'接收异常 error code = %d,ReturnStatus=%d' % (ret,ReturnStatus))
                continue
            else:
                self.__record('vst', u'sucess')
                bst_res_map["mac"] = ObuConfiguration[0:8]

                if targetMac is not None and bst_res_map["mac"].upper() != targetMac:
                    raise TestItemFailException(10,message=u"CPC5.8G得到的MAC与CPCID不符",output={"mac":bst_res_map["mac"]})

                obuID = int(ObuConfiguration[0:2], 16)
                if obuID > 0x9F:
                    len = 0
                    pos = 2
                    GLOBAL["obu_type"] = "cpc"
                    # print "Application\r\n" + Application
                    GLOBAL["opInd"] = int(Application[0:2], 16)
                    print "opInd = %x" % GLOBAL["opInd"]
                    if (GLOBAL["opInd"] & 0x80) == 0x80:
                        print "sys:"
                        GLOBAL["sysInfoLen"] = int(Application[2:4], 16)
                        GLOBAL["sysInfo"] = Application[4:4 + GLOBAL["sysInfoLen"] * 2]
                        GLOBAL["cpcid"] = GLOBAL["sysInfo"][16:32]
                        GLOBAL["cpcarea"] = GLOBAL["sysInfo"][0:8]
                        print "sysInfoLen=%x,sysInfo:%s" % (GLOBAL["sysInfoLen"], GLOBAL["sysInfo"])
                        pos = pos + 2
                    else:
                        GLOBAL["sysInfoLen"] = 0
                    if (GLOBAL["opInd"] & 0x40) == 0x40:
                        len = GLOBAL["sysInfoLen"] * 2 + pos
                        GLOBAL["df01ef03len"] = int(Application[len:][0:2], 16)
                        GLOBAL["df01ef03"] = Application[len + 2:][0:GLOBAL["df01ef03len"] * 2]
                        print "df01ef03len=%x,df01ef03:%s" % (GLOBAL["df01ef03len"], GLOBAL["df01ef03"])
                        pos = pos + 2
                    else:
                        GLOBAL["df01ef03len"] = 0
                    if (GLOBAL["opInd"] & 0x20) == 0x20:
                        len = GLOBAL["sysInfoLen"] * 2 + GLOBAL["df01ef03len"] * 2 + pos
                        GLOBAL["df01ef01len"] = int(Application[len:][0:2], 16)
                        GLOBAL["df01ef01"] = Application[len + 2:][0:GLOBAL["df01ef01len"] * 2]
                        print "df01ef01len=%x,df01ef01:%s" % (GLOBAL["df01ef01len"], GLOBAL["df01ef01"])
                        pos = pos + 2
                    else:
                        GLOBAL["df01ef01len"] = 0
                    if (GLOBAL["opInd"] & 0x10) == 0x10:
                        len = GLOBAL["sysInfoLen"] * 2 + GLOBAL["df01ef03len"] * 2 + GLOBAL["df01ef01len"] * 2 + pos
                        GLOBAL["df01ef02len"] = int(Application[len:][0:2], 16)
                        GLOBAL["df01ef02"] = Application[len + 2:][0:GLOBAL["df01ef02len"] * 2]
                        print "df01ef02len=%x,df01ef02:%s" % (GLOBAL["df01ef02len"], GLOBAL["df01ef02"])
                        pos = pos + 2
                    else:
                        GLOBAL["df01ef02len"] = 0
                    if (GLOBAL["opInd"] & 0x08) == 0x08:
                        len = GLOBAL["sysInfoLen"] * 2 + GLOBAL["df01ef03len"] * 2 + GLOBAL["df01ef01len"] * 2 + GLOBAL[
                                                                                                                     "df01ef02len"] * 2 + pos
                        GLOBAL["rand"] = Application[len:][0:16]
                        print "rand:%s" % (GLOBAL["rand"])
                else:
                    GLOBAL["obu_type"] = "etc"
                    obuStateIcc = int(ObuConfiguration[10:12], 16)
                    if obuStateIcc & 0x80 == 0:
                        GLOBAL["write_route_file_type"] = "icc"
                    else:
                        GLOBAL["write_route_file_type"] = "esam"
                bst_res_map["contractSerial"] = Application[24:40]
                strLog = "obu mac = %s,contractSerial = %s\r\n" % (bst_res_map["mac"], bst_res_map["contractSerial"])
                uiLog(strLog)
                return bst_res_map
        return "not recv vst!"

    def updateMacThroughAI(self,mac):
        # 通过空口更新MAC
        self.__record(u'cpcWriteCpcMacID.rq', u'send')
        cmdLen = "0B"
        cmdtype = "00"
        addr = "00"
        datalen = "08"
        data = "55555555" + mac
        apduData = cmdLen + cmdtype + addr + datalen + data
        self.__record('cpcWriteCpcMacID.rq', u'send')
        ret, DID, ChannelID, APDULIST, Data, ReturnStatus = self.reader.TransferChannel(1, 1, 0x0a, 1, apduData)
        strLog = "cpcWriteCpcMacID.rp: ret=%d,DID=%d,ChannelID=%d,APDULIST=%d\n,Data=%s\n,ReturnStatus=%d\r\n" % \
                 (ret, DID, ChannelID, APDULIST, Data, ReturnStatus)
        uiLog(strLog)
        print Data
        if ret != 0 or ReturnStatus != 0:
            self.__record('cpcWriteCpcMacID.rq', u'接收异常 error code = %d,ReturnStatus=%d' % (ret,ReturnStatus))
            raise TestItemFailException(failWeight = 10,message = u'cpcWriteCpcMacID.rq异常,ret=%d,ReturnStatus=%d' % (ret,ReturnStatus))
        self.__record('cpcWriteCpcMacID.rp', u'success')

