#encoding:utf-8
u" 不完整的单板数字测试\n并行测试6个单板数字功能，基于新的集成工装板，测试项目不完整"
import time

from hhplt.deviceresource import askForResource
from hhplt.parameters import PARAM, SESSION
from hhplt.productsuite.gs11sh.IntegratedVATBoard import IntegratedVATBoard, IntegratedVatTrigger
from hhplt.testengine.exceptions import AbortTestException, TestItemFailException
from hhplt.testengine.parallelTestSynAnnotation import syntest, serialSuite
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.server import serverParam as SP
from hhplt.testengine.versionContainer import getVersionFile
from hhplt.testengine.testutil import multipleTestCase

suiteName = u"单板数字测试"
version = "1.0"
failWeightSum = 10



from hhplt.deviceresource.GS11SHVatSuite import GS11NuLink



from IntegratedVATBoard import getIVB as __getIVB
from VstChecker import getVstChecker as __getVstChecker

def __stateAtNLK(product):
    # 转入NuLink模式，用于读写Flash及下载版本
    if "channelState" not in product.param or product.param["channelState"] != 0x01:
        try:
            __getIVB().peripheralCtrl(product.productSlot).channelSelect(0x01)
            product.param["channelState"] = 0x01
        except IntegratedVATBoard.DeviceNoResponseException,e:
            raise AbortTestException(message = u'工装板通信失败，无法继续测试')

def __stateAtSerial(product):
    # 转入串口模式，用于测试
    return
    # if "channelState" not in product.param or product.param["channelState"] != 0x02:
    #    __getIVB().peripheralCtrl(product.productSlot).channelSelect(0x02)
    #    product.param["channelState"] = 0x02
    #    time.sleep(0.7)


def __allSlotToSerial():
    for slot in PARAM["productSlots"].split(","):
        __getIVB().peripheralCtrl(slot).channelSelect(0x02)

# autoTrigger = IntegratedVatTrigger

######################################################################

started = False

@syntest
#@serialSuite
def setup(product):
    SESSION["isMend"] = True
    #OBU上电
    global started
    if not started:
        started = True
        if IntegratedVatTrigger.INSTANCE is None:IntegratedVatTrigger()
        __allSlotToSerial()
        IntegratedVatTrigger.INSTANCE.closeClap()
        __getVstChecker().prepareToTest()
    __getIVB().peripheralCtrl(product.productSlot).obuPowerCtrl(0x01)
    time.sleep(0.7)


finishedTestSlots = 0

from threading import RLock
vstLock = RLock()


@syntest
#@serialSuite
def finalFun(product):
    global finishedTestSlots
    finishedTestSlots += 1
    # OBU下电
    try:
        #__getIVB().peripheralCtrl(product.productSlot).obuPowerCtrl(0x03)
        __getIVB().peripheralCtrl(product.productSlot).obuPowerCtrl(0x03)
    except IntegratedVATBoard.DeviceNoResponseException,e:
        pass
    if finishedTestSlots  == len(PARAM["productSlots"].split(",")):
        # 所有槽位执行完
        global started
        started = False
        finishedTestSlots = 0
        IntegratedVatTrigger.INSTANCE.openClap()
        


#引入版本下载
#from tj_board_downloadversion import T_01_initCfg_A,T_04_writeInfo_A,T_05_downloadVatVersion_A


def T_06_rs232Test_A(product):
    u"RS232测试-测试OBU串口工作是否正常"
    try:
        __stateAtSerial(product)
        __getIVB().obuTest(product.productSlot).TestUART()
    except IntegratedVATBoard.DeviceNoResponseException,e:
        raise AbortTestException(message = u'工装板通信失败，无法继续测试')
    except IntegratedVATBoard.ObuNoResponseException,e2:
        raise TestItemFailException(failWeight = 10,message = u'RS232检测不通过:%s'%e2.msg)
    

def T_07_esamTest_A(product):
    u"ESAM测试-测试ESAM工作是否正常"
    try:
        __stateAtSerial(product)
        esam = __getIVB().obuTest(product.productSlot).TestESAM()
        esamId = esam[22:30]
        #check esam district code

        if PARAM["esamType"] == '1':tdc = u"重庆"
        elif PARAM["esamType"] == '2':tdc = u"贵州"
        else:tdc = PARAM["esamType"]
        	
        targetDistrictCode = tdc.decode().encode("gbk").encode("hex").upper()
        if targetDistrictCode not in esam:
            raise AbortTestException(message = u'ESAM类型不正确，应使用%s的ESAM'%tdc)
        return {"ESAM":esam,"ESAMID":esamId}
    except IntegratedVATBoard.DeviceNoResponseException,e:
        raise AbortTestException(message = u'工装板通信失败，无法继续测试')
    except IntegratedVATBoard.ObuNoResponseException,e2:
        raise TestItemFailException(failWeight = 10,message = u'ESAM检测不通过:%s'%e2.msg)
    

def T_08_capacityVoltage_A(product):
    u"电容电路电压测试-读取电容电路电压值，并判断是否在阈值内"
    try:
        __stateAtSerial(product)
        r = __getIVB().obuTest(product.productSlot).TestCapPower()
        cl,ch = SP('gs11.capPower.board.low',3030),SP('gs11.capPower.board.high',3250)
        if r < cl or r > ch:
            raise TestItemFailException(failWeight = 10,message = u'电容电压测试不通过,值:%d,正常阈值%d-%d'%(r,cl,ch),output={u"电容电路电压":r})
        return {u"电容电路电压":r}
    except IntegratedVATBoard.DeviceNoResponseException,e:
        raise AbortTestException(message = u'工装板通信失败，无法继续测试')
    except IntegratedVATBoard.ObuNoResponseException,e2:
        raise TestItemFailException(failWeight = 10,message = u'电容电压测试不通过:%s'%e2.msg)

def T_09_solarVoltage_A(product):
    u"太阳能电路电压测试-读取太阳能电路电压值，并判断是否在阈值内"
    try:
        __stateAtSerial(product)
        r = __getIVB().obuTest(product.productSlot).TestSolarPower()
        sl,sh = SP('gs11.solarBatteryPower.board.low',1200),SP('gs11.solarBatteryPower.board.high',2550)
        if r < sl or r > sh:
            raise TestItemFailException(failWeight = 10,message = u'太阳能电路电压测试不通过,值:%d,正常阈值%d-%d'%(r,sl,sh),output={u"太阳能电路电压":r})
        return {u"太阳能电路电压":r}
    except IntegratedVATBoard.DeviceNoResponseException,e:
        raise AbortTestException(message = u'工装板通信失败，无法继续测试')
    except IntegratedVATBoard.ObuNoResponseException,e2:
        raise TestItemFailException(failWeight = 10,message = u'太阳能电压测试不通过:%s'%e2.msg)

def T_10_batteryVoltage_A(product):
    u"电池电路电压测试-读取电池电路电压值，并判断是否在阈值内"
    try:
        __stateAtSerial(product)
        r = __getIVB().obuTest(product.productSlot).TestBattPower()
        sl,sh =  SP('gs11.batteryPower.board.low',3350),SP('gs11.batteryPower.board.high',3480)
        if r < sl or r > sh:
            raise TestItemFailException(failWeight = 10,message = u'电池电路电压测试不通过,值:%d,正常阈值%d-%d'%(r,sl,sh),output={u"电池电路电压":r})
        return {u"电池电路电压":r}
    except IntegratedVATBoard.DeviceNoResponseException,e:
        raise AbortTestException(message = u'工装板通信失败，无法继续测试')
    except IntegratedVATBoard.ObuNoResponseException,e2:
        raise TestItemFailException(failWeight = 10,message = u'电池电压测试不通过:%s'%e2.msg)

def T_11_testHFChip_A(product):
    u"测试高频芯片-测试高频芯片"
    global vstLock
    try:
        vstLock.acquire()
        __stateAtSerial(product)
        __getIVB().obuTest(product.productSlot).TestHFChip()
    except IntegratedVATBoard.DeviceNoResponseException,e:
        raise AbortTestException(message = u'工装板通信失败，无法继续测试')
    except IntegratedVATBoard.ObuNoResponseException,e2:
        raise TestItemFailException(failWeight = 10,message = u'高频芯片检测不通过:%s'%e2.msg)
    finally:
        vstLock.release()

def T_12_readRfCard_A(product):
    u"高频读卡测试-测试高频读卡是否正常"
    testTimes = SP('gs11.testHf.number',5,int)   #测试次数
    global vstLock
    try:
        vstLock.acquire()
        __stateAtSerial(product)
        failTimes = __getIVB().obuTest(product.productSlot).TestHF(testTimes)
        if failTimes !=0:
            raise TestItemFailException(failWeight = 10,message = u'高频芯片读卡失败%d次'%failTimes)
    except IntegratedVATBoard.DeviceNoResponseException,e:
        raise AbortTestException(message = u'工装板通信失败，无法继续测试')
    except IntegratedVATBoard.ObuNoResponseException,e2:
        raise TestItemFailException(failWeight = 10,message = u'高频读卡检测不通过:%s'%e2.msg)
    finally:
        vstLock.release()


#@syntest
#@multipleTestCase(times=3)

def T_13_TestVst_A(product):
    u"VST发送验证-控制OBU发送VST并使用监听确认"
    eee = None
    global vstLock	
    vstLock.acquire()
    try:
        for times in range(5):
            try:
                return _T_13_TestVst_A(product)
            except Exception,e:
                eee = e
                time.sleep(1)
    finally:
	    vstLock.release()
    raise eee
        


def _T_13_TestVst_A(product):
    u"VST发送验证-控制OBU发送VST并使用监听确认"
    testTimes = 5
    try:
        __stateAtSerial(product)
        __getIVB().obuTest(product.productSlot).TestSendVst()
        if not __getVstChecker().checkRecv(product.productSlot,testTimes):
            raise TestItemFailException(failWeight = 10,message = u'VST测试不通过:未监听到VST')
    except IntegratedVATBoard.DeviceNoResponseException,e:
        raise AbortTestException(message = u'工装板通信失败，无法继续测试')
    except IntegratedVATBoard.ObuNoResponseException,e2:
        raise TestItemFailException(failWeight = 10,message = u'VST测试不通过:%s'%e2.msg)
    finally:
        pass
		

def T_14_58Chip_A(product):
    u"5.8G芯片测试-测试5.8G芯片工作是否正常"
    try:
        __stateAtSerial(product)
        __getIVB().obuTest(product.productSlot).Test5_8G()
    except IntegratedVATBoard.DeviceNoResponseException,e:
        raise AbortTestException(message = u'工装板通信失败，无法继续测试')
    except IntegratedVATBoard.ObuNoResponseException,e2:
        raise TestItemFailException(failWeight = 10,message = u'5.8G芯片检测不通过:%s'%e2.msg)

#staticCurrentRLock = RLock()

def T_15_staticCurrent_A(product):
    u"静态电流测试-读取静态电流值，并判断是否在阈值范围内"
    try:
        #staticCurrentRLock.acquire()
        __stateAtSerial(product)
        __getIVB().obuTest(product.productSlot).OBUEnterSleep()		
        __getIVB().peripheralCtrl(product.productSlot).channelSelect(0x03)
        __getIVB().peripheralCtrl(product.productSlot).obuPowerCtrl(0x02)
        uiLog(u"切换到休眠状态，关闭串口")
        time.sleep(0.5)

        vtg = __getIVB().peripheralCtrl(product.productSlot).readObuCurrentVoltage(100)
        #staticCurrent = (vtg*100)/14.99/1000.0
        staticCurrent  =(vtg/1000.0)/166375.0
        resultMap = {u"静态电流":staticCurrent }
        sl,sh = SP('gs11.staticCurrent.low',0),SP('gs11.staticCurrent.high',12e-6)
        if staticCurrent  < sl or staticCurrent  > sh:
            raise TestItemFailException(failWeight = 10,message = u'静态电流测试不通过,值:%.2e，正常阈值%.2e-%.2e'%(staticCurrent,sl,sh),output=resultMap)
        return resultMap
    except IntegratedVATBoard.DeviceNoResponseException,e:
        raise AbortTestException(message = u'工装板通信失败，无法继续测试')
    except IntegratedVATBoard.ObuNoResponseException,e2:
        raise TestItemFailException(failWeight = 10,message = u'OBU进入休眠无响应:%s'%e2.msg)
 #   finally:
 #       staticCurrentRLock.release()




