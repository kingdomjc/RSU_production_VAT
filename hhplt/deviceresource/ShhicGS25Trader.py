#encoding:utf-8
'''
Created on 2015-9-2
基于SHHIC GS25发卡器的产线交易测试工具

@author: user
'''
from hhplt.deviceresource import TestResource,TestResourceInitException
from hhplt.deviceresource import AbortTestException,TestItemFailException
from hhplt.parameters import PARAM
import etcTradeOnGs25
from RSU import DeviceException

class ShhicGS25(TestResource):
    def __init__(self,param):
        self.assertFailWeight = 10
    
    def initResource(self):
        '''初始化资源'''
        try:
            etcTradeOnGs25.openDevice()
        except DeviceException,e:
            print e
            raise TestResourceInitException(u"SHHIC GS25发卡器初始化失败")
        
    def retrive(self):
        '''回收资源'''
        etcTradeOnGs25.closeDevice()
        
    def testTrade(self):
        '''交易测试'''
        try:
            etcTradeOnGs25.bst()
            etcTradeOnGs25.getSecureProc()
            etcTradeOnGs25.readIccInfo()
            etcTradeOnGs25.initPurcheAndWriteUnionFile()
            # etcTradeOnGs25.debitPurche()
            etcTradeOnGs25.setMMIProc()
        except etcTradeOnGs25.CommandExecuteException,e:
            raise TestItemFailException(failWeight=self.assertFailWeight,message=unicode(e))
        
    def readObuId(self):
        '''读取MAC地址和合同序列号'''
        etcTradeOnGs25.bst()
        return etcTradeOnGs25.bst_res_map["mac"],etcTradeOnGs25.bst_res_map["contractSerial"]
        
    def readEsamDistrictCode(self):
        '''读取ESAM地区分散码'''
        return etcTradeOnGs25.bst_res_map["districtCode"]
    
    def getEsamVersion(self):
        '''获得ESAM版本'''
        return etcTradeOnGs25.bst_res_map["nowEsamVersion"]
    
    def initDf0107File(self):
        '''初始化DF01的07文件'''
        ret,did,channelId,apduList,rtnValue,rtnStatus = \
            etcTradeOnGs25.reader.TransferChannel(1, 1, 2, 3, "0700a4000002df010600d6870001000500b0870001", 1000)
        print ret,did,channelId,apduList,rtnValue,rtnStatus
        if apduList !=3 or rtnStatus != 0 or rtnValue[44:50] != "009000":
            raise TestItemFailException(10,message = u"DF01的07文件初始化失败",output={u"返回APDU":rtnValue})
        
        
        