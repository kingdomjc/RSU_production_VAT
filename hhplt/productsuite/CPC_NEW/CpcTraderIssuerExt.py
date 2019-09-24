#encoding:utf-8
u"""
模块: 沣雷CPC卡测试发卡器
"""
from hhplt.parameters import PARAM
from IS13_CPCID.IS13 import IS13
from hhplt.testengine.exceptions import AbortTestException, TestItemFailException
from hhplt.testengine.testcase import uiLog
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
        self.concreteReader.resetPsam(PSAMSlot, 1)
        return 0, -1, ""

    def HFCloseRF(self):
        # 关闭13.56
        self.concreteReader.hfclose()

    def PSAM_CHANNEL(self,PSAMSlot, APDUList, APDU,timeout=None):
        if int(APDU[:2], 16) == len(APDU) / 2 - 1: APDU = APDU[2:]
        ret = self.concreteReader.psamIS13ExchangeApdu(PSAMSlot, 1, 0, APDU)
        data = ret[0]
        return 0, -1, "%.2x%s"%(len(data)/2,data)

    def HFActive(self,InenetoryTimeOut, timeout=None):
        self.concreteReader.hfInvent()
        return 0,-1,"",0

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