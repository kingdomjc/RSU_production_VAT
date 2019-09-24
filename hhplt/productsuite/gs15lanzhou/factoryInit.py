#encoding:utf-8
u'''GS15兰州电子车牌成品测试及出厂初始化
单纯完成测试和初始化，没有与镭雕机联动。用于小批量发货及补充测试。'''

suiteName = u'''GS15兰州电子车牌成品测试及出厂初始化'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过

from hhplt.testengine.manul import askForSomething,showDashboardMessage,autoCloseAsynMessage
from hhplt.parameters import PARAM,SESSION
from hhplt.productsuite.generaluhf import uhf_card_overall,uhf_card_board,uhf_card_overall_with_serial_carving
from hhplt.testengine.exceptions import TestItemFailException
from hhplt.testengine.localdb import writeProductToLocalDb

__getReader = uhf_card_board.__getReader
__getLaserCaving = uhf_card_overall_with_serial_carving.__getLaserCaving

autoTrigger = uhf_card_overall.autoTrigger
setup = uhf_card_overall.setup

def finalFun(product):
    if product.finishSmoothly and product.testResult:
        #正常完成，则递增镭雕序列号
        oldC = product.param["PID"][2:]
        PARAM["carvingCode"] = ("%."+str(len(oldC))+"d") % (int(oldC)+1)
        PARAM.dumpParameterToLocalFile()
        writeProductToLocalDb(product) #保存到本地数据库
    uhf_card_overall.finalFun(product)
        
def rollback(product):
    uhf_card_overall.rollback(product)
    
def T_01_inventoryTagAndTid_A(product):
    u'''清点标签并读取TID-测试标签可被清点到，并确保只有一个标签在测'''
    res = uhf_card_overall.T_01_inventoryTagAndTid_A(product)
    SESSION["autoTrigger"].nowEpc = res["EPC"]
    return res

def T_02_checkAndChangeToPrivateMode_A(product):
    u'''转到私有EPC模式下-检查标签是否处于私有模式，否则转入私有模式'''
    if not __getReader().qtToPrivate():
        raise TestItemFailException(failWeight = 10,message = u'转换到私有EPC模式失败')  

def T_03_testWriteUser_A(product):
    u'''USER区读写测试-清零USER区'''
    uhf_card_board.__writeReadwriteUser("0"*(PARAM["gs15userLength"]*4))

def T_04_clearKillPasswordAndLock_A(product):
    u'''清空KillPassword并永久锁定-将杀死密码区置为0并永久锁定'''
    reader = __getReader()
    if reader.getKillPassword() != '00000000':
        reader.clearKillPassword()
    res = reader.permanentLockKillPassword()  #在复测的时候，此已经锁了，所以这里不管它的返回值
    
def T_05_initPublicEpc_A(product):
    u'''初始化公有EPC区-公有EPC映射TID.6.6写入PID值并补齐0'''
    pid = PARAM["manufacturerId"]+PARAM["carvingCode"]  #生成PID，等最后都成功了，PID再递增
#    pid = askForSomething(u"确定写入的PID", u"请检查并输入卡面镭雕的PID",autoCommit=False,defaultValue=pid)
    boxId = PARAM["manufacturerId"] + "%.5d"%((int(pid[2:])-1)/PARAM["amountPerBox"] + 1)
    showDashboardMessage("当前测试的卡片PID:%s\n当前包装盒号：%s"%(pid,boxId))
    product.addBindingCode("PID",pid)
    product.param["PID"] = pid
    product.param["initEpc"] = pid+"0"*(24-len(pid))
    product.addBindingCode("EPC",product.param["initEpc"])
    __getReader().writeToTid(product.param["initEpc"],6)
    
    return {"PID":pid,u"出厂公有EPC":product.param["initEpc"]}
    
def T_06_changeToPublicModeAndInventory_A(product):
    u'''检查公有EPC清点-转入公有模式并进行清点，检查公有EPC初始化是否成功'''
    reader = __getReader()
    if not reader.qtToPublic():
        raise TestItemFailException(failWeight = 10,message = u'转换到公有EPC模式失败')  
    if reader.nowEpc[0] != product.param["initEpc"]:
        raise TestItemFailException(failWeight = 10,message = u'公有EPC写入失败')  
    
def T_07_changeToPrivateMode_A(product):
    u'''私有EPC写入测试-转入私有EPC模式并写入EPC'''
    reader = __getReader()
    if not reader.qtToPrivate():
        raise TestItemFailException(failWeight = 10,message = u'转换到私有EPC模式失败') 
    reader.writeToEpc(product.param["initEpc"])
    invRes = reader.inventory()
    if len(invRes)!=1 or invRes[0] != product.param["initEpc"]:
        raise TestItemFailException(failWeight = 10,message = u'私有EPC写入失败')
    SESSION["autoTrigger"].nowEpc = product.param["initEpc"]
    return {u"出厂私有EPC":product.param["initEpc"]}

def T_08_laserCarve_M(product):
    u'''镭雕卡面编号-自动镭雕卡面顺序编号'''
    carvingCode = product.param["PID"]
    __getLaserCaving().toCarveCode(carvingCode)
    try:
        autoCloseAsynMessage(u"操作提示（提示框会自动关闭）",u"当前镭雕号:%s,请踩下踏板进行镭雕"%carvingCode,
                                 lambda:__getLaserCaving().carved()
                                ,TestItemFailException(failWeight = 10,message = u'镭雕机未响应'))
    except TestItemFailException,e:
        __getLaserCaving().clearCarveCode()
        raise e
    product.addBindingCode(u"卡面镭雕编码",carvingCode)
    return {u"卡面镭雕编码":carvingCode}



