#encoding:utf-8
u"单板测试，包括单板数字测试及射频测试。单板正常放置在夹具上，按下开始按钮进行测试"

suiteName = u'''单板测试'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过


from hhplt.productsuite.gs11 import board_digital,board_rf_conduct
from hhplt.testengine.testutil import multipleTest,checkBySenser
from hhplt.deviceresource import askForResource,GS11IOBoardDevice,GS11NuLink,VideoCaptureAndParser
from hhplt.testengine.server import serverParam as SP,serialCode
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.versionContainer import getVersionFile
import time,os
from hhplt.testengine.testcase import uiLog,superUiLog
from hhplt.parameters import SESSION,PARAM
from hhplt.testengine.manul import broadcastTestResult,closeAsynMessage


def __getIoBoard():
    '''获得IO板资源'''
    return askForResource("GS11IOBoardDevice", GS11IOBoardDevice.GS11IOBoardDevice,)

def __getNuLink():
    '''获得ICP下载工具'''
    return askForResource("GS11NuLink", GS11NuLink.GS11NuLink,)

def __getVideoCapture():
    '''获得摄像头抓拍工具'''
    return askForResource("VideoCaptureAndParser", VideoCaptureAndParser.VideoCaptureAndParser,)


autoTrigger = GS11IOBoardDevice.IOBoardAutoTrigger

def setup(product):
    '''初始化'''
    #检查夹具动作，如果夹具没合上，则合上夹具
    iob = __getIoBoard() 
    iob.closeClap()
    iob.releaseDemolishButton()
    board_digital.setup(product)
    SESSION["autoTrigger"].pause()
    closeAsynMessage()

def finalFun(product):
    '''自动弹开夹具，输出结果信号，并给OBU下电'''
    try:
        board_digital.finalFun(product)
        iob = __getIoBoard()
        iob.openClap()
        broadcastTestResult(product)
    finally:
        SESSION["autoTrigger"].resume()

def T_01_scanBarCode_A(product):
    u"扫描条码-扫描单板条码，用于后续追溯"
    try:
        __getVideoCapture().captureBarcodeSnapshot()
        barCode = __getVideoCapture().parseBarcode()
        product.setTestingSuiteBarCode(barCode)
        return {u"条码扫描结果":barCode}
    finally:
        __getIoBoard().closeLighting()

def T_02_testVersionDownload_A(product):
    u"下载测试版本-下载用于测试的OBU版本"
    vf = getVersionFile(SP("gs11.vatVersion.filename","GS11-VAT-09.00.00.version",str))
    uiLog(u"版本文件:"+vf)
    nul = __getNuLink()
    try:
        uiLog(u"切换至NuLink模式")
        __getIoBoard().switchToNuLink()
        nul.downloadVersion(vf,verify=False)
    finally:
        #如果后面不跟随出场信息写入，则复位芯片并切回串口模式；否则不必退出
        if "出厂信息写入" not in SESSION["seletedTestItemNameList"]:
            uiLog(u"复位芯片...")
            try:
                nul.resetChip()
            finally:
                uiLog(u"切换至普通串口模式")
                __getIoBoard().switchToNormalSerial()        

def T_03_initFactorySetting_A(product):
    u'''出厂信息写入-写入MAC地址，唤醒灵敏度参数等，通过ICP方式写入并自动判断信息一致'''
    #读取旧的信息内容
    magicWord = "55555555"
    try:
        uiLog(u"切换至NuLink模式")
        __getIoBoard().switchToNuLink()
        nul = __getNuLink()
        infos = None
        try:
            infos = nul.readInfo()
            obuid = infos[8:16]
            superUiLog(u"单板信息区内容:"+infos)
            if infos.startswith(magicWord) and obuid!="FFFFFFFF":    #有魔术字，说明出场信息已经写过了
                uiLog(u"出厂信息已写入，原标识：%s"%obuid)
                product.setTestingProductIdCode(obuid)
                uiLog(u"复位芯片...")
                nul.resetChip()
                return {"OBUID":obuid,"原出厂信息区":infos[:36]+","+infos[128:200]}
        except TestItemFailException,e:
            #如果读出失败，那么也判定为需要写
            uiLog(u"区域读取失败，开始写入出厂信息")
        obuid = serialCode("mac") #分配新的MAC地址(obuid)
        displayDirect = SP("gs11.initParam.displayDirect","00",str) #显示方向
        
        softwareVerionFile = SP("gs11.vatVersion.filename","GS11-VAT-09.00.00.version",str)
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
        uiLog(u"初始化config区配置")
        nul.initCfg()
        nul.writeToInfo(CONFIG_BUILD_INFO,CONFIG_RF_PARA)
        uiLog(u"分配新的OBUID：%s"%obuid)
        product.setTestingProductIdCode(obuid)
        uiLog(u"复位芯片...")
        nul.resetChip()
        return {"OBUID":obuid,u"初始信息区":CONFIG_BUILD_INFO+","+CONFIG_RF_PARA}
    finally:
        uiLog(u"切换至普通串口模式")
        __getIoBoard().switchToNormalSerial()

def T_04_rs232Test_A(product):
    u'''RS232测试-自动判断RS232应答返回是否正确'''
    __getIoBoard().closeLighting()
    return board_digital.T_03_rs232Test_A(product)

def T_05_esam_A(product):
    u'''ESAM测试-判断地区分散码是否正确'''
    return board_digital.T_08_esam_A(product)
    
def T_06_transmittingPower_A(product):
    u'''发射功率测试-判断发射功率'''
    return multipleTest(board_rf_conduct.T_04_transmittingPower_A,product,3)
    
def T_07_receiveSensitivity_A(product):
    u'''接收灵敏度测试-判断接收灵敏度是否满足标准'''
    return multipleTest(board_rf_conduct.T_03_receiveSensitivity_A,product,3)  
    
def T_08_reset_A(product):
    u'''复位测试-单板上电后返回数据，系统自动判断是否正确'''
    sc = board_digital.__askForPlateDeviceCom()
    iob = __getIoBoard()
    sc.asynSend("TestReset")
    iob.triggerResetButton()
    sc.asynReceiveAndAssert("PowerOnSuccess")
#    try:
#        sc.bslDevice.serial.setTimeout(2)
#        sc.asynReceiveAndAssert("PowerOnSuccess")
#    except TestItemFailException,e:
#        #第二个的PowerOnSuccess可以收不到
#        pass
#    finally:
#        sc.bslDevice.serial.setTimeout(15)
    time.sleep(0.5)
    
def T_09_capacityVoltage_A(product):
    u'''电容电路电压测试-根据电容电路电压值判断是否满足要求'''    
    return board_digital.T_05_capacityVoltage_A(product)
    
def T_10_solarVoltage_A(product):
    u'''太阳能电路电压测试-判断太阳能电路电压是否满足要求'''
    return board_digital.T_06_solarVoltage_A(product)

def T_11_batteryVoltage_A(product):
    u'''电池电路电压测试-判断电池电路电压是否满足要求'''    
    return board_digital.T_07_batteryVoltage_A(product)

def T_12_testHFChip_A(product):
    u'''测试高频芯片-测试高频芯片是否正常'''    
    return board_digital.T_09_testHFChip_A(product)

def T_13_readRfCard_A(product):
    u'''测试高频读卡-测试高频读卡是否正常'''
    return board_rf_conduct.T_01_readRfCard_A(product)
        
def T_14_redLight_A(product):
    u'''红色LED灯检测-自动判定红LED灯是否正常亮起'''
    iob = __getIoBoard()
    sc = board_digital.__askForPlateDeviceCom()
    checkBySenser(u"红色LED灯",1,lambda:sc.asynSend("TestRedLedPara 1000"),
                  lambda:sc.asynReceiveAndAssert("TestRedLedParaOK"),iob.checkLedLightState)

def T_15_greenLight_A(product):
    u'''绿色LED灯检测-自动判定绿LED灯是否正常亮起'''
    iob = __getIoBoard()
    sc = board_digital.__askForPlateDeviceCom()
    checkBySenser(u"红色LED灯",1,lambda:sc.asynSend("TestGreenLedPara 1000"),
                  lambda:sc.asynReceiveAndAssert("TestGreenLedParaOK"),iob.checkLedLightState)
    
def T_16_beep_A(product):
    u'''蜂鸣器检测-自动判定蜂鸣器是否响起'''
    iob = __getIoBoard()
    sc = board_digital.__askForPlateDeviceCom()
    checkBySenser(u"蜂鸣器",2,lambda:sc.asynSend("TestBeepPara 3000"),
                  lambda:sc.asynReceiveAndAssert("TestBeepParaOK"),iob.checkBeepState)
    
def T_17_oled_A(product):
    u'''OLED屏幕测试-自动判断OLED屏幕是否全白'''
    pass #单板暂时不检
   
def T_18_wakeupSensitivity_A(product):
    u'''唤醒灵敏度测试-判断高低灵敏度是否满足标准'''
#    low_level_power = SP('gs11.wakeup.power.low',-33.5)   #低唤醒功率
#    high_level_power = SP('gs11.wakeup.power.high',-32.5) #高唤醒功率
    #GS11的上述两个参数不使用服务端获得，而从本地配置文件中搞
    
    low_level_power = PARAM['gs11.wakeup.power.low']   #低唤醒功率
    high_level_power = PARAM['gs11.wakeup.power.high'] #高唤醒功率
    uiLog(u"唤醒功率范围：%.2f-%.2f"%(low_level_power,high_level_power))
    
    sc = board_rf_conduct.__askForPlateDeviceCom()
    try:
        lowWakenSensiResult = sc.adjustWakenSensi(low_level_power)
    except TestItemFailException,e:
        e.message = u"低灵敏度测试失败"
        raise e        
    try:
        highWakenSensiResult = sc.adjustWakenSensi(high_level_power)
    except TestItemFailException,e:
        e.message = u"高灵敏度测试失败"
        raise e        
    #写入唤醒灵敏度的值
    uiLog(u"开始写入灵敏度值")
#    writeSensiCmd = "D-WriteWakeSensiPara 4 0x%.2x 0x%.2x 0x%.2x 0x%.2x"%(highWakenSensiResult[0],highWakenSensiResult[1],
#                                                                  lowWakenSensiResult[0],lowWakenSensiResult[1])
#    sc.assertSynComm(request =writeSensiCmd,response = 'D-WriteWakeSensiParaOK')

    iob = __getIoBoard()
    nul = __getNuLink()
    try:
        iob.switchToNuLink()
        oriData = nul.readInfo()
        CONFIG_BUILD_INFO = oriData[:32]
        CONFIG_RF_PARA = oriData[128:154]
        CONFIG_RF_PARA = CONFIG_RF_PARA[:8]+"%.2X%.2X%.2X%.2X"%(highWakenSensiResult[0],highWakenSensiResult[1],
                                                                  lowWakenSensiResult[0],lowWakenSensiResult[1]) + \
                        CONFIG_RF_PARA[16:]
        nul.writeToInfo(CONFIG_BUILD_INFO,CONFIG_RF_PARA)
        nul.resetChip()
    finally:
        uiLog(u"切换至普通串口模式")
        __getIoBoard().switchToNormalSerial()
#        iob.pressDemolishButton()
#        time.sleep(1)
#        iob.releaseDemolishButton()
        time.sleep(0.5)
        sc.asynSend("ResetObu")
        sc.asynReceiveAndAssert("PowerOnSuccess")
        time.sleep(1)
    return {"低唤醒灵敏度粗调":lowWakenSensiResult[0],"低唤醒灵敏度细调":lowWakenSensiResult[1],
            "高唤醒灵敏度粗调":highWakenSensiResult[0],"高唤醒灵敏度细调":highWakenSensiResult[1]}

def T_19_staticCurrent_A(product):
    u'''静态电流测试-判断静态电流值是否在正常范围内'''
    try:
        sc = board_digital.__askForPlateDeviceCom()
        iob = __getIoBoard()
#        v = sc.testStaticCurrent()
        try:
            device = sc.bslDevice
            device.make_obu_enter_sleep()
            iob.output(GS11IOBoardDevice.UART_TX_OUTPUT,True)   #切换OBU的UART串口
            iob.output(GS11IOBoardDevice.UART_RX_OUTPUT,True)
            time.sleep(0.5)
            device.set_small_current_switch(0)
            current_val = device.read_adc_current()
            if current_val > 10:
                print "current_val=",current_val
                superUiLog("small_current_switch = 0,current_val="+str(current_val))
                raise
            device.set_small_current_switch(1)
            current_val = device.read_adc_current()
            v = sc.convertAdcToCurrent(current_val)
        finally:
            iob.output(GS11IOBoardDevice.UART_TX_OUTPUT,False)
            iob.output(GS11IOBoardDevice.UART_RX_OUTPUT,False)
            device.set_small_current_switch(0)
        resultMap = {u"静态电流":v}
        if v < SP('gs11.staticCurrent.low',2) or v > SP('gs11.staticCurrent.high',18):
            raise TestItemFailException(failWeight = 10,message = u'静态电流测试不通过，正常阈值4-18',output=resultMap)
        return resultMap
    except TestItemFailException,e:
        raise e
    except:
        raise TestItemFailException(failWeight = 10,message = u'静态电流测试失败')

def T_20_deepStaticCurrent_A(product):
    u'''深度静态电流测试-判断深度静态电流值是否在正常范围内'''    
    iob = __getIoBoard()
    sc = board_digital.__askForPlateDeviceCom()
    iob.pressDemolishButton()
#    sc.assertSynComm(request ='CloseObuUart',response = 'CloseObuUartOK')
    iob.output(GS11IOBoardDevice.UART_TX_OUTPUT,True)
    iob.output(GS11IOBoardDevice.UART_RX_OUTPUT,True)
    time.sleep(2)
    try:
        v = sc.testDeepStaticCurrent()
        resultMap = {u"深度静态电流":v}
        if v < SP('gs10.deepStaticCurrent.low',0) or v > SP('gs10.deepStaticCurrent.high',3):
            raise TestItemFailException(failWeight = 10,message = u'深度静态电流测试不通过',output=resultMap)
        return resultMap
    except TestItemFailException,e:
        raise e
    except Exception,e:
        print e
        raise TestItemFailException(failWeight = 10,message = u'深度静态电流测试失败')
    finally:
        sc.assertSynComm(request ='OpenObuUart',response = 'OpenObuUartOK')
        iob.releaseDemolishButton()    
        iob.output(GS11IOBoardDevice.UART_TX_OUTPUT,False)
        iob.output(GS11IOBoardDevice.UART_RX_OUTPUT,False)
    
    
    
    
