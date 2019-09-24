#encoding:utf-8
u'''每小盒20个卡片进行包装，首先扫描小盒的条码，再依次扫码内装卡片的条码。
完成20个卡片的扫码或扫描下一个盒体视为一盒包装完成'''

suiteName = u'''每小盒20个包装'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.testengine.server import ServerBusiness
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.manul import askForSomething,manulCheck
from hhplt.testengine.autoTrigger import AutoTriggerOnSmoothFinish 
from hhplt.parameters import SESSION, PARAM
from hhplt.productsuite.gs15.jiangsu_card_overall import BAR_CODE_REGX as ITEM_BAR_CODE_REGX
import re
import winsound
from hhplt.testengine.testcase import uiLog
from hhplt.productsuite.gs15.jiangsu_card_overall import suiteName as OVERALL_SUITE_NAME 
import time

autoTrigger = AutoTriggerOnSmoothFinish

BOX_BAR_CODE_REGX = "\d"    #TODO 盒条码判定正则式

def __succBeep():
    '''成功的蜂鸣提示'''
    winsound.Beep(3000, 300)

def __errorBeep():
    '''异常的蜂鸣提示'''
    for i in range(3):
        winsound.Beep(3000 - i * 100, 100)
            
def __generateItemBarCodeSet(boxBarCode):
    '''计算出盒里应该有的20个个体的条码列表'''
    startCardCode = long(PARAM["gs15cardStartCode"])
    startBoxCode = long(PARAM["gs15smallBoxStartCode"])
    shouldList = []
    nowStart = (long(boxBarCode) - startBoxCode) * PARAM["gs15countPerSmallBox"] + startCardCode
    for itemCode in range(nowStart, nowStart + PARAM["gs15countPerSmallBox"]):
        shouldList.append(str(itemCode))
    return shouldList
    
def T_01_scanBoxBarCode_M(product):
    u'''扫描盒体条码-扫描盒体条码'''
    if "nextBoxBarCode" in SESSION and SESSION["nextBoxBarCode"] is not None:
        #前面已经扫描过盒体，直接开始的
        boxBarCode = SESSION["nextBoxBarCode"]
        del SESSION["nextBoxBarCode"]
    else:
        boxBarCode = askForSomething(u"扫描条码", u"请扫描盒体条码", autoCommit=False)
        while re.match(BOX_BAR_CODE_REGX, boxBarCode) is None:
            boxBarCode = askForSomething(u"扫描条码", u"条码扫描错误，请重新扫描", autoCommit=False)    
    product.setTestingProductIdCode(boxBarCode)
    product.addBindingCode(u"盒体条码",boxBarCode)
    product.param["itemBarCodeList_should"] = __generateItemBarCodeSet(boxBarCode) #理论上应该包含的个体条码集合
    product.param["itemBarCodeList_actual"] = []    #实际包含的个体条码列表
    return {u"盒体条码":boxBarCode}

def __checkTestResult(barCode):
    '''检查该条码的卡片是否经过了测试'''
    sb = ServerBusiness()
    sb.__enter__()
    try:
        idCode = sb.getProductIdByBindingCode(productName=u"GS15 超高频标签", codeName=u"条码", code=barCode)
        if idCode == None:
            return False
        status = sb.getProductTestStatus(productName=u"GS15 超高频标签" , idCode=idCode)
        if status is None:
            return False
        if OVERALL_SUITE_NAME not in status["suiteStatus"] or status["suiteStatus"][OVERALL_SUITE_NAME] != 'PASS':
            return False
        return True
    except:
        return False

def __processItemBarCode(product, barCode):
    '''处理扫描到的个体条码，返回值是是否完成及消息'''
    succOrFail = False
    msg = None
    if barCode not in product.param["itemBarCodeList_should"]:
        msg = u"该卡片不属于本盒，请勿包装。重新扫描"
        uiLog(u"扫描到条码为%s的卡片，但不属于本盒"%barCode)
    elif not __checkTestResult(barCode):
        msg = u"该卡片未完成测试或测试不通过，请勿包装。重新扫描"
        uiLog(u"扫描到条码为%s的卡片，但系统判定其未通过测试"%barCode)
    else:
        succOrFail = True
        msg = u"完成，请扫描下一张卡片"
        uiLog(u"扫描到条码为%s的卡片，检测通过"%barCode)
    
    if not succOrFail:
        __errorBeep()
        return False, msg
    else:
        if barCode not in product.param["itemBarCodeList_actual"]:
            product.param["itemBarCodeList_actual"].append(barCode)
        if len(product.param["itemBarCodeList_should"]) == len(product.param["itemBarCodeList_actual"]):
            return True, ""
        else:
            __succBeep()
            return False, msg

def __processBoxBarCode(product, barCode):
    '''扫描了下一盒的条码'''
    SESSION["nextBoxBarCode"] = barCode
    
def T_02_verifyHistoryPackaging_A(product):
    u'''判断小盒历史包装情况-自动检查该小盒的历史包装情况，如果已包装过，则本次进行补充包装'''
    idCode = product.getTestingProductIdCode()
    with ServerBusiness() as sb:
        unpackagedStr = sb.getBindingCode(productName=u"GS15卡片包装",idCode=idCode,bindingCodeName=u"未包装个体")
        if unpackagedStr == "":
            uiLog(u"%s盒为新包装"%idCode)
        else:
            if manulCheck(u"GS15包装", u"此盒[%s]已包装但有缺失，是否进行补充包装？"%idCode,check="confirm"):
                uiLog(u"%s盒已包装过，进行补充包装"%idCode)
                unpackaged = unpackagedStr.split(",")
                for item in product.param["itemBarCodeList_should"]:
                    if item not in unpackaged:
                        product.param["itemBarCodeList_actual"].append(item)
            else:
                uiLog(u"%s盒重新进行包装"%idCode)

def T_03_scanItemOrNextBoxBarCode_M(product):
    u'''扫描个体条码-依次扫描20个体条码，如果完成，请扫描下一盒的盒体条码'''
    boxBarCode = product.getTestingProductIdCode()
    message = u"装箱:%s\n请扫描卡片条码。装完后扫描下一盒的条码。输入ok终止。"%boxBarCode
    while True:
        barCode = askForSomething(u"扫描条码", message , autoCommit=False)
        if re.match(ITEM_BAR_CODE_REGX, barCode) is not None:
            brk, message = __processItemBarCode(product, barCode)
            if brk:break
        elif re.match(BOX_BAR_CODE_REGX, barCode) is not None:
            __processBoxBarCode(product, barCode)
            break
        elif barCode.lower() == 'ok':
            break
        else:
            message = u"条码扫描错误，请重新扫描"

def __recordUnpackagedItems(product):
    '''记录未包装的个体，返回已包装和未包装的列表'''
    itemBarCodeList_should = product.param["itemBarCodeList_should"]
    itemBarCodeList_actual = product.param["itemBarCodeList_actual"]
    packaged = []
    unpackaged = []
    for item in itemBarCodeList_should:
        if item in itemBarCodeList_actual:
            packaged.append(item)
        else:
            unpackaged.append(item)
    if len(unpackaged)!= 0:
        product.addBindingCode(u"未包装个体",",".join(unpackaged))
    return packaged, unpackaged

def __recordUnpackagedItemsToLocalFile(boxBarCode,unpackagedList):
    '''记录未包装的卡片到本地文件'''
    f = open("unpackagedCards_%s.txt"%(time.strftime('%Y-%m-%d',time.localtime(time.time()))),"a")
    for item in unpackagedList:
        f.write("卡片条码:%s\t所属小盒条码:%s\n"%(item,boxBarCode))
    f.close()

def T_04_processBoxPackaging_A(product):
    u'''记录装箱情况-个体扫描完成后，判定装箱情况'''
    if len(product.param["itemBarCodeList_should"]) == len(product.param["itemBarCodeList_actual"]):
        #完成20个的扫描了
        return {u"包装完成情况":u"完成", u"已包装个体":",".join(product.param["itemBarCodeList_actual"])}
    else:
        packaged, unpackaged = __recordUnpackagedItems(product)
        __recordUnpackagedItemsToLocalFile(product.getTestingProductIdCode(),unpackaged)
        raise TestItemFailException(failWeight=10, message=u'包装不完整',
                                    output={u"包装完成情况":u"未完成",
                                            u"已包装个体":",".join(packaged),
                                            u"未包装个体":",".join(unpackaged)
                                            })

def finalFun(product):
    '''收尾函数，如果正常完成了包装，则删除可能曾经存在的未完成绑定码'''
    if product.finishSmoothly and product.testResult:
        with ServerBusiness() as sb:
            sb.unbindCode(productName=u"GS15卡片包装",idCode=product.getTestingProductIdCode(),bindingCodeName=u"未包装个体")

    

