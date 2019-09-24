#encoding:utf-8
u'''通过下载器写入mac到此obu'''
import xlrd

suiteName = u'''分配mac到obu'''
version = "1.0"
failWeightSum = 10

from hhplt.parameters import SESSION,PARAM
from hhplt.testengine.manul import askForSomething, autoCloseAsynMessage
from hhplt.testengine.autoTrigger import AutoStartStopTrigger
from hhplt.testengine.server import ServerBusiness, serialCode
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
# from hhplt.productsuite.gs11 import overall
from hhplt.deviceresource import askForResource, CpuCardTrader, ShhicGS25Trader, DaHengLaserCarvingMachine, GS11NuLink
from hhplt.testengine.testcase import uiLog, superUiLog
from hhplt.testengine.server import serverParam as SP
from hhplt.testengine.manul import manulCheck
import time
import re
from hhplt.testengine.parallelTestSynAnnotation import serialSuite

#绑定工位的自动触发器
# autoTrigger = AutoStartStopTrigger

localRecordFile = "localdata/local_record_"+ time.strftime('%Y-%m-%d',time.localtime(time.time()))+".txt"
localRecord = {}

def __getLaserCaving():
    #获得镭雕机资源
    return askForResource("DHLaserCarvingMachine",DaHengLaserCarvingMachine.DHLaserCarvingMachine)

def __writeToLocalRecord(mac,barCode,contractSerial):
    '''写入本地记录'''
    f = open(localRecordFile,'a')
    f.write("%s,%s,%s\n"%(mac,barCode,contractSerial))
    f.close()

def __askForTrader():
    '''获得交易资源(ZXRIS 8801)'''
    sc = askForResource('ShhicGS25Trader', ShhicGS25Trader.ShhicGS25)
    return sc

def __getNuLink():
    '''获得ICP下载工具'''
    return askForResource("GS11NuLink", GS11NuLink.GS11NuLink,)


# def __checkTestFinished(idCode):
#     '''检查产品测试已完成'''
#     with ServerBusiness(testflow = True) as sb:
#         status = sb.getProductTestStatus(productName="GS11 OBU" ,idCode = idCode)
#         if status is None:
#             raise AbortTestException(message=u"该产品尚未进行单板测试，整机测试终止")
#         else:
#             sn = overall.suiteName;
#             if sn not in status["suiteStatus"] or status["suiteStatus"][sn]=='UNTESTED':
#                 raise AbortTestException(message="该产品测试[%s]项尚未完成，绑定终止"%sn)
#             if status["suiteStatus"][sn] != 'PASS':
#                 raise AbortTestException(message="该产品测试项[%s]不通过，绑定终止"%sn)
# @serialSuite
def setup(product):
    SESSION["isMend"] = False   #绑定工位不存在维修测试

# @serialSuite
def finalFun(product):
    pass

def readNember(sc):
    for i in range(5):
        try:
            mac, contractSerial = sc.readObuId()  # mac,合同序列号
            uiLog(u'测试产品标识:' + mac)
            uiLog(u'合同序列号:' + contractSerial)
            # __writeToLocalRecord(mac,product.getTestingSuiteBarCode(),contractSerial)   #记录到本地文件
            break
        except Exception, e:
            time.sleep(0.1)
    else:
        raise TestItemFailException(failWeight=10, message=u'获得合同序列号失败')
    return mac,contractSerial

def checkExcel(file_path,file_Sheet,obuNumber):
    try:
        data = xlrd.open_workbook(file_path)
        table = data.sheet_by_name(file_Sheet)
    except:
        raise AbortTestException(message=u"请检查Excel文件配置是否正确")
    col_values = table.col_values(0)
    if obuNumber not in col_values:
        raise AbortTestException(message=u"表格中无此合同序列号")
    rowIndex = col_values.index(obuNumber)
    rowvalue = table.row_values(rowIndex)
    return rowvalue[1]


def T_01_readObuId_A(product):
    u'''读取OBU内部标识-通过发卡器读取OBUID并与镭雕条码进行绑定'''
    manulCheck(u"操作提示",u"请将整机放置在发卡器上，待绿灯闪烁后确定","ok")
    sc = __askForTrader()
    mac,contractSerial = readNember(sc)
    print "mac:",mac
    print "合同序列号：",contractSerial
    newMac = checkExcel(PARAM["excelPath"].decode('utf-8'),PARAM["excelSheet"],contractSerial)
    try:
        uiLog(u"切换至NuLink模式")
        nul = __getNuLink()
        infos = nul.readInfo()
        infos00 = infos[:8] + newMac + infos[16:32]
        infos40 = infos[128:154]
        nul.writeToInfo(infos00, infos40)
    except:
        raise TestItemFailException(failWeight=10, message=u'写入新的mac失败')
    manulCheck(u"操作提示", u"请将整机放置在发卡器上，待绿灯闪烁后确定", "ok")
    for i in range(3):
        nul.resetChip()
    time.sleep(1)
    checkMac, readContractSerial = readNember(sc)
    if checkMac == newMac:
        return {u"写入新Mac":u"成功"}

# def T_03_initFactorySetting_A(product):
#     u'''出厂信息写入-写入MAC地址，唤醒灵敏度参数等，通过ICP方式写入并自动判断信息一致'''
#     #读取旧的信息内容
#     newMac = "1a1a1a1a"
#     try:
#         uiLog(u"切换至NuLink模式")
#         nul = __getNuLink()
#         infos = nul.readInfo()
#         obuid = infos[8:16]
#         print "FE00:",infos[0:32]
#         print "FE40:",infos[128:154]
#         superUiLog(u"单板信息区内容:" + infos)
#         infos00 = infos[:8] + newMac + infos[16:32]
#         infos40 = infos[128:154]
#         print infos00
#         print infos40
#         # nul.writeToInfo(infos00, infos40)
#     except TestItemFailException, e:
#         # 如果读出失败，那么也判定为需要写
#         uiLog(u"区域读取失败，开始写入出厂信息")


