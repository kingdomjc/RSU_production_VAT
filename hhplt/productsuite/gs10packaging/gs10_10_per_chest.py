#encoding:utf-8
u'''
每箱10小盒进行包装
'''

suiteName = u"每箱10小盒包装"
version = "1.0"
failWeightSum = 10


from hhplt.testengine.manul import askForSomething
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.testcase import uiLog
from hhplt.testengine.server import ServerBusiness
import re

def __scan_box(product,index):
    nowBar = product.param["nowBoxBarCode"]
    boxBar = askForSomething(u"扫描条码", u"请扫描第【%d】个位置的条码\r\n应当为:%d"%(index,nowBar),autoCommit = False)
    while int(boxBar) != nowBar:
        boxBar = askForSomething(u"扫描条码", u"装配错误，应当装配的小盒条码为:%d"%nowBar,autoCommit = False)
    __checkBoxTestStatus(boxBar)
    product.param["nowBoxBarCode"] = product.param["nowBoxBarCode"] + 1
    product.addBindingCode(u"位置%d小盒条码"%index,boxBar)
    return {u"小盒条码":boxBar}

def __checkBoxTestStatus(boxBar):
    uiLog(u'检查小盒条码%s的包装情况...'%boxBar)
    with ServerBusiness(testflow = True) as sb: #这里不会混淆，因为小箱条码为18位，大箱为20位
        status = sb.getProductTestStatus(productName="GS10包装 ",idCode = boxBar)
        if status is None:
            raise AbortTestException(message=u"条码为[%s]的小盒尚未包装，请勿进行大盒包装！"%boxBar)

def T_01_scanChestBarCode_M(product):
    u'''扫描大箱条码'''
    boxBarCode = askForSomething(u"扫描条码", u"请扫描箱体条码")
    if re.match("\d{20}", boxBarCode) is None:
        raise AbortTestException(message = u'扫描盒体条码错误')
    product.param["startBarCode"] = int(boxBarCode[:18])
    product.param["num"] = int(boxBarCode[-2:])
    product.param["nowBoxBarCode"] = product.param["startBarCode"]
    product.setTestingProductIdCode(boxBarCode)

def T_02_scan_box_M(product):
    u'''扫描并检查第1个OBU小盒'''
    return __scan_box(product,1)

def T_03_scan_box_M(product):
    u'''扫描并检查第2个OBU小盒'''
    return __scan_box(product,2)

def T_04_scan_box_M(product):
    u'''扫描并检查第3个OBU小盒'''
    return __scan_box(product,3)

def T_05_scan_box_M(product):
    u'''扫描并检查第4个OBU小盒'''
    return __scan_box(product,4)

def T_06_scan_box_M(product):
    u'''扫描并检查第5个OBU小盒'''
    return __scan_box(product,5)

def T_07_scan_box_M(product):
    u'''扫描并检查第6个OBU小盒'''
    return __scan_box(product,6)

def T_08_scan_box_M(product):
    u'''扫描并检查第7个OBU小盒'''
    return __scan_box(product,7)

def T_09_scan_box_M(product):
    u'''扫描并检查第8个OBU小盒'''
    return __scan_box(product,8)

def T_10_scan_box_M(product):
    u'''扫描并检查第9个OBU小盒'''
    return __scan_box(product,9)
    
def T_11_scan_box_M(product):
    u'''扫描并检查第10个OBU小盒'''
    return __scan_box(product,10)

