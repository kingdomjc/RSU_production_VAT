#encoding:utf-8
u'''单板维修工位，用于单板维修后的测试，测试通过后，返回到正式产线的数字测试工位'''

suiteName = u'''单板维修工位'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.testengine.testcase import uiLog
from hhplt.productsuite.gs10 import board_digital,board_rf_conduct
import time

def setup(product):
    '''检查工装板电流，如果范围不对，终止测试'''
    board_digital.setup(product)

def finalFun(product):
    board_digital.finalFun(product)

def T_01_testVersionDownload_A(product):
    u'''下载测试版本-如果板子无版本，请勾选此项'''
    return board_digital.T_01_testVersionDownload_A(product)

def T_02_initFactorySetting_A(product):
    u'''出厂信息清零-维修工位勾选此项，抹去产品旧标识'''
    sc = board_digital.__askForPlateDeviceCom()
    try:
        sc.startBslWriting(board_digital.versionFile)
        uiLog(u"开始写入MAC地址")
        sc.save_obu_id(board_digital.__toBytesarray("FFFFFFFF"))
    finally:
        sc.finishBslWritten()
        time.sleep(1)
    
def T_03_rs232Test_A(product):
    u'''RS232测试-自动判断RS232应答返回是否正确'''
    return board_digital.T_03_rs232Test_A(product)

def T_04_esam_A(product):
    u'''ESAM测试-判断地区分散码是否正确'''
    return board_digital.T_08_esam_A(product)
    
def T_05_transmittingPower_A(product):
    u'''发射功率测试-判断发射功率'''    
    return board_rf_conduct.T_04_transmittingPower_A(product)
    
def T_06_receiveSensitivity_A(product):
    u'''接收灵敏度测试-判断接收灵敏度是否满足标准'''    
    return board_rf_conduct.T_03_receiveSensitivity_A(product)

def T_07_reset_M(product):
    u'''复位测试-单板上电后返回数据，系统自动判断是否正确'''
    return board_digital.T_04_reset_M(product)

def T_08_capacityVoltage_A(product):
    u'''电容电路电压测试-根据电容电路电压值判断是否满足要求'''
    return board_digital.T_05_capacityVoltage_A(product)
    
def T_09_solarVoltage_A(product):
    u'''太阳能电路电压测试-判断太阳能电路电压是否满足要求'''
    return board_digital.T_06_solarVoltage_A(product)
    
def T_10_batteryVoltage_A(product):
    u'''电池电路电压测试-判断电池电路电压是否满足要求'''
    return board_digital.T_07_batteryVoltage_A(product)

def T_11_testHFChip_A(product):
    u'''测试高频芯片-测试高频芯片是否正常'''
    return board_digital.T_09_testHFChip_A(product)

def T_12_soundLight_M(product):
    u'''声光指示测试-人工判断指示灯显示、蜂鸣器响声是否正常'''
    return board_digital.T_10_soundLight_M(product)

def T_13_oled_M(product):
    u'''OLED屏幕测试-人工判断OLED屏幕是否全白'''
    return board_digital.T_11_oled_M(product)

def T_14_displayDirKey_M(product):
    u'''显示方向控制键测试-屏幕显示倒转，检查是否通过'''
    return board_digital.T_12_displayDirKey_M(product)

def T_15_testSensiSwitch_M(product):
    u'''灵敏度条件开关测试-测试灵敏度调节开关拨动并确保其出厂在L位置'''
    return board_digital.T_13_testSensiSwitch_M(product)

def T_16_readRfCard_A(product):
    u'''读高频卡测试-读高频卡测试'''
    return board_rf_conduct.T_01_readRfCard_A(product)
    
def T_17_wakeupSensitivity_A(product):
    u'''唤醒灵敏度测试-判断高低灵敏度是否满足标准'''
    return board_rf_conduct.T_02_wakeupSensitivity_A(product)  

#def T_18_disturbOn14k_A(product):
#    u'''5.8G芯片上电14k干扰测试-上电时发送14k，检查干扰是否造成混乱'''
#    return board_rf_conduct.T_07_disturbOn14k_M(product)

def T_18_staticCurrent_A(product):
    u'''静态电流测试-判断静态电流值是否在正常范围内'''
    return board_rf_conduct.T_05_staticCurrent_A(product)
    
def T_19_deepStaticCurrent_M(product):#深度静态电流暂时不测
    u'''深度静态电流测试-判断深度静态电流值是否在正常范围内'''
    return board_rf_conduct.T_06_deepStaticCurrent_A(product)