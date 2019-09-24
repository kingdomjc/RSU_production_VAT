#encoding:utf-8
'''
Created on 2014-8-18
人工干预测试的工具

包括需要人工确认、提示信息等的工具，在测试流程中调用
@author: 张文硕
'''

from hhplt.parameters import GLOBAL
from PyQt4.QtCore import SIGNAL
import time

def manulCheck(title,content,check="check"):
    '''人工检查，返回true/false'''
    #check = ok    只显示OK按钮，
    #check = confirm    显示是/否按钮
    #check = check    显示正常/不正常按钮
    GLOBAL["mainWnd"].emit(SIGNAL("MANUL_CHECK(QString,QString,QString)"),title, content,check)
    return GLOBAL["mainWnd"].waitForManulCheckDlg() == 0

def askForSomething(title,content,defaultValue = "",autoCommit = True):
    '''请求信息，返回请求到的信息。参数中，如果autoCommit==True，则开启自动扫码枪头，否则可以键盘输入或者手动扫码枪输入
    如果defaultValue != None，则填入初始值'''
    import hhplt.ui.askForSomethingDlg as askForSomethingDlg
    askForSomethingDlg.autoCommit = autoCommit
    GLOBAL["mainWnd"].emit(SIGNAL("ASK_FOR_SOMETHING(QString,QString,QString)"),title, content,str(defaultValue))
    return GLOBAL["mainWnd"].waitForSomething()

def showAsynMessage(title,content):
    '''显示异步提示消息，不卡住流程线程'''
    GLOBAL["mainWnd"].emit(SIGNAL("ASYN_MESSAGE(QString,QString)"),title, content)

def closeAsynMessage():
    '''关闭消息'''
    GLOBAL["mainWnd"].emit(SIGNAL("CLOSE_MESSAGE()"))

def autoCloseAsynMessage(title,content,verifyFun,exception=None,timeout = 10):
    occurExcept = None
    for i in range(timeout):
        time.sleep(0.5)
        showAsynMessage(title,content)
        try:
            if verifyFun():
                closeAsynMessage()
                break
        except Exception,e:
            occurExcept = e
    else:
        closeAsynMessage()
        if occurExcept is not None:
            raise occurExcept
        elif exception is not None:
            raise exception
    
    
def broadcastTestResult(product):
    '''大提示的测试结果'''
    if product.finishSmoothly and product.testResult:
        showAsynMessage(u"刚刚完成的测试结果", u"<font color=green>测试通过</font>");
    else:
        showAsynMessage(u"刚刚完成的测试结果", u"<font color=red>NG</font><br/>" + ("<br/>".join(product.failReasonMessage)));


def showDashboardMessage(message):
    '''显示公告'''
    GLOBAL["mainWnd"].emit(SIGNAL("SHOW_DASH_BOARD_MESSAGE(QString)"),message)


