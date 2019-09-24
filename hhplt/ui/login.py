#encoding:utf-8
'''
Created on 2014-8-14
登录界面
@author: 张文硕
'''


import sys
from PyQt4 import QtGui, QtCore, uic
from PyQt4.Qt import pyqtSlot
from PyQt4.QtGui import QMessageBox

from hhplt.parameters import PARAM,SESSION,GLOBAL
from hhplt.testengine.product_manage import getProductNameList,getProductTestSuiteNameList,getAutoTrigger

from hhplt.utils import isEmptyString
from hhplt.testengine.server import ServerBusiness
from hhplt.utils import encryPassword

class LoginDlg(QtGui.QDialog):
    def __init__(self,parent):
        super( LoginDlg, self ).__init__(parent=parent)
        uic.loadUi( "hhplt/ui/loginDlg.ui", self )
        self.setFixedSize(408,324)
        self.__initSelector()
        self.serverIp.setText(PARAM["defaultServerIp"])
        self.workbay.setText(PARAM["workbay"])
        
    def __initSelector(self):
        '''初始化联动选择器'''
        self.product.addItems(getProductNameList())
        self.__setDefaultProductAndSuiteValue()

    def __setDefaultProductAndSuiteValue(self):
        '''设置默认选择的产品和测试大项'''
        inx = self.product.findText(PARAM["defaultProduct"])
        if inx != -1:
            self.product.setCurrentIndex(inx)
            self.on_product_activated(inx)
            inx = self.testsuite.findText(PARAM["defaultSuite"])
            if inx != -1:
                self.testsuite.setCurrentIndex(inx)
   
    def show(self):
        QtGui.QDialog.show(self)
        self.testor.clear()
        self.password.clear()
        if "autoLoginUsername" in PARAM:
            self.testor.setText(PARAM["autoLoginUsername"])
        if "autoLoginPassword" in PARAM:
            self.password.setText(PARAM["autoLoginPassword"])
        
        self.testor.setFocus()
   
    @pyqtSlot(int)
    def on_product_activated(self,index):
        productName = self.product.currentText().__str__()
        self.testsuite.clear()
        for name in getProductTestSuiteNameList(productName):
            self.testsuite.addItem(name)
    
    @pyqtSlot()
    def on_loginButton_clicked(self):
        '''登录按钮'''
        if self.serverIp.text().__str__() == 'single':
            #单机登录，不带服务器的
            SESSION["testorRole"] = "SUPER_TESTOR" if self.testor.text().__str__() == 'super' else 'TESTOR'
            SESSION["testor"] = u"单机"
            SESSION["isMend"] = True
            self.__initSession()
            PARAM.dumpParameterToLocalFile()
            GLOBAL["logUi"].log(u"单机登录，即将测试[%s]产品的[%s]"%(SESSION["product"],SESSION["testsuite"]))
            self.hide()
            self.parent().setUiInfoFromSession()
        else:
            if not self.__verifyInput():
                return
            with ServerBusiness(self.serverIp.text().__str__()) as sb:
                user = sb.login(workbay=self.workbay.text().__str__(),
                         username=self.testor.text().__str__(),
                         password=encryPassword(self.password.text().__str__()),
                         product = self.product.currentText().__str__(),
                         testSuite = self.testsuite.currentText().__str__()
                         )
                SESSION["testorRole"] = user["role"]
                SESSION["testor"] = user["username"]
                self.__initSession()
                PARAM.dumpParameterToLocalFile()
                GLOBAL["logUi"].log(u"检测员[%s]登录成功，即将测试[%s]产品的[%s]"%(SESSION["testor"],SESSION["product"],SESSION["testsuite"]))
                self.hide()
                self.parent().setUiInfoFromSession()
    
    def __initSession(self):
        SESSION["serverIp"] = self.serverIp.text().__str__()
        SESSION["workbay"] = self.workbay.text().__str__()
        SESSION["product"] = self.product.currentText().__str__()
        SESSION["testsuite"] = self.testsuite.currentText().__str__()
        SESSION["autoTrigger"] = getAutoTrigger(SESSION["product"],SESSION["testsuite"])()
        SESSION["autoTrigger"].start()
        PARAM["defaultProduct"] = SESSION["product"] 
        PARAM["defaultSuite"] = SESSION["testsuite"]
        PARAM["defaultServerIp"] = SESSION["serverIp"]
    
    @pyqtSlot()
    def on_exitButton_clicked(self):
        print 'exit application'
        import os
        os._exit(0)
        
    def closeEvent(self, event):
        '''拦截关闭事件，要么登陆，要么退出，不能关闭'''
        event.ignore()
        
    def keyPressEvent(self,event):
        '''拦截ESC按钮，使其失效'''
        if event.key() == QtCore.Qt.Key_Escape:
            event.ignore()
        else:
            QtGui.QDialog.keyPressEvent(self,event)
    
    def __verifyInput(self):
        if isEmptyString(self.workbay.text()) or \
            isEmptyString(self.serverIp.text()) or \
            isEmptyString(self.testor.text()) or \
            isEmptyString(self.password.text()) or \
            isEmptyString(self.product.currentText()) or \
            isEmptyString(self.testsuite.currentText()):
            QMessageBox.warning(None,u"登录",u"请正确填写参数！",QMessageBox.Ok)
            return False
        return True
    
   
    
    
