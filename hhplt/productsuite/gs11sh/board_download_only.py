#encoding:utf-8
u""" 基于新的并行版本下载板的单独版本下载
"""
import time

from hhplt.parameters import SESSION, PARAM
from hhplt.productsuite.gs11sh.IntegratedVATBoard import IntegratedVatTrigger, IntegratedVATBoard
from ObuVersionDownloadBoard import VDBTrigger
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.parallelTestSynAnnotation import syntest
from hhplt.testengine.testcase import uiLog

suiteName = u"单独版本下载"
version = "1.0"
failWeightSum = 10


from version_downloader_update import __getVersionDownloadBoard

started = False

autoTrigger = VDBTrigger

@syntest
def setup(product):
    SESSION["isMend"] = True
    # return  #测试版本下载，不合夹具
    global started
    if not started:
        started = True
        __getVersionDownloadBoard().operateClap(1)
        #time.sleep(1)

finishedTestSlots = 0
@syntest
def finalFun(product):
    global finishedTestSlots
    finishedTestSlots += 1
    if finishedTestSlots  == len(PARAM["productSlots"].split(",")):
        # 所有槽位执行完
        global started
        started = False
        finishedTestSlots = 0
        __getVersionDownloadBoard().operateClap(2)


def T_01_downloadVersion_A(product):
    u"下载版本-下载VAT版本"
    vdb = __getVersionDownloadBoard()
    channel = int(product.productSlot)

    vdb.powerOn(channel,True)
    time.sleep(0.15)
    sum3Vot = 0
    for i in range(3): sum3Vot += vdb.readVoltage(channel)
    voltage = sum3Vot /3   #读3次，取平均
    current = (voltage / 4096.0 * 3.3)/8*1000 # 毫安	

    uiLog(u"槽位[%d]电流:%3f"%(channel,current))
    try:
        # 判断电压范围
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
