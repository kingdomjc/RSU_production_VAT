#encoding:utf-8
u"""CPC初始化
"""
import time

from hhplt.deviceresource import askForResource, retrieveAllResource
from hhplt.parameters import PARAM
from hhplt.productsuite.CPC.CpcMissingDbHelper import CpcMissingDbHelper
from hhplt.productsuite.CPC.macutil import transCpcIdToMac
from hhplt.productsuite.CPC.main_cpc_update import cpc_update_startup
from hhplt.testengine.exceptions import AbortTestException, TestItemFailException
from hhplt.testengine.manul import askForSomething
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.testutil import multipleTestCase

suiteName = u"CPC初始化"
version = "1.0"
failWeightSum = 10

from esam_erease_wenxin import *

missingDbHelper = None

def setup(product):
    OPEN_READER("USB") # open reader

def finalFun(product):
    CLOSE_READER()

def rollback(product):
    pass

def T_01_readCpcId_A(product):
    u"读取CPCID-尝试读取CPCID"
    global defaultkey
    global defaultkey_Hex
    global cpc_sn
    global cpc_id
    global area_code
    global new_sysinfo
    # **** get CPC SN
    OPEN_HFCARD() # open CPC card

    cmd_get_SN = "80F6000304"
    cpc_sn = HFCARD_COMMAND(cmd_get_SN)
    uiLog("CPC_SN: " + cpc_sn)

    # get default master key
    delivery_or_not = 0
    input_defaultkey = PARAM["masterKey"]
    input_issue_info = PARAM["issuerId"]

    if delivery_or_not == 0:
        defaultkey = input_defaultkey
        defaultkey_Hex = str_to_hex(defaultkey)
    else:
        input_defaultkey_Hex = str_to_hex(input_defaultkey)
        delivery_factor_str = cpc_sn + cpc_sn
        delivery_factor_1 = str_to_hex(delivery_factor_str)
        delivery_factor_2 = [(0xff - d) for d in delivery_factor_1]
        delivery_factor = delivery_factor_1 + delivery_factor_2
        defaultkey_Hex = sm4_crypt_ecb(ENCRYPT, input_defaultkey_Hex, delivery_factor)
        defaultkey = hexlist_to_str(defaultkey_Hex)

    ##**** get current issue_info and CPC ID
    cmd_get_sysinfo = "00b081001e"
    try:
        get_sysinfo = HFCARD_COMMAND(cmd_get_sysinfo)
    except StandardError,e:
        raise TestItemFailException(10,message=u"读CPCID失败:%s"%str(e))

    uiLog( "get_sysinfo: " + get_sysinfo)
    current_issue_info = get_sysinfo[0:16]
    uiLog("current_issue_info: " + current_issue_info)
    current_cpc_id = get_sysinfo[16:32]
    uiLog("current_cpc_id: " + current_cpc_id)

    # if not update issue_info
    if input_issue_info == '':
        new_sysinfo = get_sysinfo
    else:
        # *** get new CPC ID
        new_issue_info = input_issue_info
        uiLog("new_issue_info: " + new_issue_info)
        new_sysinfo = new_issue_info + get_sysinfo[16:]
    new_cpc_id = current_cpc_id
    # area_code
    area_code = new_sysinfo[0:8]
    # cpc_id
    cpc_id = new_cpc_id
    product.setTestingProductIdCode(cpc_id )


def T_02_manuallyAddCpcId_M(product):
    u"手动输入CPCID-对于无法读取CPCID的标签，手动输入之"
    global defaultkey
    global defaultkey_Hex
    global cpc_sn
    global cpc_id
    global area_code
    global new_sysinfo
    cpcId = askForSomething(u"手动CPCID",u"请输入CPCID",defaultValue="",autoCommit=False)
    cpc_id = cpcId
    uiLog("CPC_ID: " + cpc_id  )
    product.setTestingProductIdCode(cpc_id )

def T_03_recreate_A(product):
    u"擦除ESAM-擦除ESAM"
    try:
        cpc_esam_recreate()
    except StandardError,e:
        import traceback
        print traceback.format_exc()
        raise TestItemFailException(10,message=u"CPC擦除失败:%s"%str(e))


def T_04_update_A(product):
    u"卡片发行-卡片发行"
    try:
        OPEN_HFCARD() # open CPC card
        time.sleep(0.5)
        ##*** excute cpc update
        cpc_card_update()
    except StandardError,e:
        raise TestItemFailException(10,message=u"CPC发行失败:%s"%str(e))

def T_05_checkCpcId_A(product):
    u"检查CPCID-检查CPCID发行是否成功"
    HFCARD_COMMAND('00a40000023f00')
    cmd_get_sysinfo = "00b081001e"
    try:
        after_system = HFCARD_COMMAND(cmd_get_sysinfo)
    except StandardError,e:
        raise TestItemFailException(10,message=u"读CPCID失败:%s"%str(e))
    after_new_cpcid = after_system[16:32]
    if after_new_cpcid != cpc_id:
        raise TestItemFailException(10,message=u"CPCID验证错误,%s,%s"%(after_new_cpcid,cpc_id))
