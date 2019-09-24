#encoding:utf-8
u'''整机工位测试项\n请将USB线插入OBU整机，按住防拆开关，然后开始测试'''

suiteName = u'''整机工位测试项'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.productsuite.gs10 import manual_board,auto_board,board_digital
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.productsuite.gs10.board_digital import __askForPlateDeviceCom
from hhplt.testengine.manul import autoCloseAsynMessage
from hhplt.parameters import SESSION
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.server import serverParam as SP
from hhplt.testengine.server import ServerBusiness

import os
import time

VAT_VERSION_FILE = os.path.dirname(os.path.abspath(__file__))+os.sep+"versions\\obu-vat.txt"

def __checkBoardFinished(idCode):
    '''检查单板(数字、射频）工位已完成'''
    with ServerBusiness(testflow = True) as sb:
        status = sb.getProductTestStatus(productName="GS10 OBU" ,idCode = idCode)
        if status is None:
            raise AbortTestException(message=u"该产品尚未进行单板测试，整机测试终止")
        else:
            sn1 = auto_board.suiteName;
            sn2 = manual_board.suiteName;
            if (sn1 not in status["suiteStatus"] or status["suiteStatus"][sn1] != 'PASS') and \
                (sn2 not in status["suiteStatus"] or status["suiteStatus"][sn2] != 'PASS'):
                raise AbortTestException(message=u"该产品的单板测试项未进行或未通过，整机测试终止")
            
def setup(product):
    '''准备函数，同射频相同，读取MAC地址并设置'''
    if SESSION["isMend"]:
        return  #维修测试不需要读MAC

    uiLog(u"正在读取产品标识...")
    sc = __askForPlateDeviceCom()
    try:
        try:
            macBytes = sc.read_obu_id(VAT_VERSION_FILE)
        except Exception,e:
            if "BSL password error" in e.message :
                #如果因密码不对读取不到MAC地址，证明版本不是测试版本，且已经被擦除，重新下载测试版本
                uiLog(u"OBU中非测试版本，正在下载测试版本...")
                sc.downloadVersion(version_file = VAT_VERSION_FILE)
                macBytes = sc.read_obu_id(VAT_VERSION_FILE)
            else:
                raise e    
        mac = "".join(["%.2X"%i for i in macBytes])
        product.setTestingProductIdCode(mac)
        uiLog(u"测试产品标识:"+mac)
        __checkBoardFinished(mac)
    except AbortTestException,e:
        raise e
    except Exception,e:
        print e
        raise AbortTestException(message = u'BSL方式读取产品标识失败:'+e.message)
    finally:
        time.sleep(1)
        sc.clearSerialBuffer()

def T_01_rs232Test_A(product):
    u'''RS232测试-自动判断RS232应答返回是否正确'''
    return board_digital.T_03_rs232Test_A(product)

        
def T_02_sensiSwitchLocationVerify_A(product):
    u'''灵敏度开关位置判断-进行测试需要确认灵敏度开关在L档'''
    sc = __askForPlateDeviceCom()
    r = sc.assertAndGetNumberParam(request ='TestSensiSwitch',response = 'TestSensiSwitch')
    if r != 0:
        autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"请将灵敏度开关拨至另一侧",
                             lambda:sc.assertAndGetNumberParam(request ='TestSensiSwitch',response = 'TestSensiSwitch') == 0
                            ,TestItemFailException(failWeight = 10,message = u'灵敏度开关测试不通过'))
    
def T_03_capacityVoltage_A(product):
    u'''电容电路电压测试-根据电容电路电压值判断是否满足要求'''
    sc = __askForPlateDeviceCom()
    r = sc.assertAndGetNumberParam(request='TestCapPower',response="TestCapPower")
    result = {"电容电路电压":r}
    if r < SP('gs10.capPower.overall.low',3300) or r > SP('gs10.capPower.overall.high',3800):
        raise TestItemFailException(failWeight = 10,message = u'电容电压异常',output=result)
    return result    

def T_04_solarVoltage_A(product):
    u'''太阳能电路电压测试-判断太阳能电路电压是否满足要求'''
    #与数字单板测试判定阈值不同，故而不直接复用该用例
    sc = __askForPlateDeviceCom()
    r = sc.assertAndGetNumberParam(request='TestSolarPower',response="TestSolarPower")
    result = {"太阳能电路电压":r}
    if r < SP('gs10.solarBatteryPower.overall.low',3400) or r > SP('gs10.solarBatteryPower.overall.high',3800):
        raise TestItemFailException(failWeight = 10,message = u'太阳能电路电压异常',output=result)
    return result

def T_05_batteryVoltage_A(product):
    u'''电池电路电压测试-判断电池电路电压是否满足要求'''
    sc = __askForPlateDeviceCom()
    r = sc.assertAndGetNumberParam(request='TestBattPower',response="TestBattPower")
    result = {"电池电路电压":r}
    if r < SP('gs10.batteryPower.overall.low',3300) or r > SP('gs10.batteryPower.overall.high',4000):
        raise TestItemFailException(failWeight = 10,message = u'电池电路电压异常',output=result)
    return result
    
def T_06_esam_A(product):
    u'''ESAM测试-判断地区分散码是否正确'''
    board_digital.T_08_esam_A(product)
    
def T_07_soundLight_M(product):
    u'''声光指示测试-人工判断指示灯显示、蜂鸣器响声是否正常'''
    board_digital.T_10_soundLight_M(product)
    
def T_08_oled_M(product):
    u'''OLED屏幕测试-人工判断OLED屏幕是否全白'''
    board_digital.T_11_oled_M(product)
    
def T_09_displayDirKey_M(product):
    u'''显示方向控制键测试-屏幕显示倒转，检查是否通过'''
    board_digital.T_12_displayDirKey_M(product)


def T_10_formalVersionDownload_A(product):
    u'''正式版本下载-下载正式版本'''
    sc = __askForPlateDeviceCom()
    try:
        downloadFileName = SP("gs10.formalVersion.filename","obu-formal.txt",str)
        sc.downloadVersion(version_file = os.path.dirname(os.path.abspath(__file__))+os.sep+"versions\\"+downloadFileName)
    except Exception,e:
        raise e
    finally:
        time.sleep(1)
        sc.clearSerialBuffer()

def T_11_disassemblePowerOff_M(product):
    u'''防拆下电测试-松开防拆开关，检查按键无反应'''
    board_digital.T_14_disassemblePowerOff_M(product)