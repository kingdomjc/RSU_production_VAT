#encoding:utf-8
u'''单板数字工位测试项'''


suiteName = u'''单板数字工位测试项'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

import os,time

from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.server import serialCode,serverParam as SP,ServerBusiness
from hhplt.deviceresource import askForResource,GS10PlateDevice
from hhplt.testengine.manul import manulCheck,askForSomething,autoCloseAsynMessage
from hhplt.parameters import PARAM,SESSION
from hhplt.testengine.testcase import uiLog,superUiLog
import re

versionFile = os.path.dirname(os.path.abspath(__file__))+os.sep+"versions\\obu-vat.txt"

def __checkBarCode(barCode):
    '''条码校验'''
    #旧编码规则
    if re.match("91000010[0-9]{3}",barCode) != None:
        return True
    elif re.match("\d{14}",barCode) != None:
        return True
    return False

def __getDistrictCodeFromBarCode(barCode):
    '''从条码获取ESAM地区分散码，当前只有重庆（50）'''
    pfx = SP("gs10.boardBarPrefix","50",str)
    disCode = SP("gs10.esamDistrictCode."+pfx,"D6D8C7EC",str)
    if len(barCode) == 12:
        return "D6D8C7EC"   #为兼容12位单板条码，后续都改为14位了
    if barCode.startswith(pfx):
        return disCode
    else:
        raise AbortTestException(message = u"单板条码与ESAM地区分散码不匹配，测试终止")

def __toBytesarray(hexStr):
    '''从HEX符号转换成bytearray'''
    return bytearray([int(hexStr[i]+hexStr[i+1],16) for i in range(0,len(hexStr),2)])

def __askForPlateDeviceCom():
    '''获得工装板资源'''
    sc = askForResource('GS10PlateDevice', GS10PlateDevice.GS10PlateDevice,
               serialPortName = PARAM["gs10PlateDeviceCom"],
               cableComsuption = PARAM["cableComsuption"])
    return sc


def __deprecated_readAndAssertWorkingCurrent():
    '''老工装板的读取工作电流的逻辑，新工装板判定在前台，此函数废止'''
    sc = __askForPlateDeviceCom()
    try:
        workingCurrent = sc.getPlateWorkingCurrent()
    except:
        raise AbortTestException(message = u'读取上电电流失败，测试终止')
    if workingCurrent > 1000:
        uiLog(u'读取到工作电流:%d'%workingCurrent)
        raise AbortTestException(message = u'上电电流过大，请立即抬起夹具，测试终止。')
    else:
        uiLog(u'读取到工作电流:%d'%workingCurrent)


def __readOldMac():
    '''读取旧MAC地址'''
    sc = __askForPlateDeviceCom()
    try:
        superUiLog(u"BSL方式尝试读取旧MAC地址")
        macBytes = sc.read_obu_id(versionFile)
        mac = "".join(["%.2X"%i for i in macBytes])
        superUiLog(u"尝试读取旧MAC地址结果:%s"%mac)
        return mac
    except Exception,e:
        raise AbortTestException(message = u'BSL方式读取产品标识失败:'+e.message)
    finally:
        time.sleep(1)
        sc.clearSerialBuffer()

def __checkAndPersistEsamId(idCode,esamId):
    '''检查并立即持久ESAMID的绑定关系'''
    if idCode is None:
        return
    with ServerBusiness(testflow = True) as sb:
        if not sb.checkAndPersistUniqueBindingCode(productName="GS10 OBU" , idCode=idCode , 
                                                   bindingCodeName=u"ESAMID" , code = esamId):
            raise TestItemFailException(failWeight = 10,message = u'ESAMID重复',output={"ESAMID":esamId})  
        uiLog(u"ESAMID重复检查通过")
        
def __unbindEsam(idCode):
    '''解除绑定关系'''
    with ServerBusiness() as sb:
        sb.unbindCode(productName="GS10 OBU",idCode=idCode,bindingCodeName="ESAMID")

def setup(product):
    '''检查工装板电流，如果范围不对，终止测试'''
    #__deprecated_readAndAssertWorkingCurrent()
    sc = __askForPlateDeviceCom()
    r = sc.sendAndGet("PowerOnObu")
    if r == 'PowerOnObuFail':
        raise AbortTestException(message = u'上电电流过大，请立即抬起夹具，测试终止。')
    #老工装板，上面注释掉
    time.sleep(1)
    
def finalFun(product):
    '''收尾函数，给OBU下电'''
    sc = __askForPlateDeviceCom()
    sc.asynSend("PowerOffObu")

def rollback(product):    
    #如果测试失败，要解绑定ESAM关系
    if product.getTestingProductIdCode() is not None and SESSION["testor"] != u"单机":
        __unbindEsam(product.getTestingProductIdCode())
        uiLog(u'解除ESAM绑定关系')


def T_03_rs232Test_A(product):
    u'''RS232测试-自动判断RS232应答返回是否正确'''
    sc = __askForPlateDeviceCom()
    sc.assertSynComm(request ='TestUART',response = 'TestUartOK')

def T_04_reset_M(product):
    u'''复位测试-单板上电后返回数据，系统自动判断是否正确'''
    sc = __askForPlateDeviceCom()
    autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"请按下夹具正面的按钮，以复位被测设备",
                         lambda:sc.assertSynComm(request ='TestReset',response = 'PowerOnSuccess'))
    time.sleep(0.5)

def T_05_capacityVoltage_A(product):
    u'''电容电路电压测试-根据电容电路电压值判断是否满足要求'''
    sc = __askForPlateDeviceCom()
    r = sc.assertAndGetNumberParam(request='TestCapPower',response="TestCapPower")
    result = {"电容电路电压":r}
    if r < SP('gs10.capPower.low',2800) or r > SP('gs10.capPower.high',3500):
        raise TestItemFailException(failWeight = 10,message = u'电容电压异常，正常阈值2800-3500',output=result)
    return result

def T_06_solarVoltage_A(product):
    u'''太阳能电路电压测试-判断太阳能电路电压是否满足要求'''
    sc = __askForPlateDeviceCom()
    r = sc.assertAndGetNumberParam(request='TestSolarPower',response="TestSolarPower")
    result = {"太阳能电路电压":r}
    if r < SP('gs10.solarBatteryPower.board.low',0) or r > SP('gs10.solarBatteryPower.board.high',1000):
        raise TestItemFailException(failWeight = 10,message = u'太阳能电路电压异常，正常阈值0-1000',output=result)
    time.sleep(0.1) #这个必须要，否则下面的顺不下去
    return result

def T_07_batteryVoltage_A(product):
    u'''电池电路电压测试-判断电池电路电压是否满足要求'''
    sc = __askForPlateDeviceCom()
    r = sc.assertAndGetNumberParam(request='TestBattPower',response="TestBattPower")
    result = {"电池电路电压":r}
    if r < SP('gs10.batteryPower.low',3200) or r > SP('gs10.batteryPower.high',3600):
        raise TestItemFailException(failWeight = 10,message = u'电池电路电压异常，正常阈值3200-3600',output=result)
    time.sleep(0.1) #这个必须要，否则下面的顺不下去
    return result

def T_08_esam_A(product):
    u'''ESAM测试-判断ESAM状态及地区分散码是否正确'''
    sc = __askForPlateDeviceCom()
    
    response = sc.sendAndGet(request ='TestESAM').strip()
    if response.startswith("TestESAMOK"):
        esam = response[11:]
        districtCode = esam[-16:-8]
        esamId = esam[22:30]
        idCode = product.getTestingProductIdCode();
        
        if product.getTestingSuiteBarCode()!= "" and districtCode != SP('gs10.esam.defaultDistrict','45544301',str)   \
            and districtCode != __getDistrictCodeFromBarCode(product.getTestingSuiteBarCode()):
            raise TestItemFailException(failWeight = 10,message = u'ESAM异常，值:'+esam,output={"ESAM":esam})
        if esam[22:26] == 'FFFF':
            raise TestItemFailException(failWeight = 10,message = u'ESAM异常，值:'+esam,output={"ESAM":esam})
        if SESSION["testor"] != u"单机":
            __checkAndPersistEsamId(idCode,esamId)
        time.sleep(0.5)
        return {"ESAM":esam,"ESAMID":esamId}
    elif response == "ResetFail":
        raise TestItemFailException(failWeight = 10,message = u'ESAM复位失败，可能是焊接不良')
    elif response == "SelectMFFail":
        raise TestItemFailException(failWeight = 10,message = u'ESAM选择MF文件失败，可能是焊接不良')
    elif response.startswith("SelectMFErrCode"):
        code = response[-2:]
        raise TestItemFailException(failWeight = 10,message = u'ESAM选择MF文件错误，错误码:'+code)
    elif response == "ReadSysInfoFail":
        raise TestItemFailException(failWeight = 10,message = u'ESAM读系统信息失败')
    elif response.startswith("ReadSysInfoErrCode"):
        code = response[-2:]
        raise TestItemFailException(failWeight = 10,message = u'ESAM读系统信息返回错误，错误码:'+code)
    elif response == "SelectDFFail":
        raise TestItemFailException(failWeight = 10,message = u'ESAM选择DF文件失败')
    elif response.startswith("SelectDFErrCode"):
        code = response[-2:]
        raise TestItemFailException(failWeight = 10,message = u'ESAM选择DF文件返回错误，错误码:'+code)
   
def T_09_testHFChip_A(product):
    u'''测试高频芯片-测试高频芯片是否正常'''
    sc = __askForPlateDeviceCom()
    sc.assertSynComm(request ='TestHFChip',response = 'TestHFChipOK')
    time.sleep(0.1)
    
def T_10_soundLight_M(product):
    u'''声光指示测试-人工判断指示灯显示、蜂鸣器响声是否正常'''
    sc = __askForPlateDeviceCom()
    sc.assertSynComm(request ='TestLedLight',response = 'TestLedLightOK')
    mcr = manulCheck(u"声光指示测试", u"请确认指示灯显示正常，蜂鸣器响声正常。")
    if not mcr:
        raise TestItemFailException(failWeight = 10,message = u'声光指示测试人工判断不通过！')

def T_11_oled_M(product):
    u'''OLED屏幕测试-人工判断OLED屏幕是否全白'''
    sc = __askForPlateDeviceCom()
    sc.asynSend('TestOLED')
    if not manulCheck(u"OLED屏幕测试", u"请确认屏幕全白。"):
        raise TestItemFailException(failWeight = 10,message = u'OLED屏幕测试人工判断不通过！')
    sc.asynReceiveAndAssert('TestOLEDOK')

def T_12_displayDirKey_M(product):
    u'''显示方向控制键测试-屏幕显示倒转，检查是否通过'''
    sc = __askForPlateDeviceCom()
    sc.assertSynComm(request ='CloseLcdDisp',response = 'CloseLcdDispOK')
    autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"请按动屏幕倒置键",
                         lambda:sc.assertSynComm(request ='TestDirection',response = 'TestDirectionOK'))
    time.sleep(1)
    sc.assertSynComm(request ='ReadButtonStatus',response = 'ButtonisRelease')
    

def T_13_testSensiSwitch_M(product):
    u'''灵敏度条件开关测试-测试灵敏度调节开关拨动并确保其出厂在L位置'''
    sc = __askForPlateDeviceCom()
     
    r = sc.assertAndGetNumberParam(request ='TestSensiSwitch',response = 'TestSensiSwitch')
    failException = TestItemFailException(failWeight = 10,message = u'灵敏度开关测试不通过')
    if r == 0:
        autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"请将灵敏度开关拨至另一侧",
                             lambda:sc.assertAndGetNumberParam(request ='TestSensiSwitch',response = 'TestSensiSwitch') == 1
                            ,failException)
        autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"测试成功，请将灵敏度开关拨回原来的位置",
                             lambda:sc.assertAndGetNumberParam(request ='TestSensiSwitch',response = 'TestSensiSwitch') == 0
                            ,failException)
    else:
        autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"请将灵敏度开关拨至另一侧",
                             lambda:sc.assertAndGetNumberParam(request ='TestSensiSwitch',response = 'TestSensiSwitch') == 0
                            ,failException)

def T_14_disassemblePowerOff_M(product):
    u'''防拆下电测试-防拆下电功能测试'''
    if not manulCheck(u"防拆下电测试", u"按下防拆按钮后，屏幕应闪现'标签失效'，请确认。"):
        raise TestItemFailException(failWeight = 10,message = u'防拆下电测试人工判断不通过！')

