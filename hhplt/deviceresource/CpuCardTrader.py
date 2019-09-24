#encoding:utf-8
'''
Created on 2014-10-27
CPU卡交易测试设施
@author: user
'''

from hhplt.deviceresource import TestResource
from hhplt.deviceresource import AbortTestException,TestItemFailException
from hhplt.parameters import PARAM

from hhplt.deviceresource.Zxris8801 import Zxris8801,PsamCmdException,ObuCmdException,DeviceException
from hhplt.testengine.testcase import uiLog,superUiLog

import logging
def tradeDebug(msg):
    '''交易日志'''
    logging.debug(msg)


class CpuCardTrader(TestResource):
    def __init__(self,assertFailWeight = 10):
        self.assertFailWeight = assertFailWeight
        self.reader = Zxris8801()
        self.psam_res_map = {}
        self.transfer_channel_res_map = {}
    
    def initResource(self):
        '''初始化资源'''
        ret = self.reader.initResource()
        if ret > 0:
            tradeDebug("open reader success")
        else:
            tradeDebug("open reader fail " + str(ret))
        try:
            self.reader.config_device()
        except DeviceException as e:
            raise AbortTestException(message = u'发卡器初始化失败,请检查软硬件设置:'+str(e)) 
        tradeDebug("rsu info is " + self.reader.rsu_info)
        
    def retrive(self):
        '''回收资源'''
        self.reader.retrive()
    
    def testTrade(self):
        '''交易测试'''
        try:
            self.__activePsam()
            self.__read0016File()
            self.__selectDf01()
            self.__bstProc()
            self.__getSecureProc()
            self.__readIccInfo()
            self.__initPurcheAndWriteUnionFile()
            self.__chiperMac1()
            self.__debitPurche()
            self.__setMMIProc()
        except PsamCmdException,e:
            raise AbortTestException(message = u'PSAM异常，请检查软硬件设置，消息:'+e.error)
        except DeviceException,e:
            raise AbortTestException(message = u'测试设备异常，请检查软硬件设置，消息:'+e.error)
        except ObuCmdException,e:
            raise TestItemFailException(failWeight = 10,message = u'交易测试不通过，消息:'+e.error)

    def readObuId(self):
        '''读取MAC地址和合同序列号'''
        self.reader.invent_obu(3000)
        return self.reader.nowObuId.upper(),self.reader.nowContractSerial.upper()
    
    def readEsamDistrictCode(self):
        '''读取ESAM地区分散码'''
        return self.reader.districtCode.upper()
    
    def getEsamVersion(self):
        return self.reader.nowEsamVersion

    def initDf0107File(self):
        '''初始化DF01的07文件'''
        rtnList = self.reader.transfer_channel(3, "0700a4000002df010600d6870001000500b0870001",2)
        apduRtn = "".join(rtnList)
        uiLog(u"初始化DF01指令返回:"+apduRtn)
        if len(rtnList) != 3 or rtnList[2] != "009000":
            raise TestItemFailException(failWeight = 10,message=u"DF01的07文件初始化失败",output={u"返回APDU":apduRtn})
        

    def __activePsam(self):
        self.reader.active_psam(0)
        tradeDebug("active psam success!")
    
    class _PsamCmd():
        def __init__(self,cpuCardTraderSelf):
            self.cmd = ''
            self.res = ''
            self.reader = cpuCardTraderSelf.reader
            self.psam_res_map = cpuCardTraderSelf.psam_res_map
            self.transfer_channel_res_map = cpuCardTraderSelf.transfer_channel_res_map
            
        def execute(self):
            self.pre_exe()
            tradeDebug(self.__class__.__name__ + " send: " + self.cmd)
            res = self.reader.exchange_apdu(0, self.cmd)
            tradeDebug(self.__class__.__name__ + " recv: " + res)
            self.res = res[0:-4]
            if hasattr(self, "after_exe"):
                self.after_exe()

    class _SimplePsmCmd(_PsamCmd):
        def __init__(self,cpuCardTraderSelf,cmd):
            CpuCardTrader._PsamCmd.__init__(self,cpuCardTraderSelf)
#            super(self,cpuCardTraderSelf)
            self.cmd = cmd
        def pre_exe(self):
            pass
        def after_exe(self):
            print self.res

    def __read0016File(self):
        class Read0016File(CpuCardTrader._PsamCmd):
            def pre_exe(self):
                self.cmd = '00B0960006'
            def after_exe(self):
                self.psam_res_map["psam_terminal_id"] = self.res[0:12]
                print "psam_terminal_id = %s"%self.psam_res_map["psam_terminal_id"]
        Read0016File(self).execute()
    
    def __selectDf01(self):
        CpuCardTrader._SimplePsmCmd(self,"00A4000002DF0100").execute()
    
    def __bstProc(self):
        self.reader.invent_obu(3000)
        tradeDebug("bstProc success!")

    def __getSecureProc(self):
        secure_file = self.reader.get_secure()      
        tradeDebug("receive secure file: " + str(secure_file))


    class _TransferChannelProc():
        def __init__(self,cpuCardTraderSelf):
            self.reader = cpuCardTraderSelf.reader
            self.transfer_channel_res_map = cpuCardTraderSelf.transfer_channel_res_map
            self.psam_res_map = cpuCardTraderSelf.psam_res_map
            self.apdu_size = 0
            self.apdu = ''
    
        def execute(self):
            self.pre_exe()
            tradeDebug(self.__class__.__name__ + " send: " + self.apdu)
            res = self.reader.transfer_channel(self.apdu_size, self.apdu)
            tradeDebug(self.__class__.__name__ + " receive: " + str(res))
            self.res = res
            if hasattr(self, "after_exe"):
                self.after_exe()

    def __readIccInfo(self):
        class ReadIccInfo(CpuCardTrader._TransferChannelProc):
            def pre_exe(self):
                self.apdu_size = 1
                self.apdu =  "0500b095002b"
        
            def after_exe(self):
                self.transfer_channel_res_map["icc_card_sn"] = self.res[0][24:40]
                self.transfer_channel_res_map["icc_card_provider"] = (self.res[0][0:8])*2
                print "icc_card_sn = %s,icc_card_provider = %s"%(self.transfer_channel_res_map["icc_card_sn"],self.transfer_channel_res_map["icc_card_provider"])
                
        ReadIccInfo(self).execute()      
    
    def __initPurcheAndWriteUnionFile(self):
        class InitPurcheAndWriteUnionFile(CpuCardTrader._TransferChannelProc):
            def pre_exe(self):
                self.apdu_size = 2
                init_purchase_cmd = "10805003020b0100000000" + self.psam_res_map["psam_terminal_id"]
                write_union_cmd = "3080dcaac82b" + "AA290001020304050607080910111213141516171819202122232425262728293031323334353637383940"
                self.apdu = init_purchase_cmd + write_union_cmd
        
            def after_exe(self):
                self.transfer_channel_res_map["icc_random_for_mac1"] = self.res[0][22:30]
                self.transfer_channel_res_map["icc_trade_sn"] = self.res[0][8:12]
                self.transfer_channel_res_map["icc_trade_key_version"] = self.res[0][18:20]
                self.transfer_channel_res_map["icc_trade_key_id"] = self.res[0][20:22]
                
                print "icc_random_for_mac1 = %s,icc_trade_sn = %s,icc_trade_key_version = %s,icc_trade_key_id = %s"\
                        %(self.transfer_channel_res_map["icc_random_for_mac1"],self.transfer_channel_res_map["icc_trade_sn"],
                          self.transfer_channel_res_map["icc_trade_key_version"],self.transfer_channel_res_map["icc_trade_key_id"])                
        InitPurcheAndWriteUnionFile(self).execute()
   
    def __chiperMac1(self):
        class ChiperMac1(CpuCardTrader._PsamCmd):
            def pre_exe(self):
                trade_time = "20140916214018"
                debit_money = "00000000"
                self.cmd = "8070000024" + self.transfer_channel_res_map["icc_random_for_mac1"] + \
                           self.transfer_channel_res_map["icc_trade_sn"] + debit_money + "09" + \
                           trade_time + self.transfer_channel_res_map["icc_trade_key_version"] + \
                           self.transfer_channel_res_map["icc_trade_key_id"] + self.transfer_channel_res_map["icc_card_sn"] +\
                           self.transfer_channel_res_map["icc_card_provider"] + "08"
            def after_exe(self):
                self.psam_res_map["terminal_trade_sn_and_mac1_ack"] = self.res[0:16]
                print "terminal_trade_sn_and_mac1_ack = %s"%self.psam_res_map["terminal_trade_sn_and_mac1_ack"]
        ChiperMac1(self).execute()
        
    def __debitPurche(self):
        class DebitPurche(CpuCardTrader._TransferChannelProc):
            def pre_exe(self):
                trade_time = "20140916214018"
                self.apdu_size = 1
                debit_purche = "14805401000f" + self.psam_res_map["terminal_trade_sn_and_mac1_ack"][0:8] + \
                                trade_time + self.psam_res_map["terminal_trade_sn_and_mac1_ack"][8:16]
                self.apdu = debit_purche
            def after_exe(self):
                self.transfer_channel_res_map["mac2_tac"] = self.res[0][0:8]
                print "mac2_tac = %s"%self.transfer_channel_res_map["mac2_tac"]
        DebitPurche(self).execute()
    
    def __setMMIProc(self):
        secure_file = self.reader.set_mmi()  
        tradeDebug("trade success!")
