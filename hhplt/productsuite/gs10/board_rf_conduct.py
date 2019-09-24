#encoding:utf-8
u'''单板射频工位测试项（传导方式）\n请将带缺口的射频卡插入OBU，并放入夹具中。'''


suiteName = u'''单板射频工位测试项-传导方式'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

import os
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.server import serverParam as SP
from hhplt.testengine.manul import manulCheck,closeAsynMessage,autoCloseAsynMessage
from hhplt.productsuite.gs10.board_digital import __askForPlateDeviceCom
from hhplt.parameters import SESSION
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.server import ServerBusiness

import time

passwordFile = os.path.dirname(os.path.abspath(__file__))+os.sep+"versions\\obu-vat.txt"


def __checkDigitalCheckFinished(idCode):
    '''检查数字工位已完成'''
    with ServerBusiness(testflow = True) as sb:
        status = sb.getProductTestStatus(productName="GS10 OBU" ,idCode = idCode)
        if status is None:
            raise AbortTestException(message=u"该产品尚未进行数字工位测试，射频测试终止")

def setup(product):
    '''准备函数，获取MAC地址'''
    if SESSION["isMend"]:
        return  #维修测试不需要读MAC
    uiLog(u"正在读取产品标识...")
    sc = __askForPlateDeviceCom()
    try:
        macBytes = sc.read_obu_id(passwordFile)
        mac = "".join(["%.2X"%i for i in macBytes])
        product.setTestingProductIdCode(mac)
        uiLog(u"测试产品标识:"+mac)
        __checkDigitalCheckFinished(mac)
    except Exception,e:
        print e
        raise AbortTestException(message = u'BSL方式读取产品标识失败:'+e.message)
    finally:
        time.sleep(1)
        sc.clearSerialBuffer()

def T_01_readRfCard_A(product):
    u'''读高频卡测试-读高频卡测试'''
    testTimes = SP('gs10.testHf.number',5)   #测试次数
    sc = __askForPlateDeviceCom()
    sc.assertSynComm(request ='TestHF %d'%testTimes,response = 'TestHFOK')
    
def T_02_wakeupSensitivity_A(product):
    u'''唤醒灵敏度测试-判断高低灵敏度是否满足标准'''
    low_level_power = SP('gs10.wakeup.power.low',-40)   #低唤醒功率
    high_level_power = SP('gs10.wakeup.power.high',-42) #高唤醒功率
   
    sc = __askForPlateDeviceCom()
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
    
    #写入灵敏度值
    print u"开始写入灵敏度"
    try:
        sc.startBslWriting(passwordFile)
        sc.save_waken_sensi(lowWakenSensiResult[0],lowWakenSensiResult[1],highWakenSensiResult[0],highWakenSensiResult[1])
    except Exception,e:
        print e
        raise TestItemFailException(failWeight = 10,message = u'唤醒灵敏度写入失败')
    finally:
        sc.finishBslWritten()
        time.sleep(1)
        sc.clearSerialBuffer()
    return {"低唤醒灵敏度粗调":lowWakenSensiResult[0],"低唤醒灵敏度细调":lowWakenSensiResult[1],
            "高唤醒灵敏度粗调":highWakenSensiResult[0],"高唤醒灵敏度细调":highWakenSensiResult[1]}

def T_03_receiveSensitivity_A(product):
    u'''接收灵敏度测试-判断接收灵敏度是否满足标准'''
    power_db = SP('gs10.receiveSensitivity.power',-48)
    frame_num = SP('gs10.receiveSensitivity.frameNum',500)   #发送帧总数
    frame_scope_high = SP('gs10.receiveSensitivity.frameBorder',485) #帧数阈值
    
    try:
        resultMap = {}
        sc = __askForPlateDeviceCom()
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

def T_04_transmittingPower_A(product):
    u'''发射功率测试-判断发射功率'''
    power_border_low = SP('gs10.sendPower.low',-3.5)
    power_border_high = SP('gs10.sendPower.high',5)
    try:
        sc = __askForPlateDeviceCom()
        v = sc.getObuSendPower()
        resultMap = {u"发射功率":v}
        if v < power_border_low or v > power_border_high:
            raise TestItemFailException(failWeight = 10,message = u'发射功率异常',output=resultMap)
        return resultMap
    except TestItemFailException,e:
        raise e
    except:
        raise TestItemFailException(failWeight = 10,message = u'发射功率测试失败')

def T_05_staticCurrent_A(product):
    u'''静态电流测试-判断静态电流值是否在正常范围内'''
    try:
        sc = __askForPlateDeviceCom()
        v = sc.testStaticCurrent()
        resultMap = {u"静态电流":v}
        if v < SP('gs10.staticCurrent.low',4) or v > SP('gs10.staticCurrent.high',18):
            raise TestItemFailException(failWeight = 10,message = u'静态电流测试不通过，正常阈值4-18',output=resultMap)
        return resultMap
    except TestItemFailException,e:
        raise e
    except:
        raise TestItemFailException(failWeight = 10,message = u'静态电流测试失败')

def T_06_deepStaticCurrent_A(product):
    u'''深度静态电流测试-判断深度静态电流值是否在正常范围内'''
    manulCheck(u"操作提示",u"请按住防拆下电按钮，使其下电","ok")
    sc = __askForPlateDeviceCom()
    sc.assertSynComm(request ='CloseObuUart',response = 'CloseObuUartOK')
    time.sleep(2)
    try:
        v = sc.testDeepStaticCurrent()
        resultMap = {u"深度静态电流":v}
        if v < SP('gs10.deepStaticCurrent.low',0) or v > SP('gs10.deepStaticCurrent.high',3):
            raise TestItemFailException(failWeight = 10,message = u'深度静态电流测试不通过，正常阈值0-3',output=resultMap)
        return resultMap
    except TestItemFailException,e:
        raise e
    except:
        raise TestItemFailException(failWeight = 10,message = u'深度静态电流测试失败')
    finally:
        closeAsynMessage()
        sc.assertSynComm(request ='OpenObuUart',response = 'OpenObuUartOK')
    
    
#def T_07_disturbOn14k_M(product):
#    u'''5.8G芯片上电14k干扰测试-上电时发送14k，检查干扰是否造成混乱'''
#    sc = __askForPlateDeviceCom()
#    time.sleep(1)
#    autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"请按住防拆下电按键!",
#                         lambda:not time.sleep(1))
#    sc.asynSend('EtSend14k 3000')
#    autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"请松开防拆下电按键!",
#                         lambda:not time.sleep(1))
#    time.sleep(1)
#    res = sc.asynReceive()
#    uiLog(u"串口接收:%s"%(res))
#    time.sleep(1)
#    sc.clearSerialBuffer()
#    target_power = -35    
#    sc.bslDevice.calibra_target_power(target_power)
#    if not sc.bslDevice.test_if_obu_wakeup():
#        raise TestItemFailException(failWeight = 10,message = u'5.8G芯片14k干扰测试不通过!')
