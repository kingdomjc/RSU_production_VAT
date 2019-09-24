#encoding:utf-8
u"版本下载，依次通过NuLink下载boot版本、信息区、VAT应用版本"

suiteName = u'''VAT版本下载'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过


from hhplt.parameters import SESSION,PARAM
from hhplt.testengine.server import serverParam as SP,serialCode
from hhplt.testengine.testcase import uiLog,superUiLog
from hhplt.deviceresource import askForResource
from hhplt.deviceresource.GS11SHVatSuite import GS11NuLink
from hhplt.testengine.versionContainer import getVersionFile
import VersionDownloadIOController
from hhplt.testengine.parallelTestSynAnnotation import syntest
import time

def __getNuLink(slot):
    '''获得ICP下载工具'''
    return askForResource("GS11NuLink-slot%s"%slot, GS11NuLink,
                          linkId = PARAM["linkId-slot%s"%slot],
                          nulinkCfg0Value = PARAM["nulinkCfg0Value"],
                          nulinkCfg1Value = PARAM["nulinkCfg1Value"]
                          )

def __getIoBoard():
    '''获得IO板资源'''
    return askForResource("VersionDownloadIOController", VersionDownloadIOController.VersionDownloadIOController,)

autoTrigger = VersionDownloadIOController.VersionDownloadIOControllerAutoTrigger

isTesting = False
finishedTestSlots = 0

@syntest
def setup(product): 
    '''初始化'''
    SESSION["isMend"] = True    #版本下载全部离线
    global isTesting
    if not isTesting:
        isTesting = True
        SESSION["autoTrigger"].pause()
        iob = __getIoBoard() 
        iob.clearAllLight()
        iob.closeClap()
        time.sleep(1)   #等待夹具到位

@syntest
def finalFun(product):
    u'''资源回收'''
    global finishedTestSlots,isTesting
    finishedTestSlots += 1
    iob = __getIoBoard()
    if finishedTestSlots == 6:
        iob.openClap()
        isTesting = False
        finishedTestSlots = 0
        SESSION["autoTrigger"].resume()
    if not ( product.finishSmoothly and product.testResult):    #下载失败
        iob.showLight(product.productSlot)


def T_01_initCfg_A(product):
    u"初始化CFG-初始化芯片CFG配置"
    nul = __getNuLink(product.productSlot)
    uiLog(u"初始化config区配置")
    nul.initCfg()
    
def T_02_downloadBoot_A(product):
    u"下载Boot-写入Boot"
    versionFileName = SP("gs11.boot.filename",PARAM["defaultBootFile"],str)
    vf = getVersionFile(versionFileName)
    uiLog(u"版本文件:"+vf)
    __getNuLink(product.productSlot).downloadBoot(vf,verify=False)
    return {u"BOOT版本文件":versionFileName}
    

def T_03_writeInfo_A(product):
    u"初始化信息区-写入初始OBU的信息区"
    nul = __getNuLink(product.productSlot)
    magicWord = "55555555"
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

def T_04_downloadVatVersion_A(product):
    u"下载VAT版本-下载测试用的VAT版本"
    versionFileName = SP("gs11.vatVersion.filename",PARAM["defaultVatVersionFile"],str)
    vf = getVersionFile(versionFileName)
    uiLog(u"版本文件:"+vf)
    __getNuLink(product.productSlot).downloadVersion(vf,verify=False)
    return {u"VAT版本文件":versionFileName}
            
