#encoding:utf-8
u'''OBU升级-20150513
更新版本文件并更新INFO区-MAC地址本地累加，方向键更换
'''

suiteName = u'''OBU升级-20150513'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.testengine.testcase import uiLog
from hhplt.productsuite.gs10.board_digital import __askForPlateDeviceCom
from hhplt.testengine.manul import askForSomething
from hhplt.parameters import SESSION
from hhplt.testengine.manul import manulCheck
from hhplt.testengine.autoTrigger import AutoStartStopTrigger 

import os
import time
import re

#autoTrigger = AutoStartStopTrigger

def setup(product):
    SESSION["isMend"] = True   #补丁按维修进行

def T_01_indicateVersionFile_M(product):
    u'''指定版本文件-首次运行指定版本文件'''
    if "versionFileName" not in SESSION:
        SESSION["versionFileName"] = askForSomething(u"确定版本文件", u"请输入版本文件名（只需一次）",autoCommit=False,defaultValue="obu-formal.txt")
    uiLog(u'即将下载版本文件:'+SESSION["versionFileName"])

def T_02_indicateFirstMac_M(product):
    u'''指定初始MAC地址-首次运行指定MAC地址'''
    if "localMac" not in SESSION:
        SESSION["localMac"] = askForSomething(u"确定MAC地址", u"请输入起始MAC地址（只需一次）",autoCommit=False,defaultValue="24FF0001")
    else:
        SESSION["localMac"] = "24%.6X"%(int(SESSION["localMac"][2:],16)+1)
    uiLog(u'即将写入的MAC地址:'+SESSION["localMac"])

    if "directIndicator" not in SESSION:
        SESSION["directIndicator"] = askForSomething(u"确定方向", u"请输入按键方向指示（只需一次）",autoCommit=False,defaultValue="00")
    uiLog(u'方向指示写入:'+SESSION["directIndicator"])

def T_02_downloadNewVersion_A(product):
    u'''下载新版本-自动下载新版本'''
    manulCheck(u"操作提示",u"请连接整机和工装板的U口线，然后点击确定","ok")
    sc = __askForPlateDeviceCom()
    try:
        sc.downloadVersion(version_file = os.path.dirname(os.path.abspath(__file__))+os.sep+"versions\\"+SESSION["versionFileName"])
    except Exception,e:
        raise e
    finally:
        time.sleep(1)
        sc.clearSerialBuffer()

def T_03_updateInfoFields_A(product):
    u'''更新信息区数据-更新信息区数据'''
    sc = __askForPlateDeviceCom()
    readResult = sc.read_INFO(os.path.dirname(os.path.abspath(__file__))+os.sep+"versions\\"+SESSION["versionFileName"],0x1880)
    print "old CONFIG_BUILD_INFO:"+"".join(["%.2x"%c for c in readResult])
    mac = bytearray([int(SESSION["localMac"][i]+SESSION["localMac"][i+1],16) for i in range(0,len(SESSION["localMac"]),2)])
    
    readResult[4] = mac[0]
    readResult[5] = mac[1]
    readResult[6] = mac[2]
    readResult[7] = mac[4]
    readResult[8] = int(SESSION["directIndicator"],16)
    
    CONFIG_BUILD_INFO = readResult[:24]
    
    uiLog(u"开始写入CONFIG_BUILD_INFO，值:%s"%"".join(["%.2x"%c for c in CONFIG_BUILD_INFO]))
    sc.save_CONFIG_BUILD_INFO(CONFIG_BUILD_INFO)
    
    sc.finishBslWritten()
    
    
#def T_03_saveRecordInLocal_A(product):
#    u'''记录补丁信息-本地记录本地信息'''
#    barCode = product.getTestingSuiteBarCode()
#    txt = open("updateVersionRecord.txt","a")
#    txt.write(barCode+"\r\n");
#    txt.close()
#    uiLog(u'信息已记录:'+barCode)
#    
    
