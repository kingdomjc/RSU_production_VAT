#encoding:utf-8
'''
Created on 2014-8-15
测试主体框
@author: 张文硕
'''
from PyQt4 import QtCore, QtGui, uic
from PyQt4.Qt import pyqtSlot
from hhplt.ui.AbstractContentFrame import AbstractContentFrame
from hhplt.testengine.product_manage import getTestItemList
from hhplt.parameters import SESSION
from hhplt.testengine.testcase import startTest 

class TestingFrame(AbstractContentFrame):
    def _ui(self):
        self.connect(self, QtCore.SIGNAL("LOG(QString)"), self.log)
        self.connect(self, QtCore.SIGNAL("START_ITEM(QString)"), self.markItemStarting)
        self.connect(self, QtCore.SIGNAL("ITEM_FINISH(QString,bool)"), self.markTestItemFinish)
        self.connect(self, QtCore.SIGNAL("FINISH_TEST()"), self.switchToFinishTest)
        return "hhplt/ui/testingFrame.ui"
    
    def _initUi(self):
        self.nowTesting.setText(u"正在测试");
        self.testItemList = filter(lambda x:x["name"] in SESSION["seletedTestItemNameList"],
                                   getTestItemList(SESSION["product"],SESSION["testsuite"]))

        self.progressBar.setRange(0,len(self.testItemList))
        self.testItemTable.clearContents()
        self.testItemTable.setRowCount(len(self.testItemList))
        self.testItemTable.setColumnCount(5)
        self.testItemTable.setColumnWidth(1,150)
        self.testItemTable.setColumnWidth(2,350)
        for i in range(len(self.testItemList)):
            f = self.testItemList[i]
            self.testItemTable.setItem(i,0,QtGui.QTableWidgetItem(f["index"]))
            self.testItemTable.setItem(i,1,QtGui.QTableWidgetItem(f["name"]))
            self.testItemTable.setItem(i,2,QtGui.QTableWidgetItem(f["desc"]))
            self.testItemTable.setItem(i,3,QtGui.QTableWidgetItem(f["method"]))
            self.testItemTable.setItem(i,4,QtGui.QTableWidgetItem(u"未测试"))
        self.progressBar.setValue(0)
        
        self.__startExecutingTest()
        
        
    def __startExecutingTest(self):
        self.mainWnd.logoutButton.setEnabled(False)
        self.mainWnd.suiteSelect.setEnabled(False)
        startTest(self)
    
    def __getItemIndex(self,fun):
        for i in range(len(self.testItemList)):
            if self.testItemList[i]["name"] == fun:
                return i
    
    ##########################################################################################
    
    def switchToFinishTest(self):
        from hhplt.ui.finishTestFrame import FinishTestFrame
        self._switchToFrame(FinishTestFrame)
        self.mainWnd.logoutButton.setEnabled(True)
        self.mainWnd.suiteSelect.setEnabled(True)
    
    def markItemStarting(self,fun):
        i = self.__getItemIndex(fun)
        self.testItemTable.selectRow(i)
        self.testItemTable.setItem(i,4,QtGui.QTableWidgetItem(u"正在测试"))
    
    def markTestItemFinish(self,fun,succOrFail):
        i = self.__getItemIndex(fun)
        self.testItemTable.setItem(i,4,QtGui.QTableWidgetItem(u"测试通过" if succOrFail else u"测试不通过"))
        self.progressBar.setValue(i+1)
        self.testItemTable.scrollToItem(self.testItemTable.item(i,0))

    def log(self,msg):
        self.logUi.log(msg)
    
    


