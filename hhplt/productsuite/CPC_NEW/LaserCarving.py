#encoding:utf-8
u"""镭雕
读取CPC ID并镭雕到卡面
"""
import time

from hhplt.deviceresource import DaHengLaserCarvingMachine
from hhplt.deviceresource import retrieveAllResource, askForResource
from IS13_CPCID.IS13 import IS13
from hhplt.parameters import PARAM
from hhplt.testengine.autoTrigger import AutoStartStopTrigger
from hhplt.testengine.exceptions import TestItemFailException, AbortTestException
from hhplt.testengine.manul import manulCheck, autoCloseAsynMessage,showDashboardMessage
from hhplt.testengine.server import ServerBusiness, serialCode, retrieveSerialCode
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.testutil import multipleTestCase
import CpcTraderIssuer

class IS13_Adapter():
    def __init__(self):
        self.concreteReader = IS13()

    def setTimeout(self,timeout):
        pass

    def open(self,serialPortNum):
        return self.concreteReader.open(serialPortNum)

    def RSU_Close(self):
        self.concreteReader.close()

    def PSAM_Reset(self,PSAMSlot, baud,timeout = None):
        pass

    def PSAM_CHANNEL(self,PSAMSlot, APDUList, APDU,timeout=None):
        pass

    def HFActive(self,InenetoryTimeOut, timeout=None):
        ret = self.concreteReader.hfInvent()
        tmp = ret, -1, "", 0
        return tmp

    def HFCmd(self,APDULIST,APDU, timeout=None):
        # 这款发卡器太坑爹，APDU前面不带长度。所以要检一下
        if int(APDU[:2],16) == len(APDU) / 2 - 1: APDU = APDU[2:]
        ret = self.concreteReader.hfExchangeApdu(APDU)
        Data = ret[0]
        data = Data[4:]+Data[:4]
        return 0, 1,"%.2x%s"%(len(data)/2,data) , 0

class CpcTraderIssuerExt(CpcTraderIssuer.CpcTraderIssuer):
    def __init__(self,param):
        self.dll = None
        self.reader =  IS13_Adapter()
        self.param = param

    def initResource(self):
        ret = self.reader.open(PARAM["issuerSerialPort"])
        print "RSU Open ret",ret

    def retrive(self):
        self.reader.RSU_Close()

class CpcIdSerialComplement:
    def __init__(self):
        self.serialFile = None
        self.retrivedCode = None

    def serialFileIter(self):
        with open(PARAM["cpcIdSerialName"]) as f:
            while True:
                ln = f.readline()
                if ln == "":break
                yield ln.strip()

    def fetchCpcSerialFromFile(self):
        if self.retrivedCode is not None:
            c,self.retrivedCode  = self.retrivedCode,None
            return c
        if self.serialFile is None: self.serialFile = self.serialFileIter()
        try:
            return self.serialFile.next()
        except StopIteration,e:
            print 'StopIter'
            return "FF"*8

    def retriveCode(self,code):
        self.retrivedCode = code

suiteName = u"沣雷初始化ESAM-CPC卡镭雕"
version = "1.0"
failWeightSum = 10
autoTrigger =  AutoStartStopTrigger
lastCpcId = None
COMP_SERIAL = CpcIdSerialComplement()

def __getRsu():
    return askForResource("CpcIssuerExt",CpcTraderIssuerExt)

def __getLaserCaving():
    #获得镭雕机资源
    return askForResource("DHLaserCarvingMachine",DaHengLaserCarvingMachine.DHLaserCarvingMachine)

def setup(product):
    pass

def finalFun(product):
    global lastCpcId
    if product.testResult:
        lastCpcId = product.getTestingProductIdCode()
    showDashboardMessage(u"刚刚读到的CPCID:\n%s"%product.param["targetCpcId"])

def rollback(product):
    if "\\" in PARAM["cpcIdSerialName"]:  # 如果是补卡的流程，那么补卡的CPCID要回收
        COMP_SERIAL.retriveCode(product.param["targetCpcId"])
        uiLog(u"回收待补卡的CPCID:%s" % product.param["targetCpcId"])

    try:
        rsu = __getRsu()
        psamSlotId = PARAM["psamSlotId"]
        cpcId = product.param["cpcId"]
        rsu.deliverKey(psamSlotId, cpcId)
        rsu.cpcHFSelectDf01()
        rand = rsu.cpcHFGetRand()
        cpc_mac = rsu.psamGenerateMac(psamSlotId, rand)
        rsu.cpcHFexternalAuth(cpc_mac)
        rsu.cpcHFWriteEntryInfo("02")
    except Exception, e:
        pass

def __checkTestFinished(idCode):
    # 检查产品测试已完成
    with ServerBusiness(testflow = True) as sb:
        status = sb.getProductTestStatus(productName=u"CPC卡片" ,idCode = idCode)
        if status is None:
            raise AbortTestException(message=u"该产品尚未进行交易测试，初始化ESAM-镭雕中止")
        else:
            sn1 = u"沣雷CPC路径验证及关卡"
            # sn1 = u"CPC集成出入口及路径标识测试"
            # sn2 = u"整机MAC更新"
            #
            # if sn1 not in status["suiteStatus"] and sn2 not in status["suiteStatus"]:
            #     raise AbortTestException(message=u"该产品测试未进行交易测试，请退回前续工序")
            #
            # if sn2 in status["suiteStatus"]:
            #     if status["suiteStatus"][sn2] != 'PASS': raise AbortTestException(message=u"该产品交易测试未通过，请退回前续工序")
            if sn1 in status["suiteStatus"] and status["suiteStatus"][sn1] != 'PASS':
                raise AbortTestException(message=u"该产品交易测试未通过，请退回前续工序")

def hfcardCmd(cmdHex,rsu):
    ret, APDULIST, Data, ReturnStatus = rsu.reader.HFCmd(1,cmdHex)
    if Data.endswith("9000"):return Data[2:-4]
    return Data
@multipleTestCase(times=30)
def T_01_inventoryAndReadMac_A(product):
    u"读取MAC并检查测试-读取MAC并检查该卡是否经过前续测试"
    rsu = __getRsu()
    rsu.cpcHfActive()
    cpcSysInfo = rsu.cpcHFReadSysInfo()
    cpcId = cpcSysInfo["cpcId"]
    mac = rsu.cpcReadMac()
    uiLog(u"读取到MAC:%s"%mac)
    if mac == lastCpcId: raise TestItemFailException(10, message=u"等待放置新标签")
    product.param["currentCpcId"] = cpcId
    product.param["mac"] = mac
    __checkTestFinished(mac)
    product.setTestingProductIdCode(mac)
    return cpcSysInfo

def T_02_checkBattary_A(product):
    u"电量检测-检测电量"
    rsu = __getRsu()
    rsu.cpcHFEnterMF()
    state = rsu.cpcHFReadBaseInfo()
    if state["RfpowerFlag"] != 0:
        raise TestItemFailException(failWeight = 10,message = u'卡片未断电，请检查并复测')
    if state["powerRatio"] < PARAM["powerLimit"]:
        raise TestItemFailException(failWeight = 10,message = u'卡片电量不足',output=state)

def T_03_allotCpcId_A(product):
    u"分配CPCID-分配新的CPCID"
    # 检查MAC是否已经对应过CPCID
    with ServerBusiness() as sb:
        currentCpcIdOnServer = sb.getBindingCode(productName=u"CPC卡片",idCode=product.param["mac"],bindingCodeName=u"CPCID")
    if currentCpcIdOnServer is not None and currentCpcIdOnServer!="":
        if currentCpcIdOnServer == product.param["currentCpcId"]:  # CPCID完全相同，属于复测，直接判为成功即可
            product.param["targetCpcId"] = str(currentCpcIdOnServer)
            product.param["retest"] = True
        else:
            uiLog(u"当前卡片的CPCID:%s，与数据库中记录不符，重新刷写成:%s"%(product.param["currentCpcId"],currentCpcIdOnServer))
            product.param["retest"] = False
            product.param["targetCpcId"] = str(currentCpcIdOnServer)
    else:
        uiLog(u"卡片没有刷写过CPCID，分配新的CPCID")

        # 判断是补卡流程，还是新生产流程。看cpcIdSerialName参数，如果是文件名，说明是补卡；否则是正常ID
        if "\\" not in PARAM["cpcIdSerialName"]:    #从服务端分配，正常生产
            targetCpcId = serialCode(PARAM["cpcIdSerialName"])
            if targetCpcId > PARAM["endCpcId"]: # 产量已超
                retrieveSerialCode(PARAM["cpcIdSerialName"],targetCpcId )
                raise AbortTestException(u"CPCID已超过范围，产量已完成")
        else:   #从补卡文件中获取，补卡
            targetCpcId = COMP_SERIAL.fetchCpcSerialFromFile()
            if targetCpcId == "FF"*8:   #补卡完成
                raise AbortTestException(u"补卡全部完成，本片忽略")

        uiLog(u"分配新的CPCID:%s"%targetCpcId)
        product.param["retest"] = False
        product.param["targetCpcId"] = str(targetCpcId)

def T_04_initEsam_A(product):
    u"初始化ESAM-初始化ESAM并写入CPCID"
    # product.param["targetCpcId"] = "5555000055550000"
    rsu = __getRsu()
    # if product.param["retest"]: raise AbortTestException(message=u"卡片已经过本工位测试，本次直接终止")
    all_zero = "00000000000000000000000000000000"
    issue_info = "C9CFBAA331010001"
    import esam_erease_wenxin as eew
    eew.HFCARD_COMMAND = lambda cmdHex:hfcardCmd(cmdHex,rsu)
    eew.activeEsam  = lambda :rsu.reader.HFActive(0)
    eew.cpc_update_startup(all_zero, 0, str(PARAM["issue_info"]), str(product.param["targetCpcId"]))
    sn = product.param["targetCpcId"][-8:]
    eew.update_SN(sn)
    product.addBindingCode("CPCID",product.param["targetCpcId"])
    product.addBindingCode("SN",sn)
    return {"CPCID":product.param["targetCpcId"],"SN":sn}

def T_05_assertCpcId_A(product):
    u"验证CPCID写入成功-验证CPCID是否写入成功"
    rsu = __getRsu()
    rsu.cpcHfActive()
    cpcSysInfo = rsu.cpcHFReadSysInfo()
    cpcId = cpcSysInfo["cpcId"]
    if cpcId != product.param["targetCpcId"]:
        raise TestItemFailException(failWeight=10,message=u"初始化ESAM失败，目标写入的CPCID及SN与实际不符")
    else:
        product.param["cpcId"] = cpcId

def T_06_readSn_A(product):
    u"读取SN-射频方式读取卡片SN"
    rsu = __getRsu()
    sn = rsu.cpcReadSn()
    product.param["sn"] = sn
    return {"SN":sn}

def T_07_carving_A(product):
    u"卡面镭雕-将CPC ID镭雕到卡面"
    carvingCode = product.param["cpcId"]
    # 16个字符，按4个一组加空格
    carvingCode = "%s %s %s %s"%(carvingCode[:4], carvingCode[4:8],carvingCode[8:12],carvingCode[12:])
    __getLaserCaving().toCarveCode(carvingCode)
    try:
        autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"当前镭雕号:%s,请踩下踏板进行镭雕"%carvingCode,
                                 lambda:__getLaserCaving().carved()
                                ,TestItemFailException(failWeight = 10,message = u'镭雕机未响应'))
    except TestItemFailException,e:
        __getLaserCaving().clearCarveCode()
        raise e