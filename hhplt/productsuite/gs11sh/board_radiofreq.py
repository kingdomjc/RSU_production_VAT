#encoding:utf-8
u"单板射频测试\n串行测试六个单板的射频功能"

suiteName = u'''单板射频测试'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

import time
from hhplt.parameters import SESSION,PARAM
from hhplt.testengine.parallelTestSynAnnotation import syntest,serialSuite
from hhplt.deviceresource import askForResource,GS10PlateDevice
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.server import serverParam as SP,serialCode, ServerBusiness
from hhplt.testengine.testutil import  multipleTestCase
from hhplt.testengine.testcase import uiLog
from hhplt.productsuite.gs11sh.BoardIOController import BoardFreqIOControllerAutoTrigger, BoardFreqIOController
import util

__askForPlateDeviceCom = lambda slot:askForResource('GS10PlateDevice-slot%s'%slot, GS10PlateDevice.GS10PlateDevice,
               serialPortName =  PARAM["gs10PlateDeviceCom-slot%s"%slot],
               cableComsuption = PARAM["cableComsuption"])

autoTrigger = BoardFreqIOControllerAutoTrigger

finishedTestSlots = 0

@serialSuite
def setup(product):
    iob = askForResource("BoardFreqIOController", BoardFreqIOController)
    if iob.currentState != BoardFreqIOController.STATE_TESTING: iob.startTesting()
    r = __askForPlateDeviceCom(product.productSlot).sendAndGet("PowerOnObu")
    if r == 'PowerOnObuFail':
        raise AbortTestException(message = u'上电电流过大，请立即抬起夹具，测试终止。')
    time.sleep(1)

@serialSuite
def finalFun(product):
    __askForPlateDeviceCom(product.productSlot).asynSend("PowerOffObu")
    global finishedTestSlots
    finishedTestSlots += 1
    if finishedTestSlots  == len(PARAM["productSlots"].split(",")):
        finishedTestSlots = 0
        askForResource("BoardFreqIOController", BoardFreqIOController).stopTesting()


# def T_00_mock_M(product):
#     u"单纯调夹具-无任何测试内容"
#     return


def T_01_readMacAndCheckBoard_M(product):
    u"MAC检查-读取OBU的MAC并检查单板数字是否测试通过"
    r = __askForPlateDeviceCom(product.productSlot).sendAndGet("D-ReadFlashPara 0x02 0x00 0x10").strip()
    if not r.startswith("D-ReadFlashOK"):raise AbortTestException(message=u"读取OBU的MAC地址失败")
    obuFlash = util.cmdFormatToHexStr(r[14:])
    obuid = obuFlash[8:16]
    uiLog(u"读取到OBUID:"+obuid)
    return {"obumac":obuid}
    if obuid == "ffffffff":raise AbortTestException(message=u"单板未写入MAC，请退回单板数字测试工位")
    with ServerBusiness(testflow = True) as sb:
        status = sb.getProductTestStatus(productName="GS11 OBU")
        if status is None:raise AbortTestException(message=u"单板未进行数字测试，请退回单板数字测试工位")

@multipleTestCase(times=3)
def T_02_transmittingPower_A(product):
    u'发射功率测试-判断发射功率是否在阈值范围内'
    power_border_low = PARAM['gs11.sendPower.low']
    power_border_high = PARAM['gs11.sendPower.high']
    uiLog(u"功率判定阈值要求:%.2f-%.2f"%(power_border_low,power_border_high))
    try:
        sc = __askForPlateDeviceCom(product.productSlot)
        v = sc.getObuSendPower()
        resultMap = {u"发射功率":v}
        if v < power_border_low or v > power_border_high:
            raise TestItemFailException(failWeight = 10,message = u'发射功率异常,值%.2f，正常阈值:%.2f-%.2f'%(v,power_border_low,power_border_high)
                                        ,output=resultMap)
        return resultMap
    except TestItemFailException,e:
        raise e
    except:
        raise TestItemFailException(failWeight = 10,message = u'发射功率测试失败')

@multipleTestCase(times=3)
def T_03_receiveSensitivity_A(product):
    u'接收灵敏度测试-判断接收灵敏度是否满足标准'
    frame_num = SP('gs11.receiveSensitivity.frameNum',500,int)   #发送帧总数
    frame_scope_high = SP('gs11.receiveSensitivity.frameBorder',485,int) #帧数阈值
    power_db = PARAM['gs11.receiveSensitivity.power']
    uiLog(u"数据测试发射功率:%.2f"%power_db)
    try:
        resultMap = {}
        sc = __askForPlateDeviceCom(product.productSlot)
        v = sc.testObuRecvSensi(power_db,frame_num)
        resultMap[u"功率%d唤醒次数"%power_db]=v;
        uiLog(u"功率值:%d，唤醒次数:%d"%(power_db,v))
        if v < frame_scope_high:
            raise TestItemFailException(failWeight = 10,message = u'功率%d接收灵敏度测试不通过，正常值大于485'%power_db,output=resultMap)
        return resultMap
    except TestItemFailException,e:
        raise e
    except Exception,e:
        print e
        raise TestItemFailException(failWeight = 10,message = u'接收灵敏度测试失败')
    finally:
        time.sleep(1)

def T_04_wakeupSensitivity_A(product):
    u'唤醒灵敏度测试-判断高低灵敏度是否满足标准，校准值写入OBU'
    low_level_power = PARAM['gs11.wakeup.power.low']   #低唤醒功率
    high_level_power = PARAM['gs11.wakeup.power.high'] #高唤醒功率
    uiLog(u"唤醒功率范围：%.2f-%.2f"%(low_level_power,high_level_power))
    sc = __askForPlateDeviceCom(product.productSlot)
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
    uiLog(u"TODO 开始写入灵敏度值")

    pb = __askForPlateDeviceCom(product.productSlot)
    r = pb.sendAndGet("D-ReadFlashPara 0x02 0x40 0x0d")
    if not r.startswith("D-ReadFlashOK"): raise AbortTestException(message=u"读取OBU的灵敏度信息失败")
    obuFlash = util.cmdFormatToHexStr(r[14:])
    uiLog(u"OBU原灵敏度储存（Flash）信息:"+obuFlash)
    toWriteSensiCmd = "D-WriteFlashPara 0x05 0x44 0x%.2x 0x%.2x 0x%.2x 0x%.2x"%(highWakenSensiResult[0],highWakenSensiResult[1],
                                           lowWakenSensiResult[0],lowWakenSensiResult[1])
    r = pb.sendAndGet(toWriteSensiCmd)
    if not r.startswith("D-WriteFlashOK"):raise AbortTestException(message=u"写入OBU灵敏度信息失败")

    targetFlash = obuFlash[:8]+"%.2x%.2x%.2x%.2x"%(highWakenSensiResult[0],highWakenSensiResult[1],
                                           lowWakenSensiResult[0],lowWakenSensiResult[1])  + obuFlash[16:]


    r = pb.sendAndGet("D-ReadFlashPara 0x02 0x40 0x0d")
    if not r.startswith("D-ReadFlashOK"): raise AbortTestException(message=u"读取OBU的灵敏度信息失败")
    obuFlash = util.cmdFormatToHexStr(r[14:])
    uiLog(u"写入灵敏度后的OBU储存（Flash）信息:"+obuFlash)
    if obuFlash!=targetFlash:raise AbortTestException(message=u"写入OBU灵敏度信息失败")

    
    return {"低唤醒灵敏度粗调":lowWakenSensiResult[0],"低唤醒灵敏度细调":lowWakenSensiResult[1],
            "高唤醒灵敏度粗调":highWakenSensiResult[0],"高唤醒灵敏度细调":highWakenSensiResult[1]}
    
    
    
    
    
    