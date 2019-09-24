#encoding:utf-8
u'''
更新MAC地址
重新从服务端获取顺序新的MAC地址，并通过BSL方式写入OBU
'''

suiteName = u'''更新MAC地址'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过


from hhplt.parameters import SESSION
from hhplt.testengine.autoTrigger import AutoStartStopTrigger 
from hhplt.testengine.manul import manulCheck
from hhplt.productsuite.gs10.board_digital import __askForPlateDeviceCom,__toBytesarray
from hhplt.testengine.manul import askForSomething

from hhplt.testengine.server import serialCode
from hhplt.testengine.testcase import uiLog
import time
import os
import re

autoTrigger = AutoStartStopTrigger

passwordFile = os.path.dirname(os.path.abspath(__file__))+os.sep+"versions\\obu-formal.txt"

def setup(product):
    SESSION["isMend"] = True   #补丁按维修进行

def T_02_updateMac_A(product):
    u'''更新MAC地址-获取新的MAC地址并BSL写入'''
    manulCheck(u"操作提示",u"请连接整机和工装板的U口线，然后点击确定","ok")
    if SESSION["testor"] != u"单机":
        obuid = serialCode("mac")
    else:
        obuid = ""
        while re.match("^([0-9]|[A-F]|[a-f]){8}$", obuid) is None:
            obuid = askForSomething(u"MAC地址", u"请输入MAC地址",autoCommit=False,defaultValue="24")
        
    uiLog(u"分配测试产品标识:"+obuid)
    
    sc = __askForPlateDeviceCom()
    product.setTestingProductIdCode(obuid)
    try:
        sc.startBslWriting(passwordFile)
        uiLog(u"开始写入MAC地址")
        sc.save_obu_id(__toBytesarray(obuid))
    finally:
        sc.finishBslWritten()
    time.sleep(1)
    sc.clearSerialBuffer()
    
    
    