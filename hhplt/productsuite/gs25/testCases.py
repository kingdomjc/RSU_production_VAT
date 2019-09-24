#coding=utf8

import random
import time
from hhplt.deviceresource.pyDes import *
from binascii import *
from hhplt.parameters import PARAM
from hhplt.testengine.testcase import uiLog,superUiLog


from hhplt.deviceresource import askForResource,GS25Testor
GS25 = askForResource("GS25Testor", GS25Testor.GS25)

def tdes_raw(key, ori):
    k = triple_des(unhexlify(key), ECB, pad='\x00', padmode=PAD_NORMAL)
    new_ori = unhexlify(ori)
    d = k.encrypt(new_ori)
    return hexlify(d)

def single_mac(key, init, data):
    if(len(init) == 8):
        init += '00000000'
    k = des(unhexlify(key), CBC, unhexlify(init), pad="\x00", padmode = PAD_NORMAL)
    data += '80'
    d = k.encrypt(unhexlify(data))
    mac = hexlify(d)
    return mac[-16:-8]

def calc_mac1(random, tradeSn, terminalTradeSn, terminalId, tradeTime):
    dpk_01 = "EC7D409E75101DB6F17C74C557BF301E"
    rawData = random + tradeSn + terminalTradeSn[4:]
    sespk = tdes_raw(dpk_01, rawData)
    data = "00000000" + "09" + terminalId + tradeTime
    mac1 = single_mac(sespk, "00000000", data) 
    return mac1


class TestGS25_UART(object):
    def setUp(self):
        GS25.open(0,PARAM["gs25SerialPort"].encode("ascii"))
        #GS25.switchToUart()
#        GS25.open(0)

    def assertEqual(self, a, b):
        if a != b:
            raise Exception(str(a) + " not equal " + str(b))

    def test_ReadInfo(self):
        ret = GS25.rsuInit("dddddddd", 5, 40, 8, 0, 1000)
        self.assertEqual(ret['status'], 0)
        self.assertEqual(ret['rsuInfo'], PARAM["rsuInfo"]) 
#        self.assertEqual(ret['rsuInfo'], "240000010001") 

    def test_M1Card(self):   
        ret = GS25.hfInvent()
        endTime = time.time()
        for x in range(0, 4, 4):
            GS25.M1CardAuth(0x60, x, "ffffffffffff")
            GS25.M1CardWrite(x+1, "00112233445566778899aabbccddeeff")
            GS25.M1CardWrite(x+2, "00112233445566778899aabbccddeeff")
            ret = GS25.M1CardRead(x+1)
            self.assertEqual(ret, "00112233445566778899aabbccddeeff")
            ret = GS25.M1CardRead(x+2)
            self.assertEqual(ret, "00112233445566778899aabbccddeeff")
        GS25.M1CardAuth(0x60, 1, "ffffffffffff")
        GS25.M1CardWrite(1, "00000000ffffffff0000000001fe01fe")
        ret = GS25.M1CardRead(1)        
        self.assertEqual(ret, "00000000ffffffff0000000001fe01fe")
        ret = GS25.M1CardInc(1, 5)
        ret = GS25.M1CardRead(1)
        self.assertEqual(ret, "00000005fffffffa0000000501fe01fe")
        ret = GS25.hfInvent()      
        GS25.M1CardAuth(0x60, 1, "ffffffffffff")  
        ret = GS25.M1CardDec(1, 2)
        ret = GS25.M1CardRead(1)
        self.assertEqual(ret, "00000003fffffffc0000000301fe01fe")

    def tearDown(self):
        try:
            GS25.closeHf()
            GS25.close()
        except Exception,e:
            print e
            uiLog(u"系统异常:"+str(e))

class TestGS25_USB(object):
    def setUp(self):
        GS25.open(2, 0)
#        GS25.open(2, 0)

    def assertEqual(self, a, b):
        if a != b:
            raise Exception(str(a) + " not equal " + str(b))

    def test_ReadInfo(self):
        ret = GS25.rsuInit("dddddddd", 5, 40, 8, 0, 1000)
        self.assertEqual(ret['status'], 0)
        self.assertEqual(ret['rsuInfo'], PARAM["rsuInfo"])
#        self.assertEqual(ret['rsuInfo'], "240000010001")

    def test_Beep(self):
        GS25.beep()

    def test_LightRedLed(self):
        GS25.lightRedLed()

    def test_LightGreenLed(self):
        GS25.lightGreenLed()

    def test_Psam_1(self):
        GS25.resetPsam(1)
        ret = GS25.psamExchangeApdu(1, 3, "0700a40000023f000700a4000002df01050084000008")
        self.assertEqual(len(ret), 3)
        self.assertEqual(ret[0][-4:], "9000")
        self.assertEqual(ret[1][-4:], "9000")
        self.assertEqual(ret[2][-4:], "9000")

    def test_Psam_2(self):    	
        GS25.resetPsam(2)
        ret = GS25.psamExchangeApdu(2, 3, "0700a40000023f000700a4000002df01050084000008")
        self.assertEqual(len(ret), 3)
        self.assertEqual(ret[0][-4:], "9000")
        self.assertEqual(ret[1][-4:], "9000")
        self.assertEqual(ret[2][-4:], "9000")

    def test_Psam_3(self):
        GS25.resetPsam(3)
        ret = GS25.psamExchangeApdu(3, 3, "0700a40000023f000700a4000002df01050084000008")
        self.assertEqual(len(ret), 3)
        self.assertEqual(ret[0][-4:], "9000")
        self.assertEqual(ret[1][-4:], "9000")
        self.assertEqual(ret[2][-4:], "9000")

    def test_Psam_4(self):
        GS25.resetPsam(4)
        ret = GS25.psamExchangeApdu(4, 3, "0700a40000023f000700a4000002df01050084000008")
        self.assertEqual(len(ret), 3)
        self.assertEqual(ret[0][-4:], "9000")
        self.assertEqual(ret[1][-4:], "9000")
        self.assertEqual(ret[2][-4:], "9000")

    def test_icc(self):
        GS25.resetPsam(0)
        ret = GS25.psamExchangeApdu(0, 3, "0700a40000023f000700a4000002df01050084000008")
        self.assertEqual(len(ret), 3)
        self.assertEqual(ret[0][-4:], "9000")
        self.assertEqual(ret[1][-4:], "9000")
        self.assertEqual(ret[2][-4:], "9000")

    def test_EtcTradeWithPsam(self):
        psamSlot = int(PARAM["tradePsamSlot"])
        GS25.resetPsam(psamSlot)
        terminalId = GS25.psamExchangeApdu(psamSlot, 1, "0500B0960006")[0][0:12] 
        GS25.psamExchangeApdu(psamSlot, 1, "0700a4000002df01")
        GS25.inventObu()
        ret = GS25.getSecure()
        self.assertEqual(ret['length'], 32)
        ret = GS25.transferChannelIcc(1, "0500b095002b")
        iccSn = ret[0][24:40]
        iccCardProvider = ret[0][0:8]*2
        initPurchase = "10805003020b0100000000"+terminalId
        writeUnion = "3080dcaac82b"+"AA290001020304050607080910111213141516171819202122232425262728293031323334353637383940"
        ret = GS25.transferChannelIcc(2, initPurchase+writeUnion)
        randomForMac1 = ret[0][22:30]
        tradeSn = ret[0][8:12]
        keyVersion = ret[0][18:20]
        keyId = ret[0][20:22]
        tradeTime = "20140916214018"
        money = "00000000"
        calcMac1 = "298070000024"+randomForMac1+tradeSn+money+"09"+tradeTime+keyVersion+keyId+iccSn+iccCardProvider
        ret = GS25.psamExchangeApdu(psamSlot, 1, calcMac1)
        terminalTradeSn = ret[0][0:8]
        mac1 = ret[0][8:16]
        debitPurche = "14805401000f"+terminalTradeSn+tradeTime+mac1
        ret = GS25.transferChannelIcc(1, debitPurche)
        self.assertEqual(ret[0][-4:], "9000")
        GS25.setMMI()
        GS25.eventReport()

    def test_EtcTradeWithoutPsam(self):
        GS25.inventObu()
        ret = GS25.getSecure()
        self.assertEqual(ret['length'], 32)
        ret = GS25.transferChannelIcc(1, "0500b095002b")
        iccSn = ret[0][24:40]
        iccCardProvider = ret[0][0:8]*2
        terminalId = "0151000119f8"
        initPurchase = "10805003020b0100000000"+terminalId
        writeUnion = "3080dcaac82b"+"AA290001020304050607080910111213141516171819202122232425262728293031323334353637383940"
        ret = GS25.transferChannelIcc(2, initPurchase+writeUnion)
        randomForMac1 = ret[0][22:30]
        tradeSn = ret[0][8:12]
        keyVersion = ret[0][18:20]
        keyId = ret[0][20:22]
        tradeTime = "20140916214018"
        money = "00000000"
        terminalTradeSn = "00011569"        
        mac1 = calc_mac1(randomForMac1, tradeSn, terminalTradeSn, terminalId, tradeTime)
        debitPurche = "14805401000f"+terminalTradeSn+tradeTime+mac1
        ret = GS25.transferChannelIcc(1, debitPurche)
        self.assertEqual(ret[0][-4:], "9000")
        #GS25.setMMI()
        GS25.eventReport()

    def test_CpuCard(self):
        ret = GS25.hfInvent()
        ret = GS25.hfExchangeApdu(3, "0500840000080700a40000021001050084000008")
        GS25.closeHf()
        self.assertEqual(len(ret), 3)
        self.assertEqual(ret[0][-4:], "9000")
        self.assertEqual(ret[1][-4:], "9000")
        self.assertEqual(ret[2][-4:], "9000")


    def test_M1Card(self):   
        ret = GS25.hfInvent()
        for x in range(0, 4, 4):
            GS25.M1CardAuth(0x60, x, "ffffffffffff")
            GS25.M1CardWrite(x+1, "00112233445566778899aabbccddeeff")
            GS25.M1CardWrite(x+2, "00112233445566778899aabbccddeeff")
            ret = GS25.M1CardRead(x+1)
            self.assertEqual(ret, "00112233445566778899aabbccddeeff")
            ret = GS25.M1CardRead(x+2)
            self.assertEqual(ret, "00112233445566778899aabbccddeeff")
        GS25.M1CardAuth(0x60, 1, "ffffffffffff")
        GS25.M1CardWrite(1, "00000000ffffffff0000000001fe01fe")
        ret = GS25.M1CardRead(1)        
        self.assertEqual(ret, "00000000ffffffff0000000001fe01fe")
        ret = GS25.M1CardInc(1, 5)
        ret = GS25.M1CardRead(1)
        self.assertEqual(ret, "00000005fffffffa0000000501fe01fe")
        ret = GS25.hfInvent()      
        GS25.M1CardAuth(0x60, 1, "ffffffffffff")  
        ret = GS25.M1CardDec(1, 2)
        ret = GS25.M1CardRead(1)
        self.assertEqual(ret, "00000003fffffffc0000000301fe01fe")
        GS25.closeHf()

    def test_MIreadCardId(self):
        ''' card id  need change if use different card'''
        ret = GS25.MIreadCardId()
        self.assertEqual(ret, PARAM["miReadCardId"])
        GS25.closeHf()
#        self.assertEqual(ret, "04b60f00")

    def test_writeDeviceSn(self,deviceSn):
        #crid = PARAM["initCrid"]
        crid = "0001"
        print deviceSn
        print crid
        GS25.writeDeviceSn(deviceSn, crid)
        ret = GS25.readDeviceSn()
        self.assertEqual(ret[0],deviceSn)
        self.assertEqual(ret[1], crid)

    def tearDown(self):
        try:
            GS25.closeHf()
            GS25.close()
        except Exception,e:
            print e
            uiLog(u"系统异常:"+str(e))
