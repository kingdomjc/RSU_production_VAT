#encoding:utf-8
u"整机测试，在整机环境下重做数字测试项。整机正常放置在夹具上，按下开始按钮进行测试"

suiteName = u'''整机测试'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

import board_digital
from hhplt.testengine.server import serverParam as SP
from hhplt.parameters import SESSION
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.manul import manulCheck,askForSomething,autoCloseAsynMessage
from hhplt.testengine.testcase import uiLog,superUiLog
from hhplt.testengine.server import ServerBusiness
from hhplt.testengine.versionContainer import getVersionFile
import time

import board

def __checkBoardFinished(idCode):
    '''检查单板(数字、射频）工位已完成'''
    with ServerBusiness(testflow = True) as sb:
        status = sb.getProductTestStatus(productName="GS11 OBU" ,idCode = idCode)
        if status is None:
            raise AbortTestException(message=u"该产品尚未进行单板测试，整机测试终止")
        else:
            sn1 = board.suiteName
            if sn1 not in status["suiteStatus"] or status["suiteStatus"][sn1] != 'PASS':
                raise AbortTestException(message=u"该产品的单板测试项未进行或未通过，整机测试终止")
            
def __switchToNulink():
    board_digital.__askForPlateDeviceCom().bslDevice.serial.setRTS(True)
    uiLog(u"切换至NuLink模式")
    time.sleep(1)

def __switchToNormalSerial():
    board_digital.__askForPlateDeviceCom().bslDevice.serial.setRTS(False)
    uiLog(u"切换至普通串口模式")
    time.sleep(1)
            
def T_01_readObuId_A(product):
    u"读取OBU内部标识-通过ICP方式读取OBU的内部标识"
    nul = board.__getNuLink()
    try:
        __switchToNulink()
        infos = nul.readInfo()
        superUiLog(u"信息区"+infos)
        currentSoftVersion = infos[18:26]
        vf = SP("gs11.vatVersion.filename","GS11-VAT-09.00.00.version",str)
        targetVatSoftwareVersion = "".join(vf.split("-")[2].split(".")[:3])+"00"
        if currentSoftVersion != targetVatSoftwareVersion:
            uiLog(u"整机内非测试版本，下载测试版本:"+vf)
            #下载测试版本
            vf = getVersionFile(SP("gs11.vatVersion.filename","GS11-VAT-09.00.00.version",str))
            nul.downloadVersion(vf)
            #写入测试版本号
            CONFIG_BUILD_INFO = infos[:32]
            CONFIG_RF_PARA = infos[128:154]
            CONFIG_BUILD_INFO = CONFIG_BUILD_INFO[:18] + targetVatSoftwareVersion + CONFIG_BUILD_INFO[26:]
            nul.writeToInfo(CONFIG_BUILD_INFO,CONFIG_RF_PARA)
    except Exception,e:
        print e
        raise AbortTestException(u"无法读取内部标识及版本号")
    finally:
        nul.resetChip()
        __switchToNormalSerial()
    if not infos.startswith("55555555"):
        raise AbortTestException(u"单板未经过测试，请退回到单板测试工位")
    mac = infos[8:16]
    uiLog(u"读取到测试产品标识:"+mac)
    product.setTestingProductIdCode(mac)
    if not SESSION["isMend"]:__checkBoardFinished(mac)
    return {"OBUID":mac}

def T_02_rs232Test_A(product):
    u'''RS232测试-自动判断RS232应答返回是否正确'''
    time.sleep(1)
    return board_digital.T_03_rs232Test_A(product)

def T_03_capacityVoltage_A(product):
    u'''电容电路电压测试-根据电容电路电压值判断是否满足要求'''
    sc = board_digital.__askForPlateDeviceCom()
    r = sc.assertAndGetNumberParam(request='TestCapPower',response="TestCapPower")
    result = {"电容电路电压":r}
    if r < SP('gs11.capPower.overall.low',3300) or r > SP('gs11.capPower.overall.high',3800):
        raise TestItemFailException(failWeight = 10,message = u'电容电压异常',output=result)
    return result    
    
def T_04_solarVoltage_A(product):
    u'''太阳能电路电压测试-判断太阳能电路电压是否满足要求'''
    sc = board_digital.__askForPlateDeviceCom()
    r = sc.assertAndGetNumberParam(request='TestSolarPower',response="TestSolarPower")
    result = {"太阳能电路电压":r}
    if r < SP('gs11.solarBatteryPower.overall.low',3400) or r > SP('gs11.solarBatteryPower.overall.high',3900):
        raise TestItemFailException(failWeight = 10,message = u'太阳能电路电压异常',output=result)
    return result
    
def T_05_batteryVoltage_A(product):
    u'''电池电路电压测试-判断电池电路电压是否满足要求'''
    sc = board_digital.__askForPlateDeviceCom()
    r = sc.assertAndGetNumberParam(request='TestBattPower',response="TestBattPower")
    result = {"电池电路电压":r}
    if r < SP('gs10.batteryPower.overall.low',3300) or r > SP('gs10.batteryPower.overall.high',4000):
        raise TestItemFailException(failWeight = 10,message = u'电池电路电压异常',output=result)
    return result

def T_06_esam_A(product):
    u'''ESAM测试-判断地区分散码是否正确'''
    return board_digital.T_08_esam_A(product)

def T_07_redLight_M(product):
    u'''红色LED灯检测-自动判定红LED灯是否正常亮起'''
    sc = board_digital.__askForPlateDeviceCom()
    sc.asynSend("TestRedLedPara 1000")
    mcr = manulCheck(u"声光指示测试", u"请确认红色指示灯显示是否正常。")
    sc.asynReceiveAndAssert("TestRedLedParaOK")
    if not mcr:raise TestItemFailException(failWeight = 10,message = u'红色指示灯测试人工判断不通过！')

def T_08_greenLight_M(product):
    u'''绿色LED灯检测-自动判定绿LED灯是否正常亮起'''
    sc = board_digital.__askForPlateDeviceCom()
    sc.asynSend("TestGreenLedPara 1000")
    mcr = manulCheck(u"声光指示测试", u"请确认绿色指示灯显示是否正常。")
    sc.asynReceiveAndAssert("TestGreenLedParaOK")
    if not mcr:raise TestItemFailException(failWeight = 10,message = u'绿色指示灯测试人工判断不通过！')

def T_09_beep_M(product):
    u'''蜂鸣器检测-自动判定蜂鸣器是否响起'''
    sc = board_digital.__askForPlateDeviceCom()
    sc.asynSend("TestBeepPara 1000")
    mcr = manulCheck(u"声光指示测试", u"请确认蜂鸣器响声正常。")
    sc.asynReceiveAndAssert("TestBeepParaOK")
    if not mcr:raise TestItemFailException(failWeight = 10,message = u'蜂鸣器测试人工判断不通过！')
    
def T_10_oled_M(product):
    u'''OLED屏幕测试-自动判断OLED屏幕是否全黑'''
    sc = board_digital.__askForPlateDeviceCom()
    sc.asynSend("TestOLED")
    mcr = manulCheck(u"OLED测试", u"请确认OLED屏幕显示全黑。")
    sc.asynReceiveAndAssert("TestOLEDOK")
    if not mcr:raise TestItemFailException(failWeight = 10,message = u'OLED屏幕测试人工判断不通过！')

def T_12_formalVersionDownload_A(product):
    u'''正式版本下载-下载正式版本'''
    vf = getVersionFile(SP("gs11.formalVersion.filename","GS11-FORMAL_CHONGQING-01.00.00.version",str))
    uiLog(u"版本文件:"+vf)
    try:
        __switchToNulink()
        nul = board.__getNuLink()
        oriData = nul.readInfo()
        softwareVersion = "".join(vf.split("-")[2].split(".")[:3])+"00"
        uiLog(u"开始写入软件版本号:"+softwareVersion)
        CONFIG_BUILD_INFO = oriData[:32]
        CONFIG_RF_PARA = oriData[128:154]
        CONFIG_BUILD_INFO = CONFIG_BUILD_INFO[:18] + softwareVersion + CONFIG_BUILD_INFO[26:]
        nul.writeToInfo(CONFIG_BUILD_INFO,CONFIG_RF_PARA)
        uiLog(u"开始下载正式版本")
        nul.downloadVersion(vf)
        nul.resetChip()
    finally:
        __switchToNormalSerial()
        
def T_11_disassemblePowerOff_A(product):
    u'''防拆下电测试-松开防拆开关，检查OBU已经下电'''
    return board_digital.T_14_disassemblePowerOff_M(product)
    
