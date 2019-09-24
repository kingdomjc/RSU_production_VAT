#encoding:utf-8
u"单板数字测试\n并行测试六个单板的数字功能"
from hhplt.productsuite.gs11sh.BoardIOController import BoardDigitIOControllerAutoTrigger, BoardDigitIOController,BoardIOController

suiteName = u'''单板数字测试'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

import time

from hhplt.parameters import SESSION,PARAM
from hhplt.testengine.parallelTestSynAnnotation import syntest,serialSuite
from hhplt.testengine.manul import askForSomething
from hhplt.deviceresource.GS11SHVatSuite import GS11ShDigitalBoardSwitcher,GS11VatSerial
from hhplt.deviceresource import askForResource
from hhplt.testengine.server import serverParam as SP,serialCode
from hhplt.testengine.testcase import uiLog,superUiLog
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.testutil import multipleTest,checkBySenser
import util

autoTrigger = BoardDigitIOControllerAutoTrigger

BARCODE_CONTAINER = {}  #每个周期的条码扫描结果放在这里，用完删掉

#OBU串口
__getObuSerial = lambda slotNo:askForResource('GS11VatSerial-slot%s'%slotNo, GS11VatSerial,serialPortName = PARAM["obuSerial-slot%s"%slotNo])

#IO控制板
def __getIo():return askForResource("BoardDigitIOController",BoardDigitIOController)

#工装板（开关板）
def __getSwitcher():return askForResource('BoardDigitalSwitch',GS11ShDigitalBoardSwitcher,serialPort = PARAM["boardDigitalFixtureCom"],baudrate=38400)

#声光检测板
def __getSoundLight():return askForResource('SoundLightDetector',GS11ShDigitalBoardSwitcher,serialPort = PARAM["soundLightDetectorCom"],baudrate=115200)

@syntest
def setup(product):
    iob = __getIo()
    if iob.currentState != BoardIOController.STATE_TESTING:
        # 软件触发开始，如果需要扫条码，不能合夹具
        if u"扫描条码" not in SESSION["seletedTestItemNameList"]:
            iob.startTesting()
            __getIo().ctrlDemolish(product.productSlot,True)
    else:# 按钮触发，扫不了条码，去掉这个测试项
        if u"扫描条码" in SESSION["seletedTestItemNameList"]:
            SESSION["seletedTestItemNameList"].remove(u"扫描条码")
        __getIo().ctrlDemolish(product.productSlot,True)

finishedTestSlots = 0

@syntest
def finalFun(product):
    global finishedTestSlots
    finishedTestSlots += 1
    __getSwitcher().powerObu(product.productSlot,False)
    iob = __getIo()
    iob.ctrlDemolish(product.productSlot,False)
    if finishedTestSlots  == len(PARAM["productSlots"].split(",")):
        finishedTestSlots = 0
        iob.stopTesting()
        if u"扫描条码" not in SESSION["seletedTestItemNameList"]:
            SESSION["seletedTestItemNameList"].append(u"扫描条码")


def __scanAllBarCodes():
    #　扫描全部条码
    for slot in PARAM["productSlots"].split(","):
        #if lastSlot is not None:sc.setIndicatorLight(slot,False)
        #sc.setIndicatorLight(slot,True)
        try:
            barCode = askForSomething(u"扫描条码", u"请扫描槽位[%s]的单板条码"%slot,autoCommit=False)
        except AbortTestException,e:
            barCode = u"人工中止"
        BARCODE_CONTAINER[slot] = barCode
    __getIo().startTesting()

def __fillBarCode(product):
    # 给产品填充条码，填充完所有条码后，合夹具
    barCode = BARCODE_CONTAINER[product.productSlot]
    product.setTestingSuiteBarCode(barCode)
    del BARCODE_CONTAINER[product.productSlot]
    if barCode == u"人工中止":raise AbortTestException(message=u"人工中止")
    __getIo().ctrlDemolish(product.productSlot,True)
    return {u"条码扫描结果":barCode}

@syntest
def T_01_scanBarCode_M(product):
    u"扫描条码-扫描各个槽位的条码"
    if product.productSlot in BARCODE_CONTAINER:
        return __fillBarCode(product)
    else:
        __scanAllBarCodes()
        return __fillBarCode(product)

def T_02_rs232Test_A(product):
    u"RS232测试-测试RS232串口通信"
    sw = __getSwitcher()
    sw.powerObu(product.productSlot,True)
    sw.switchCurrentMode(product.productSlot,1)
    sw.setSerialCom(product.productSlot,True)
    time.sleep(1)
    sc = __getObuSerial(product.productSlot)
    sc.assertSynComm(request ='TestUART',response = 'TestUartOK')
    
def T_03_allocMac_A(product):
    u"分配MAC地址-读取MAC地址，如果不存在，分配新的，并写入出厂信息"
    sc = __getObuSerial(product.productSlot)
    r = sc.sendAndGet("D-ReadFlashPara 0x02 0x00 0x10").strip()
    if not r.startswith("D-ReadFlashOK"):raise AbortTestException(message=u"读取OBU的MAC地址失败")
    obuFlash = util.cmdFormatToHexStr(r[14:])
    obuid = obuFlash[8:16]
    uiLog(u"读取到OBUFlash："+obuFlash)

    initFactoryInfo = obuFlash[16:]
    # initFactoryInfo = SP("gs11.test.initFactoryInfo","0109200100010000",paramType=str)    #01（显示模式）09 20 01 00（软件版本号）01 00 00（硬件版本号）；

    if not obuid.startswith(PARAM["macPrefix"]):
        obuid = serialCode("gs11sh.mac") #分配新的MAC地址(obuid)
        product.setTestingProductIdCode(obuid)
        uiLog(u"分配新的OBUID：%s"%obuid)
    else:
        uiLog(u"OBUID已存在，原标识：%s"%obuid)
        product.setTestingProductIdCode(obuid)

    targetFlash = "55555555"+obuid.lower()+initFactoryInfo
    r = sc.sendAndGet(request="D-WriteFlashPara 0x11 0x00 "+util.hexStrToSerialCmdFormat(targetFlash))
    if not r.startswith("D-WriteFlashOK"):raise AbortTestException(message=u"写入OBUID及出厂信息失败")

    r = sc.sendAndGet("D-ReadFlashPara 0x02 0x00 0x10").strip()
    if not r.startswith("D-ReadFlashOK"):raise AbortTestException(message=u"读取OBU的MAC地址失败")
    obuFlash = util.cmdFormatToHexStr(r[14:])
    if obuFlash!=targetFlash:raise AbortTestException(message=u"写入OBU灵敏度信息失败")

    return {"OBUID":obuid,u"出厂信息":initFactoryInfo}

def T_04_esam_A(product):
    u"ESAM测试-测试ESAM工作是否正常"
    sc = __getObuSerial(product.productSlot)
    response = sc.sendAndGet(request ='TestESAM').strip()
    if response.startswith("TestESAMOK"):
        esam = response[11:]
        districtCode = esam[-16:-8]
        esamId = esam[22:30]
        targetDistrictCode = SP("gs11.esamDistrictCode."+product.getTestingSuiteBarCode()[:2],"",str)
        if product.getTestingSuiteBarCode()!= "" and districtCode != SP('gs11.esam.defaultDistrict','45544301',str)   \
            and districtCode != targetDistrictCode():
            raise TestItemFailException(failWeight = 10,message = u'ESAM异常，值:'+esam,output={"ESAM":esam})
        if esam[22:26] == 'FFFF':
            raise TestItemFailException(failWeight = 10,message = u'ESAM异常，值:'+esam,output={"ESAM":esam})
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
    
def T_05_reset_A(product):
    u"复位测试-测试插卡复位"
    sc = __getObuSerial(product.productSlot)
    iob = __getIo()
    sc.asynSend("TestReset")
    iob.triggerResetButton(product.productSlot)
    sc.asynReceiveAndAssert("PowerOnSuccess")
    
def T_06_capacityVoltage_A(product):
    u"电容电路电压测试-根据电容电路电压值判断是否满足要求"
    r = __getObuSerial(product.productSlot).assertAndGetNumberParam(request='TestCapPower',response="TestCapPower")
    result = {"电容电路电压":r}
    cl,ch = SP('gs11.capPower.board.low',2500),SP('gs11.capPower.board.high',3500)
    if r < cl or r > ch:
        raise TestItemFailException(failWeight = 10,message = u'电容电压异常，正常阈值%d-%d'%(cl,ch),output=result)
    return result
    
def T_07_solarVoltage_A(product):
    u'太阳能电路电压测试-判断太阳能电路电压是否满足要求'
    r = __getObuSerial(product.productSlot).assertAndGetNumberParam(request='TestSolarPower',response="TestSolarPower")
    result = {"太阳能电路电压":r}
    sl,sh = SP('gs11.solarBatteryPower.board.low',0),SP('gs11.solarBatteryPower.board.high',1000)
    if r < sl or r > sh:
        raise TestItemFailException(failWeight = 10,message = u'太阳能电路电压异常，正常阈值%d-%d'%(sl,sh),output=result)
    time.sleep(0.1) #这个必须要，否则下面的顺不下去
    return result

def T_08_batteryVoltage_A(product):
    u'电池电路电压测试-判断电池电路电压是否满足要求'
    r = __getObuSerial(product.productSlot).assertAndGetNumberParam(request='TestBattPower',response="TestBattPower")
    result = {"电池电路电压":r}
    bl,bh =  SP('gs11.batteryPower.board.low',3200),SP('gs11.batteryPower.board.high',3600)
    if r < bl or r > bh:
        raise TestItemFailException(failWeight = 10,message = u'电池电路电压异常，正常阈值%d-%d'%(bl,bh),output=result)
    time.sleep(0.1) #这个必须要，否则下面的顺不下去
    return result

def T_09_testHFChip_A(product):
    u'测试高频芯片-测试高频芯片是否正常'
    __getObuSerial(product.productSlot).assertSynComm(request ='TestHFChip',response = 'TestHFChipOK')
    time.sleep(0.1)
    
def T_10_readRfCard_A(product):
    u'测试高频读卡-测试高频读卡是否正常'
    testTimes = SP('gs11.testHf.number',5)   #测试次数
    __getObuSerial(product.productSlot).assertSynComm(request ='TestHF %d'%testTimes,response = 'TestHFOK')
    
def T_11_redLight_A(product):
    u'红色LED灯检测-自动判定红LED灯是否正常亮起'
    sl = __getSoundLight()
    sc = __getObuSerial(product.productSlot)
    thrd = int(PARAM["redLedSensorThreshold"].split(",")[int(product.productSlot)-1])
    checkBySenser(u"红色LED灯",1,lambda:sc.asynSend("TestRedLedPara 1500"),
                  lambda:sc.asynReceiveAndAssert("TestRedLedParaOK"),
                  lambda:sl.getLightState(product.productSlot,"red") > thrd)
    
def T_12_greenLight_A(product):
    u'绿色LED灯检测-自动判定绿LED灯是否正常亮起'
    sl = __getSoundLight()
    sc = __getObuSerial(product.productSlot)
    thrd = int(PARAM["greenLedSensorThreshold"].split(",")[int(product.productSlot)-1])
    checkBySenser(u"绿色LED灯",1,lambda:sc.asynSend("TestGreenLedPara 3000"),
                  lambda:sc.asynReceiveAndAssert("TestGreenLedParaOK"),
                  lambda:sl.getLightState(product.productSlot,"green") > thrd)
    
@syntest
def T_13_beep_A(product):
    u'蜂鸣器检测-自动判定蜂鸣器是否响起'
    sl = __getSoundLight()
    sc = __getObuSerial(product.productSlot)
    checkBySenser(u"蜂鸣器",2,lambda:sc.asynSend("TestBeepPara 1500"),
                  lambda:sc.asynReceiveAndAssert("TestBeepParaOK"),
                  lambda:sl.getSoundState(product.productSlot))

def T_14_oled_A(product):
    u'OLED屏幕测试(不检)-自动判断OLED屏幕是否全白'
    return {u"OLED测试结果":u"暂不测试"}

def T_15_bluetooth_A(product):
    u"蓝牙测试（不检）-检测OBU蓝牙功能是否正常"
    return {u"蓝牙测试结果":u"暂不测试"}
    
def T_16_staticCurrent_A(product):
    u'静态电流测试-判断静态电流值是否在正常范围内'
    sw = __getSwitcher()
    sw.setSerialCom(product.productSlot,False)
    time.sleep(3)
    sw.switchCurrentMode(product.productSlot,0)
    v = sw.readCurrent(product.productSlot)
    v = (float(v)*2.5/4096/11/14000)*1000000
    resultMap = {u"静态电流":v}
    sl,sh = SP('gs11.staticCurrent.low',2),SP('gs11.staticCurrent.high',18)
    if v < sl or v > sh:
        raise TestItemFailException(failWeight = 10,message = u'静态电流测试不通过，正常阈值%d-%d'%(sl,sh),output=resultMap)
    return resultMap
    
def T_17_deepStaticCurrent_A(product):
    u'深度静态电流测试-判断深度静态电流值是否在正常范围内'
    sw = __getSwitcher()
    iob = __getIo()
    iob.ctrlDemolish(product.productSlot,False)
    sw.switchCurrentMode(product.productSlot,0)
    time.sleep(3)
    v = sw.readCurrent(product.productSlot)
    v = (float(v)*2.5/4096/11/14000)*1000000
    resultMap = {u"深度静态电流":v}
    sl,sh = SP('gs11.deepStaticCurrent.low',2),SP('gs11.deepStaticCurrent.high',18)
    if v < sl or v > sh:
        raise TestItemFailException(failWeight = 10,message = u'深度静态电流测试不通过，正常阈值%d-%d'%(sl,sh),output=resultMap)
    return resultMap


