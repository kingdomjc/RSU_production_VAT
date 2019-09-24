#encoding:utf-8
u'''
CPC卡片版本下载，并写入MAC地址和其他信息
'''
from hhplt.productsuite.CPC.macutil import transCpcIdToMac
from hhplt.testengine.autoTrigger import AutoStartStopTrigger
from hhplt.testengine.exceptions import TestItemFailException
import sky6610s_main_V01 as SKS

suiteName = u"CPC卡片版本下载"
version = "1.0"
failWeightSum = 10



from hhplt.productsuite.CPC.cpcMacMaintancePool import CpcMacMaintancePool
from hhplt.testengine.localdb import writeProductToLocalDb
from hhplt.testengine.manul import manulCheck, askForSomething
from hhplt.testengine.testcase import uiLog

MAC_POOL = None


#autoTrigger =  AutoStartStopTrigger




def setup(product):
    if SKS.ser is None:SKS.openSerial()

def finalFun(product):
    pass
    #writeProductToLocalDb(product,"cpcCard.db")
    #if product.testResult :MAC_POOL.dumpToParam()

def rollback(product):
    # if MAC_POOL is not None:
    #     MAC_POOL.withdrawCurrentMac()
    #     uiLog(u"回收MAC地址:"+product.getTestingProductIdCode())
    pass

# def _____T_01_determineMacRange_A(product):
#     u"确定MAC地址范围-首次测试时确定MAC地址范围，后续自动累加"
#     global MAC_POOL
#     if MAC_POOL is None:
#         if manulCheck(u"确定MAC范围",u'''已设定的MAC范围是【%s】至【%s】\n当前MAC是【%s】，是否修改？'''%\
#                 (PARAM["startMac"],PARAM["endMac"],PARAM["currentMac"]),check="confirm"):
#             startMac = askForSomething(u"确定起始MAC地址", u"请输入起始MAC地址，4字节（8个HEX符号）",autoCommit=False,defaultValue = PARAM["startMac"])
#             endMac = askForSomething(u"确定结束MAC地址", u"请输入结束MAC地址，4字节（8个HEX符号）",autoCommit=False,defaultValue = PARAM["endMac"])
#             currentMac = startMac
#             PARAM["startMac"] = startMac
#             PARAM["endMac"] = endMac
#             PARAM["currentMac"] = currentMac
#             PARAM.dumpParameterToLocalFile()
#         else:
#             startMac,endMac,currentMac = PARAM["startMac"],PARAM["endMac"],PARAM["currentMac"]
#         MAC_POOL = CpcMacMaintancePool((startMac,endMac),currentMac)
#         uiLog(u"已确定本次测试MAC范围：【%s】至【%s】"%(PARAM["startMac"],PARAM["endMac"]))
#
#     currentMac = MAC_POOL.fetchAndSwitchToNextMac()
#     uiLog(u"当前MAC是【%s】"%currentMac)
#     manulCheck(u"开始写入MAC",u"请确认插好CPC单板，即将写入MAC:\n%s"%currentMac,check="ok")
#     product.setTestingProductIdCode(currentMac)
#     product.addBindingCode(u"MAC",currentMac)
#     return {"MAC":currentMac}

def T_01_downloadTestVersion_A(product):
    u"测试版本下载-自动下载CPC卡片测试版本"
    SKS.switchMode("VER")
    SKS.download(verCmd="ef")

    readdata = SKS.revdata(10)#读取回复
    print "<",readdata
    if SKS.RSP_CMD_OK in readdata:#收到命令格式正确的回复
        #readdata = ''
        #readdata = SKS.revdata(50)#读取回复
        resDataHex = SKS.hexShow(readdata)
        uiLog(u"版本下载:" + resDataHex )
        if SKS.RSP_FINISH in readdata:#执行完成回复码
            return {u"版本下载返回":resDataHex}
        raise TestItemFailException(failWeight = 10,message = u'版本下载失败')
    else:
        raise TestItemFailException(failWeight = 10,message = u'版本下载失败')

def T_02_readCpcId_A(product):
    u"读取CPCID-读取卡片的CPCID并据此生成MAC"
    SKS.switchMode("CPC")
    #SKS.resetChip()
    uiLog(u"切换到CPC读取模式")

    cpcId,sn = SKS.readCpcIdAndSn()
    if cpcId is None:
        raise TestItemFailException(failWeight = 10,message = u'读取CPCID失败')
    mac = transCpcIdToMac(cpcId)
    uiLog(u"读取到CPCID:%s，SN:%s，生成MAC:%s"%(cpcId,sn,mac))

    product.setTestingProductIdCode(cpcId)
    product.param["mac"] = mac
    product.param["sn"] = sn
    return {"cpcId":cpcId,"sn":sn,"mac":mac}


def T_03_writeMac_A(product):
    u"写入MAC地址-写入MAC地址"
    SKS.switchMode("VER")
    #SKS.resetChip()
    uiLog(u"切换到版本下载模式")

    macid =product.param["mac"]
    try:
        SKS.Senddataadd0(SKS.write_cmd, macid)
        readdata = ''
        readdata = SKS.revdata(10) #读取回复
        resDataHex = SKS.hexShow(readdata)
        if SKS.RSP_FINISH in readdata: #执行完成回复码
            uiLog(u"地址0x40000配置成功"+resDataHex)
            uiLog(u"写入MAC地址成功:"+product.param["mac"])
        else:
            raise TestItemFailException(failWeight = 10,message = u"地址0x40000配置失败"+resDataHex)
    except TestItemFailException,e:
        raise e
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'写入MAC失败:'+str(e))

def T_04_writeOtherData_A(product):
    u"写入片内其他数据-配置地址0x40000,0x40080,0x40040的出厂数据"
    try:
        SKS.Senddataadd1(SKS.write_cmd, chr(0x00))
        print u"地址0x40080写入数据："
        readdata = ''
        readdata = SKS.revdata(10)#读取回复
        resDataHex = SKS.hexShow(readdata)
        if SKS.RSP_FINISH in readdata:#执行完成回复码
            uiLog(u"地址0x40080配置成功"+resDataHex)
        else:
            raise TestItemFailException(failWeight = 10,message = u'地址0x40080配置失败'+resDataHex)

        SKS.Senddataadd2(SKS.write_cmd, chr(0x00))
        readdata = ''
        readdata = SKS.revdata(10)#读取回复
        resDataHex = SKS.hexShow(readdata)
        if SKS.RSP_FINISH in readdata:#执行完成回复码
            uiLog(u"地址0x40040配置成功"+resDataHex)
        else:
            raise TestItemFailException(failWeight = 10,message = u'地址0x40040配置失败'+resDataHex)
    except TestItemFailException,e:
        raise e
    except Exception,e:
        raise TestItemFailException(failWeight = 10,message = u'写入内存区失败:'+str(e))

def T_05_downloadFormalVersion_A(product):
    u"正式版本下载-自动下载CPC卡片正式版本"
    SKS.download(verCmd="ee")
    readdata = SKS.revdata(10)#读取回复
    if SKS.RSP_CMD_OK in readdata:#收到命令格式正确的回复
        readdata = ''
        readdata = SKS.revdata(50)#读取回复
        resDataHex = SKS.hexShow(readdata)
        uiLog(u"版本下载:" + resDataHex )
        if SKS.RSP_FINISH in readdata:#执行完成回复码
            return {u"版本下载返回":resDataHex}
        raise TestItemFailException(failWeight = 10,message = u'版本下载失败')
    else:
        raise TestItemFailException(failWeight = 10,message = u'版本下载失败')
