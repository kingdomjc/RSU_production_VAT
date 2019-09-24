#encoding:utf-8
u'''
并行版本下载
并行版本下载
'''

suiteName = u'''并行版本下载'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.testengine.exceptions import TestItemFailException
from hhplt.deviceresource import askForResource,GS10PlateDevice
from hhplt.testengine.testcase import uiLog
from hhplt.parameters import SESSION,PARAM
from hhplt.testengine.manul import askForSomething

from threading import Event,Lock
 
import thread
import os
import time

#autoTrigger = AutoStartStopTrigger

def __askForPlateDeviceCom(comName):
    sc = askForResource('GS10PlateDevice_'+comName, GS10PlateDevice.GS10PlateDevice,
               serialPortName = comName,
               cableComsuption = PARAM["cableComsuption"])
    return sc

class CountDownLatch:
    def __init__(self,count):
        self.count = count
        self.lock = Event()
        self.selfLock = Lock()
    
    def waitForCountOver(self):
        self.lock.wait()
    
    def release(self):
        self.selfLock.acquire()
        self.count = self.count - 1
        self.selfLock.release()
        print '-----------lock count:%d'%self.count
        if self.count == 0:
            self.lock.set()


def setup(product):
    SESSION["isMend"] = True   #补丁按维修进行
    

msg = ""

def __versionDownloadThread(comName,lock):
    sc = __askForPlateDeviceCom(comName)
    try:
        sc.downloadVersion(version_file = os.path.dirname(os.path.abspath(__file__))+os.sep+"versions\\"+SESSION["versionFileName"])
        uiLog(u'%s下载完成'%comName)
    except Exception,e:
        global msg
        msg = "%s,%s下载失败:%s"%(msg,comName,e.message)
        uiLog(u'%s下载失败'%comName)
    finally:
        time.sleep(1)
        sc.clearSerialBuffer()
        lock.release()

def T_01_indicateVersionFile_M(product):
    u'''指定版本文件-首次运行指定版本文件'''
    if "versionFileName" not in SESSION:
        SESSION["versionFileName"] = askForSomething(u"确定版本文件", u"请输入版本文件名（只需一次）",autoCommit=False,defaultValue="obu-formal.txt")
    uiLog(u'即将下载版本文件:'+SESSION["versionFileName"])


def T_02_downloadNewVersion_A(product):
    u'''下载新版本-自动下载新版本'''
    global msg
    msg = ""
    comList = PARAM["parallelComList"].split(",")
    lock = CountDownLatch(len(comList))
    for com in comList:
        thread.start_new_thread(__versionDownloadThread,(com,lock))
    time.sleep(1)
    lock.waitForCountOver()
    if msg!="":
        raise TestItemFailException(failWeight = 10,message = msg) 
    
    
    
    