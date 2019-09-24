#encoding:utf-8
u'''
更新正式版本-20141203
用于更新已经完成测试的整机的版本
'''

suiteName = u'''正式版本更新-20141203'''
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

autoTrigger = AutoStartStopTrigger

def setup(product):
    SESSION["isMend"] = True   #补丁按维修进行

#def T_01_scanBarCode_M(product):
#    u'''扫描镭雕条码-扫描镭雕条码'''
#    barCode = askForSomething(u"扫描条码", u"请扫描镭雕条码",autoCommit=False)
#    
#    while re.match("\d{16}", barCode) is None:
#        barCode = askForSomething(u"扫描条码", u"条码扫描错误，请重新扫描",autoCommit = False)
#    uiLog(u'扫描到镭雕条码:'+barCode)
#    product.setTestingSuiteBarCode(barCode)
#    product.addBindingCode(u"镭雕条码",barCode)
#    return {u"镭雕条码":barCode}


def T_01_indicateVersionFile_M(product):
    u'''指定版本文件-首次运行指定版本文件'''
    if "versionFileName" not in SESSION:
        SESSION["versionFileName"] = askForSomething(u"确定版本文件", u"请输入版本文件名（只需一次）",autoCommit=False,defaultValue="obu-formal.txt")
    uiLog(u'即将下载版本文件:'+SESSION["versionFileName"])

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
    
#def T_03_saveRecordInLocal_A(product):
#    u'''记录补丁信息-本地记录本地信息'''
#    barCode = product.getTestingSuiteBarCode()
#    txt = open("updateVersionRecord.txt","a")
#    txt.write(barCode+"\r\n");
#    txt.close()
#    uiLog(u'信息已记录:'+barCode)
#    
    