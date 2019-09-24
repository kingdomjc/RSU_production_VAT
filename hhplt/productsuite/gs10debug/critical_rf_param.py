#encoding:utf-8
u'''关键射频参数的反复测试并记录'''


suiteName = u'''射频关键参数调试'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

import os
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.server import serverParam as SP
from hhplt.productsuite.gs10.board_digital import __askForPlateDeviceCom
from hhplt.productsuite.gs10 import board_digital
from hhplt.parameters import SESSION
from hhplt.testengine.testcase import uiLog
import time
from hhplt.testengine.autoTrigger import AutoStartStopTrigger 


TEST_TIMES = 5  #测试次数 

autoTrigger = AutoStartStopTrigger

def __saveRecordToLocalFile(filename,message):
    u'''记录补丁信息-本地记录本地信息'''
    txt = open(filename,"a")
    txt.write(message+"\r\n");
    txt.close()

def setup(product):
    SESSION["isMend"] = True
    if "debug_count" not in SESSION:
        SESSION["debug_count"] = 1
    SESSION["debug_count"] = SESSION["debug_count"]+1
    if SESSION["debug_count"] > TEST_TIMES:
        SESSION["debug_count"] = 0
        raise AbortTestException(message = u'已完成%d次测试，请检查输出文件'%TEST_TIMES)
    board_digital.setup(product)

def T_01_wakeupSensitivity_A(product):
    u'''唤醒灵敏度测试-高低灵敏度分别计入两个文件'''
    low_level_power = SP('gs10.wakeup.power.low',-40)   #低唤醒功率
    high_level_power = SP('gs10.wakeup.power.high',-42) #高唤醒功率
   
    sc = __askForPlateDeviceCom()
    try:
        lowWakenSensiResult = sc.adjustWakenSensi(low_level_power)
        __saveRecordToLocalFile(u"低灵敏度.txt", "%.2x\t%.2x"%(lowWakenSensiResult[0],lowWakenSensiResult[1]))
    except Exception,e:
        e.message = u"低灵敏度测试失败"
        __saveRecordToLocalFile(u"低灵敏度.txt", u'失败')
    try:
        highWakenSensiResult = sc.adjustWakenSensi(high_level_power)
        __saveRecordToLocalFile(u"高灵敏度.txt","%.2x\t%.2x"%(highWakenSensiResult[0],highWakenSensiResult[1]))
    except Exception,e:
        e.message = u"高灵敏度测试失败"
        __saveRecordToLocalFile(u"高灵敏度.txt", u'失败')
    
def T_02_receiveSensitivity_A(product):
    u'''接收灵敏度测试-记录灵敏度的值'''
    power_db = SP('gs10.receiveSensitivity.power',-48)
    frame_num = SP('gs10.receiveSensitivity.frameNum',500)   #发送帧总数
    try:
        sc = __askForPlateDeviceCom()
        v = sc.testObuRecvSensi(power_db,frame_num)
        uiLog(u"功率值:%d，唤醒次数:%d"%(power_db,v))
        __saveRecordToLocalFile(u"接收灵敏度.txt", str(v))
    except Exception,e:
        print e
        __saveRecordToLocalFile(u"接收灵敏度.txt", u'失败')
    finally:
        time.sleep(1)

def T_03_transmittingPower_A(product):
    u'''发射功率测试-记录发射功率的值'''
    try:
        sc = __askForPlateDeviceCom()
        v = sc.getObuSendPower()
        __saveRecordToLocalFile(u"功率.txt", str(v))
    except Exception,e:
        print e
    
    
    
    
