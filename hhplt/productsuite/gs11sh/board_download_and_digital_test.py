#encoding:utf-8
u""" 基于新的并行版本下载板的，版本下载及数字测试综合测试用例
"""
import time

from hhplt.parameters import SESSION, PARAM
from hhplt.productsuite.gs11sh.IntegratedVATBoard import IntegratedVatTrigger, IntegratedVATBoard
from ObuVersionDownloadBoard import VDBTrigger
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.parallelTestSynAnnotation import syntest
from hhplt.testengine.testcase import uiLog

suiteName = u"版本下载及单板数字测试"
version = "1.0"
failWeightSum = 10



from tj_board_digital import \
    finalFun,\
    T_06_rs232Test_A,	\
	T_07_esamTest_A as T_07_esamTest_A,	\
	T_08_capacityVoltage_A,    \
    T_09_solarVoltage_A,T_10_batteryVoltage_A,T_11_testHFChip_A,T_12_readRfCard_A,  \
    T_13_TestVst_A as T_13_TestVst_A,	\
	T_14_58Chip_A,T_15_staticCurrent_A, __allSlotToSerial

from VstChecker import getVstChecker as __getVstChecker
from IntegratedVATBoard import getIVB as __getIVB
from version_downloader_update import __getVersionDownloadBoard

started = False

#autoTrigger = VDBTrigger

@syntest
def setup(product):
    SESSION["isMend"] = True
    # return  #测试版本下载，不合夹具
    global started
    if not started:
        started = True
        # __allSlotToSerial()
        if PARAM["clapOperate"] == "I":
            if IntegratedVatTrigger.INSTANCE is None:IntegratedVatTrigger()
            IntegratedVatTrigger.INSTANCE.closeClap()
        elif PARAM["clapOperate"] == "V":
            print 'close clap'
            __getVersionDownloadBoard().operateClap(1)
        __getVstChecker().prepareToTest()
    time.sleep(0.7)

finishedTestSlots = 0
@syntest
def finalFun(product):
    global finishedTestSlots
    finishedTestSlots += 1
    try:
        __getIVB().peripheralCtrl(product.productSlot).obuPowerCtrl(0x03) # OBU下电
        __getIVB().peripheralCtrl(product.productSlot).channelSelect(0x03)
    except IntegratedVATBoard.DeviceNoResponseException,e:
        pass
    if finishedTestSlots  == len(PARAM["productSlots"].split(",")):
        # 所有槽位执行完
        global started
        started = False
        finishedTestSlots = 0
        #time.sleep(1)
        if PARAM["clapOperate"] == "I":
            IntegratedVatTrigger.INSTANCE.openClap()
        elif PARAM["clapOperate"] == "V":
            __getVersionDownloadBoard().operateClap(2)


def T_01_downloadVersion_A(product):
    u"下载版本-下载VAT版本"
    vdb = __getVersionDownloadBoard()
    channel = int(product.productSlot)

    vdb.powerOn(channel,True)
    time.sleep(0.3)
    sum3Vot = 0
    for i in range(3): sum3Vot += vdb.readVoltage(channel)
	
    voltage = sum3Vot /3   #读3次，取平均
    current = (voltage / 4096.0 * 3.3)/8*1000 # 毫安	

    uiLog(u"槽位[%d]电流:%3f"%(channel,current))

    try:
        # 判断电压范围
        # if voltage > 200: raise TestItemFailException(failWeight = 10,message = u"电流过大[%d]或者没有放置单板"%voltage)
        if current > PARAM["currentLimit"]: raise TestItemFailException(failWeight = 10,message = u"电流过大[%d]或者没有放置单板"%current)
        vdb.resetEnable(channel,True)
        vdb.dataClockEnable(channel,True)
        try:
            #vdb.reset(int(product.productSlot))
            time.sleep(0.15)
            vdb.triggerDownload(channel)
        except Exception,e:
            # 第一次下载失败，那么复位一下，重试下载
            #uiLog(u"槽位[%d]第一次版本下载失败:%s"%(channel,str(e)))
            #vdb.reset(channel)
            #time.sleep(0.5)
            #vdb.triggerDownload(channel)
            raise e
    except TestItemFailException,e:
        raise e
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u"版本下载失败:%s"%e)
    finally:
        vdb.resetEnable(channel,False)
        vdb.dataClockEnable(channel,False)
        vdb.powerOn(channel,False)


def T_02_switchToDigitalTestBoard_A(product):
    u"切换数字测试板-切换到数字测试模式"
    time.sleep(1)
    __getIVB().peripheralCtrl(product.productSlot).channelSelect(0x04)
    __getIVB().peripheralCtrl(product.productSlot).obuPowerCtrl(0x01)
    #__getVersionDownloadBoard().powerOn(int(product.productSlot),False)
    # vdb = __getVersionDownloadBoard()
    # vdb.powerOn(int(product.productSlot),True)
    time.sleep(int(product.productSlot))
    #time.sleep(1)
