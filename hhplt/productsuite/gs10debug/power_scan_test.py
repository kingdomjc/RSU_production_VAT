#encoding:utf-8
u'''扫描功率，反复测试并记录'''


suiteName = u'''扫描功率调试'''
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
from hhplt.testengine.autoTrigger import AutoStartStopTrigger,EmptyTrigger


TEST_TIMES = 5  #测试次数 

triggerStarted = False

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
    
    global triggerStarted
    if not triggerStarted:
        AutoStartStopTrigger().start()
        triggerStarted = True
    

def T_01_wakeupSensitivity_A(product):
    u'''唤醒灵敏度测试-高低灵敏度分别计入两个文件'''
    low_level_power = -45
    high_level_power  = -35
    grade = 0x03
    level = 0x0e

    sc = __askForPlateDeviceCom()
    for power in range(low_level_power,high_level_power+1):
        try:
            if sc.testWakenSensiWithFixedPowerAndSensi(power,grade,level):
                __saveRecordToLocalFile(u"唤醒功率.txt", str(power))
                break
        except Exception,e:
            print e
    else:
        __saveRecordToLocalFile(u"唤醒功率.txt", u'失败')
        
        
def T_02_receiveSensitivity_A(product):
    u'''接收灵敏度测试-记录灵敏度的值'''
    low_power_db = -55
    high_power_db = -45
    frame_num = SP('gs10.receiveSensitivity.frameNum',500)   #发送帧总数
    gate = 485
    
    sc = __askForPlateDeviceCom()
    for power in range(low_power_db,high_power_db+1):
        try:
            v = sc.testObuRecvSensi(power,frame_num)
            if v >= gate:
                __saveRecordToLocalFile(u"接收功率.txt", str(power))
                break
                
        except Exception,e:
            print e
    else:
        __saveRecordToLocalFile(u"接收功率.txt", u'未找到')
    
def T_03_wakeupSensitivity_A(product):
    u'''负40唤醒灵敏度动态扫功率-扫描功率并动态调整灵敏度'''
    low_level_power = -42
    high_level_power  = -35
    grade = 0x03
    start_level = 0x0e
    target_power = -40
    
    sc = __askForPlateDeviceCom()
    
    for level in range(start_level,0x00,-1):
        for power in range(low_level_power,high_level_power+1):
            try:
                if sc.testWakenSensiWithFixedPowerAndSensi(power,grade,level):
                    if power > target_power:
                        continue
                    else:
                        __saveRecordToLocalFile(u"-40功率灵敏度.txt", "%.2x\t%.2x\n"%(grade,level))
                        break
            except Exception,e:
                print e
        else:
            continue
        break
    else:
        __saveRecordToLocalFile(u"-40功率灵敏度.txt", u'失败')





