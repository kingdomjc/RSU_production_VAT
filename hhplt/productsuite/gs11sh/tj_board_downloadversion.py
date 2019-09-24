#encoding:utf-8
u""" 测试版本下载 """
import time

from hhplt.deviceresource.GS11SHVatSuite import GS11NuLink
from hhplt.deviceresource import askForResource
from hhplt.parameters import PARAM, SESSION
from hhplt.testengine.exceptions import AbortTestException
from hhplt.testengine.parallelTestSynAnnotation import syntest
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.versionContainer import getVersionFile
from hhplt.testengine.server import serverParam as SP



suiteName = u"测试版本下载"
version = "1.0"
failWeightSum = 10


import tj_board_digital


from IntegratedVATBoard import getIVB as __getIVB, IntegratedVATBoard, IntegratedVatTrigger


started = False

@syntest
def setup(product):
    SESSION["isMend"] = True
    global started
    if not started:
        started = True
        if IntegratedVatTrigger.INSTANCE is None:IntegratedVatTrigger()
        IntegratedVatTrigger.INSTANCE.closeClap()

    #OBU上电
    __getIVB().peripheralCtrl(product.productSlot).obuPowerCtrl(0x01)

    time.sleep(0.5)


finishedTestSlots = 0

@syntest
def finalFun(product):
    global finishedTestSlots
    finishedTestSlots += 1
    # OBU下电
    try:
        __getIVB().peripheralCtrl(product.productSlot).obuPowerCtrl(0x03)
    except IntegratedVATBoard.DeviceNoResponseException,e:
        pass
    if finishedTestSlots  == len(PARAM["productSlots"].split(",")):
        # 所有槽位执行完
        finishedTestSlots = 0
        IntegratedVatTrigger.INSTANCE.openClap()
        global started
        started = False

def __getNuLink(slot):
    # 获得ICP下载工具
    return askForResource("GS11NuLink-slot%s"%slot, GS11NuLink,
                          linkId = PARAM["linkId-slot%s"%slot],
                          nulinkCfg0Value = PARAM["nulinkCfg0Value"],
                          nulinkCfg1Value = PARAM["nulinkCfg1Value"] )


def __stateAtNLK(product):
    # 转入NuLink模式，用于读写Flash及下载版本
    if "channelState" not in product.param or product.param["channelState"] != 0x01:
        try:
            __getIVB().peripheralCtrl(product.productSlot).channelSelect(0x01)
            product.param["channelState"] = 0x01
        except IntegratedVATBoard.DeviceNoResponseException,e:
            raise AbortTestException(message = u'工装板通信失败，无法继续测试')

def T_01_initCfg_A(product):
    u"初始化CFG-初始化芯片CFG配置"
    __stateAtNLK(product)
    nul = __getNuLink(product.productSlot)
    uiLog(u"初始化config区配置")
    nul.initCfg()

def _T_02_downloadBoot_A(product):
    u"下载Boot-写入BOOT信息"
    __stateAtNLK(product)
    versionFileName = SP("gs11.boot.filename",PARAM["defaultBootFile"],str)
    vf = getVersionFile(versionFileName)
    uiLog(u"版本文件:"+vf)
    __getNuLink(product.productSlot).downloadBoot(vf,verify=False)
    return {u"BOOT版本文件":versionFileName}


def T_04_writeInfo_A(product):
    u"初始化信息区-写入OBU信息区初始值"
    __stateAtNLK(product)
    nul = __getNuLink(product.productSlot)
    magicWord = "FFFFFFFF"
    obuid = "FFFFFFFF"
    displayDirect = SP("gs11.initParam.displayDirect","00",str) #显示方向
    softwareVerionFile = SP("gs11.vatVersion.filename",PARAM["defaultVatVersionFile"],str)
    softwareVersion = "".join(softwareVerionFile.split("-")[2].split(".")[:3])+"00"
    hardwareVersion = SP("gs11.initParam.hardwareVersion","010000",str)#硬件版本号

    initWankenSensi_high_grade = SP('gs11.initWanken.high.grade',"03",str)#高灵敏度-grade
    initWankenSensi_high_level = SP('gs11.initWanken.high.level',"0E",str)#高灵敏度-level
    initWankenSensi_low_grade = SP('gs11.initWanken.low.grade',"03",str)   #低灵敏度-grade
    initWankenSensi_low_level = SP('gs11.initWanken.low.level',"0E",str)#低灵敏度-level
    wakeupMode = SP("gs11.initParam.wakeupMode","04",str)#唤醒模式
    amIndex = SP("gs11.initParam.amIndex","00",str)#AmIndex
    transPower = SP("gs11.initParam.transPower","02",str)   #发射功率
    txFilter = SP("gs11.initParam.txFilter","06",str)   #TxFilter
    sensitivity = SP("gs11.initParam.sensitivity","00",str)   #使用灵敏度

    CONFIG_BUILD_INFO = "".join((magicWord,obuid,displayDirect,softwareVersion,hardwareVersion))
    CONFIG_RF_PARA = "".join((magicWord,initWankenSensi_high_grade,initWankenSensi_high_level,
                              initWankenSensi_low_grade,initWankenSensi_low_level,
                              wakeupMode,amIndex,transPower,txFilter,sensitivity))
    nul.writeToInfo(CONFIG_BUILD_INFO,CONFIG_RF_PARA)
    return {u"初始信息区":CONFIG_BUILD_INFO+","+CONFIG_RF_PARA}


def T_05_downloadVatVersion_A(product):
    u"下载测试版本-下载测试用的VAT版本"
    __stateAtNLK(product)
    versionFileName = SP("gs11.vatVersion.filename",PARAM["defaultVatVersionFile"],str)
    vf = getVersionFile(versionFileName)
    uiLog(u"版本文件:"+vf)
    __getNuLink(product.productSlot).downloadVersion(vf,verify=False)
    uiLog(u"槽位[%s]版本下载成功，正在复位芯片"%product.productSlot)
    __getNuLink(product.productSlot).resetChip()
    #__getIVB().peripheralCtrl(product.productSlot).obuPowerCtrl(0x03)
    #time.sleep(0.5)
    #__getIVB().peripheralCtrl(product.productSlot).obuPowerCtrl(0x01)
    #time.sleep(0.5)
    return {u"VAT版本文件":versionFileName}
