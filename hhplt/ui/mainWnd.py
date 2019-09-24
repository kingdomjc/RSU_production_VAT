#encoding:utf-8
'''
Created on 2014-8-14
主窗口
@author: 张文硕
'''
import json

from PyQt4.QtGui import QMessageBox
from PyQt4 import QtCore, QtGui, uic
from PyQt4.Qt import pyqtSlot
from hhplt.parameters import SESSION, PARAM,GLOBAL
from hhplt.testengine.server import SERVER_PARAM_CACHE
from hhplt.ui.login import LoginDlg
from hhplt.ui.startTestFrame import StartTestFrame
from hhplt.ui.finishTestFrame import  FinishTestFrame
from hhplt.ui.parallelFinishTestFrame import ParallelFinishTestFrame
from hhplt.ui.askForSomethingDlg import AskForSomethingDlg
from hhplt.ui.localSPSettingDlg import LocalSPSettingDlg
import time
from threading import Event
from hhplt.testengine.product_manage import getProductTestSuiteNameList,getAutoTrigger
from hhplt.deviceresource import retrieveAllResource

class ClientStatistic():
    def __init__(self,statusLabel):
        #测试统计数据，5者分别是：测试总数、测试成功数、测试失败数、异常终止数、复测数量
        self.total = 0
        self.succ = 0
        self.fail = 0
        self.abort = 0
        self.repeat = 0
        self.statusLabel = statusLabel
        self.testedSet = set()
    
    def __addTotal(self):
        self.total = self.total + 1
    
    def __processRepeat(self,testingProductIdCode):
        if testingProductIdCode is not None:
            if testingProductIdCode in self.testedSet:
                self.repeat = self.repeat + 1
            else:
                self.testedSet.add(testingProductIdCode)
        
    def addSucc(self,testingProductIdCode=None):
        self.__addTotal()
        self.succ = self.succ + 1
        self.__processRepeat(testingProductIdCode)
        self.__showToStatus()
    
    def addFail(self,testingProductIdCode=None):
        self.__addTotal()
        self.fail = self.fail + 1
        self.__processRepeat(testingProductIdCode)
        self.__showToStatus()
    
    def addAbort(self):
        self.__addTotal()
        self.abort = self.abort + 1
        self.__showToStatus()

    def __toString(self):
        return u"本工位测试总数[%d],<font color=green>成功[%d]</font>,\
            <font color=red>失败[%d]</font>,<font color=blue>异常终止[%d]</font>,\
                                复测[%d],\
                                成功率:[%d%%],复测率:[%d%%]" %(
            self.total,self.succ,self.fail,self.abort,self.repeat,
             self.succ*100/self.total,(self.repeat*100/(self.total-self.abort)) if self.total-self.abort!=0 else 0
             )
    def __showToStatus(self):
        msg = self.__toString()
        self.statusLabel.setText(msg)

class MainWnd(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        uic.loadUi("hhplt/ui/mainWnd.ui",self)
        GLOBAL["logUi"] = LogUi(self.message)
        self.nowFrameContent = None
        self.loginDlg = LoginDlg(self)
        self.workingFrame.setEnabled(False)

        self.childFrames = {}   #子界面容器，key是Frame类型
        self.ad = AskForSomethingDlg(self)  #人工请求对话框
        self.msgDlg = QMessageBox() #异步提示消息对话框
        self.msgDlg.setParent(self)
        self.msgDlg.setWindowFlags(QtCore.Qt.Dialog)
        
        self.manulEvent = Event()   #用于同步界面线程和工作者线程的事件
        
        self.__registerAllLocalUtil()   #注册所有的本地工具对话框到菜单
        
        self.localSPSettingDlg = LocalSPSettingDlg(self)    #临时调参对话框
        
        #初始化状态栏
        self.statusLabel = QtGui.QLabel() 
        self.statusLabel.setAlignment(QtCore.Qt.AlignRight)
        self.statusLabel.setIndent(5)
        self.statusBar.addWidget(self.statusLabel,1) 
        self.stat = ClientStatistic(self.statusLabel)   #测试结果统计

        #关闭日志框的时候，触发菜单中的选中状态
        def logDockCloseEvent(event):
            QtGui.QDockWidget.closeEvent (self.logDockWidget, event)
            self.logWndMenu.setChecked(False)
        self.logDockWidget.closeEvent = logDockCloseEvent
        
        #主窗口事件，依次：手工检查、手动请求信息、
        #异步（不卡界面线程）消息、关闭异步消息、公告板消息、
        #警告消息、严重消息、
        #外部触发测试开始、外部触发测试结束
        self.connect(self, QtCore.SIGNAL("MANUL_CHECK(QString,QString,QString)"), self.__manulAskDlg)
        self.connect(self, QtCore.SIGNAL("MANUL_CHECK_TRIGGER(QString)"), self.__manulAskDlgTrigger)
        self.connect(self, QtCore.SIGNAL("ASK_FOR_SOMETHING(QString,QString,QString)"), self.__askForSomethingDlg)
        
        self.connect(self, QtCore.SIGNAL("ASYN_MESSAGE(QString,QString)"), self.__showMessageDlg)
        self.connect(self, QtCore.SIGNAL("CLOSE_MESSAGE()"), self.__closeMessageDlg)
        self.connect(self, QtCore.SIGNAL("SHOW_DASH_BOARD_MESSAGE(QString)"), self.__showMessageOnDashboard)
        
        self.connect(self, QtCore.SIGNAL("ALERT_MESSAGE(QString)"), self.__alertMessage)
        self.connect(self, QtCore.SIGNAL("CRITICAL_MESSAGE(QString)"), self.__criticalMessage)

        self.connect(self, QtCore.SIGNAL("TRIGGER_START_TESTING()"), self.__triggerStartTesting)
        self.connect(self, QtCore.SIGNAL("TRIGGER_STOP_TESTING()"), self.__triggerStopTesting)

    def closeEvent(self, event):
        print 'exit application'
        QtGui.QMainWindow.closeEvent(self,event);
        import os
        os._exit(0)
        
    def initDashbaord(self):
        '''初始化公告板'''
        #关闭消息框的时候，触发菜单中的选中状态
        def dashboardDockCloseEvent(event):
            QtGui.QDockWidget.closeEvent (self.dashboardDockWidget, event)
            self.dashboardWndMenu.setChecked(False)
        self.dashboardDockWidget.closeEvent = dashboardDockCloseEvent
        self.dashboardDockWidget.hide()
        r = self.frameGeometry()
        self.dashboardDockWidget.setGeometry(r.right()-310,r.bottom()-150,300,100)    
        
    def __initContentFrames(self):
        self.switchToFrame(StartTestFrame)
    
    def switchToFrame(self,newFrame):
        fm = None
        if newFrame in self.childFrames:
            fm = self.childFrames[newFrame]
        else:
            fm = newFrame(self)
            self.childFrames[newFrame] = fm
        if self.nowFrameContent != None:
            self.nowFrameContent.hide()
        self.nowFrameContent = fm
        self.nowFrameContent.show()

    @pyqtSlot(int)
    def on_suiteSelect_activated(self,index):
        if "autoTrigger" in SESSION:
            SESSION["autoTrigger"].close()
        SESSION["testsuite"] = self.suiteSelect.currentText().__str__()
        del SESSION["seletedTestItemNameList"]
        del SESSION["localDataFileName"]
        self.__initContentFrames()
        self.setUiInfoFromSession()
        SESSION["autoTrigger"] = getAutoTrigger(SESSION["product"],SESSION["testsuite"])()
        SESSION["autoTrigger"].start()

    @pyqtSlot()
    def on_logoutButton_clicked(self):
        self.__relogin()
    
    @pyqtSlot()
    def on_loginMenu_triggered(self):
        self.__relogin()
        
    @pyqtSlot()
    def on_logWndMenu_triggered(self):    
        if self.logWndMenu.isChecked():
            self.logDockWidget.show()
        else:
            self.logDockWidget.hide()
    
    @pyqtSlot() 
    def on_dashboardWndMenu_triggered(self):
        if self.dashboardWndMenu.isChecked():
            self.dashboardDockWidget.show()
        else:
            self.dashboardDockWidget.hide()
    
    @pyqtSlot()
    def on_changePasswordMenu_triggered(self):
        from hhplt.ui.modifyPasswordDlg import ModifyPasswordDlg
        modifyPasswordDlg = ModifyPasswordDlg(self)
        modifyPasswordDlg.show()
        
    @pyqtSlot()
    def on_paramSettingMenu_triggered(self):
        if SESSION["testorRole"] == 'TESTOR':
            QMessageBox.information(None,u"提示",u"非高级用户不能修改参数",u"确定")
            return
        from hhplt.ui.paramSettingDlg import ParamSettingDlg
        paramSettingDlg = ParamSettingDlg(self)
        paramSettingDlg.show()
        
    @pyqtSlot()    
    def on_aboutMenu_triggered(self):
        QMessageBox.information(None,u"关于",
            u"KCHT生产线工装测试平台 V2.01.00\n 天津科畅慧通信息技术有限公司\n版权所有@2014-2018",
            u"确定")
    
    @pyqtSlot()    
    def on_exitMenu_triggered(self):
        import os
        os._exit(0)

    @pyqtSlot()
    def on_modifyLocalParamMenu_triggered(self):
        '''修改本地临时参数'''
        self.localSPSettingDlg.show()
        
    
    def paintEvent(self,event):
        QtGui.QMainWindow.paintEvent(self,event)
        self.__resizeContentFrame()

    def __resizeContentFrame(self):
        '''重置工作区大小'''
        if self.nowFrameContent is not None:
            self.nowFrameContent.resize(self.workingFrame.size())
    
    def __relogin(self):
        self.dashboardDockWidget.hide()
        if "testor" in SESSION:
            GLOBAL["logUi"].log(u"检测员[%s]退出"%SESSION["testor"])
        if "autoTrigger" in SESSION:
            SESSION["autoTrigger"].close()
        SESSION.clearAll()
        self.initDefaultLocalSpParams()
        retrieveAllResource()
        self.testContent.clear()
        self.testorContent.clear()
        self.loginDlg.show()
        self.workingFrame.setEnabled(False)
        self.__initContentFrames()

    def initDefaultLocalSpParams(self):
        SERVER_PARAM_CACHE.clear()
        if "SP_PARAM" in PARAM:
            sp = json.load(open(PARAM["SP_PARAM"],"r"))
            SERVER_PARAM_CACHE.update(sp)

    def show(self):
        QtGui.QMainWindow.show(self)
        self.__relogin()

    def setUiInfoFromSession(self):
        '''从session设置界面信息'''
        self.testContent.setText("产品:[%s]"%SESSION["product"])
        self.testorContent.setText(SESSION["workbay"]+u"工位"+SESSION["testor"]+u"正在检验")
        self.statusLabel.setText(SESSION["serverIp"]+u"服务已连接")
        
        #初始化测试集合选择栏
        self.suiteSelect.clear()
        for name in getProductTestSuiteNameList(SESSION["product"]):
            self.suiteSelect.addItem(name)
        inx = self.suiteSelect.findText(SESSION["testsuite"])
        self.suiteSelect.setCurrentIndex(inx)
        
        self.workingFrame.setEnabled(True)
        self.nowFrameContent._initUi()
        
        if SESSION["testorRole"] == 'TESTOR':
            self.modifyLocalParamMenu.setDisabled(True)
    
    def __alertMessage(self,message):
        QMessageBox.warning(None,u"消息",message,QMessageBox.Ok)
            
    def __criticalMessage(self,message):
        QMessageBox.critical(GLOBAL["mainWnd"],u"严重异常！",message,QMessageBox.Ok)
    
    def __large(self,msg):
        return "<font size='30'>"+msg+"</font>"
    
    #以下两个方法用于处理人工检验的模态对话框，由于验证逻辑和界面分署不同的线程，因此通过一个Event来同步
    def __manulAskDlg(self,title,msg,check):
        self.confirmDlg = QMessageBox()
        self.confirmDlg.setWindowTitle(title)
        self.confirmDlg.setIcon(QMessageBox.Question);
        self.confirmDlg.setText(self.__large(msg));
        self.confirmDlg.setParent(self)
        self.confirmDlg.setWindowFlags(QtCore.Qt.Dialog)
        
        if check == 'check':
            self.confirmDlg.addButton(u"正常", QMessageBox.AcceptRole)
            self.confirmDlg.addButton(u"不正常", QMessageBox.RejectRole)
        elif check == 'ok':
            self.confirmDlg.addButton(u"确定", QMessageBox.AcceptRole)
        elif check == 'confirm':
            self.confirmDlg.addButton(u"是", QMessageBox.AcceptRole)
            self.confirmDlg.addButton(u"否", QMessageBox.RejectRole)
        elif check == 'sucess':
            self.confirmDlg.addButton(u"成功", QMessageBox.AcceptRole)
            self.confirmDlg.addButton(u"不成功", QMessageBox.RejectRole)
        elif check == 'nothing':
            abc = self.confirmDlg.addButton(u"成功", QMessageBox.AcceptRole)
            abc.hide()
        self.manulDlgResult = self.confirmDlg.exec_()
        self.manulEvent.set()
    
    def waitForManulCheckDlg(self):
        self.manulEvent.wait()
        self.manulEvent.clear()
        return self.manulDlgResult
    
    def __manulAskDlgTrigger(self,result):
        if result == 'NORMAL':
            self.confirmDlg.done(0)
        elif result == 'ABNORMAL':
            self.confirmDlg.done(1)
    
    #以下两个方法用于处理中途交互请求，例如扫描条码等
    def __askForSomethingDlg(self,title,msg,defaultValue=None):
        self.manulSomething = None
        self.ad.show(title,msg)
        if defaultValue is not None:
            self.ad.setDefaultValue(defaultValue)
    
    def waitForSomething(self):
        self.manulEvent.wait()
        self.manulEvent.clear()
        if self.manulSomething == "#$%^&EXIT&^%$#":
            from hhplt.testengine.exceptions import AbortTestException
            raise AbortTestException(message = u'用户人工中止')
        return self.manulSomething
    
    #用户异步提示信息
    def __showMessageDlg(self,title,msg):
        #self.msgDlg = QMessageBox.information(None, title, msg,u"确定")
        self.msgDlg.setWindowTitle(title)
        self.msgDlg.setIcon(QMessageBox.Information);
        self.msgDlg.setText(self.__large(msg));
        self.msgDlg.show()
        pass
    
    def __closeMessageDlg(self):
        self.msgDlg.hide()    
    
    #外部触发测试开始/结束
    def __triggerStartTesting(self):
        #这两个函数应该是用不着加锁，因为是由主线程的槽触发的，不会造成同步问题
        if isinstance(self.nowFrameContent,StartTestFrame) and self.nowFrameContent.isEnabled():
            self.nowFrameContent.on_startTestButton_clicked()

    def __triggerStopTesting(self):
        if isinstance(self.nowFrameContent,FinishTestFrame):
            self.nowFrameContent.on_finishButton_clicked()
        if isinstance(self.nowFrameContent,ParallelFinishTestFrame):
            self.nowFrameContent.on_finishButton_clicked()
    
    def __registerAllLocalUtil(self):
        '''注册本地工具的界面，增加菜单项并显示在界面上'''
        from hhplt.localutil import REGISTERED_LOCAL_UTIL
        
        class LocalUtilSlotContainer(QtCore.QObject):
            '''本地工具槽响应容器'''
            def __init__(self,dlgCls,mainWnd):
                QtCore.QObject.__init__(self,mainWnd)
                self.utilDlg = dlgCls(mainWnd)
                
            @pyqtSlot()
            def triggerLocalUtil(self):
                '''点击本地工具菜单触发槽的响应函数'''
                self.utilDlg.show()
        
        for dlgCls in REGISTERED_LOCAL_UTIL:
            lusc = LocalUtilSlotContainer(dlgCls,self)
            self.localUtilMenu.addAction(lusc.utilDlg.windowTitle(),lusc, QtCore.SLOT("triggerLocalUtil()"))
    
    def __showMessageOnDashboard(self,message):
        '''公告板上显示信息'''
        if not self.dashboardDockWidget.isVisible():
            self.dashboardWndMenu.setChecked(True)
            self.dashboardDockWidget.show()
        message = message.replace("\n","<br/>")
        self.dashboardMessage.setText("<font size=25>%s</font>"%message)
    
    
import logging
class LogUi:
    '''日志框'''
    def __init__(self,logListView):
        self.logListView = logListView
        self.qi = QtGui.QStandardItemModel()
        logListView.setModel(self.qi)
        
        #初始化文件保存
        logging.basicConfig(level=logging.INFO,
                format='%(asctime)s : %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='logs/%s.log'%(self.now()[:10]),
                filemode='a')
    
    @staticmethod
    def now():
        return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    
    def log(self,message):
        logging.info(message)
        logMessage = LogUi.now()+"\t"+message
        logItem = QtGui.QStandardItem(logMessage)
        if u'失败' in message or u'不通过' in message:
            logItem.setForeground(QtGui.QBrush(QtCore.Qt.red))
        elif u'终止' in message:
            logItem.setForeground(QtGui.QBrush(QtCore.Qt.blue))
        elif u'测试通过' in message:
            logItem.setForeground(QtGui.QBrush(QtCore.Qt.green))
        logItem.setEditable(False)
        self.qi.appendRow(logItem)
        if self.qi.rowCount() >= PARAM["maxLogItemNumber"]:
            self.qi.removeRow(0)
        self.logListView.scrollToBottom()
        
