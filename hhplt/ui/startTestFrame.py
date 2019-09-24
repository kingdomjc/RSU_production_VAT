#encoding:utf-8
'''
Created on 2014-8-14
开始测试框
@author: 张文硕
'''
from hhplt.testengine.product_manage import getTestSuiteDesc,getTestSuiteParallelSlotCount
from PyQt4 import QtCore, QtGui, uic
from PyQt4.Qt import pyqtSlot
from hhplt.testengine.product_manage import getTestItemList
from hhplt.ui.AbstractContentFrame import AbstractContentFrame
from hhplt.parameters import SESSION,PARAM


class StartTestFrame(AbstractContentFrame):
    def _ui(self):
        return "hhplt/ui/startTestFrame.ui"
    
    def _initUi(self):
        if not SESSION.isEmpty():
            self.desc.setText(getTestSuiteDesc(SESSION["product"],SESSION["testsuite"]))
        self.__initTestItemSelection()
        self.startTestButton.setFocus()
        SESSION["testingProduct"] = None
    
    @pyqtSlot()
    def on_startTestButton_clicked(self):
        self.__startTesting()

    @pyqtSlot()            
    def on_selectAllButton_clicked(self):
        for i in range(self.testItemTable.rowCount()):
            self.testItemTable.cellWidget(i,0).setChecked(True)        
    
    @pyqtSlot()            
    def on_deselectAllButton_clicked(self):
        for i in range(self.testItemTable.rowCount()):
            self.testItemTable.cellWidget(i,0).setChecked(False)    
            
    def __initTestItemSelection(self):
        '''初始化测试项目列表'''
        if "product" not in SESSION:
            return
        allTestItemList = getTestItemList(SESSION["product"],SESSION["testsuite"])
        seletedTestItemNameList = SESSION["seletedTestItemNameList"] if "seletedTestItemNameList" in SESSION else [f["name"] for f in allTestItemList] 
        
        self.testItemTable.clearContents()
        self.testItemTable.setColumnWidth(2,150)
        self.testItemTable.setColumnWidth(3,400)
        self.testItemTable.setRowCount(len(allTestItemList))
        self.testItemTable.setColumnCount(5)
        for i in range(len(allTestItemList)):
            f = allTestItemList[i]
            ckbx = QtGui.QCheckBox()
            ckbx.setChecked(f["name"] in seletedTestItemNameList)
            if SESSION["testorRole"] == 'TESTOR':
                #普通测试角色，不能进行复测和维修测试
                ckbx.setEnabled(False)
            self.testItemTable.setCellWidget(i,0,ckbx)#TODO 复选框
            self.testItemTable.setItem(i,1,QtGui.QTableWidgetItem(f["index"]))
            self.testItemTable.setItem(i,2,QtGui.QTableWidgetItem(f["name"]))
            self.testItemTable.setItem(i,3,QtGui.QTableWidgetItem(f["desc"]))
            self.testItemTable.setItem(i,4,QtGui.QTableWidgetItem(f["method"]))
        
        self.isMend.setChecked(SESSION["isMend"] if "isMend" in SESSION else False)
        if SESSION["testorRole"] == 'TESTOR':
            #普通测试角色，不能进行复测和维修测试
            self.isMend.setEnabled(False)
        else:
            self.isMend.setEnabled(True)
            
    def __startTesting(self):    
        '''正式开始测试'''
        seletedTestItemNameList = []
        for i in range(self.testItemTable.rowCount()):
            if self.testItemTable.cellWidget(i,0).isChecked():
                seletedTestItemNameList.append(self.testItemTable.item(i,2).text().__str__())
        if len(seletedTestItemNameList) == 0:
            QtGui.QMessageBox.warning(None,u"消息",u"您没有选择任何测试项",QtGui.QMessageBox.Ok)
            return 
        
        SESSION["seletedTestItemNameList"] = seletedTestItemNameList
        SESSION["isMend"] = self.isMend.isChecked()
        
        self.logUi.log(u"开始测试产品[%s]的[%s]"%(SESSION["product"],SESSION["testsuite"]) + 
                       ("(维修测试)" if SESSION["isMend"] else ""))
        
        if "productSlots" not in PARAM:
            from hhplt.ui.testingFrame import TestingFrame
            self._switchToFrame(TestingFrame)
        else:
            from hhplt.ui.parallelTestingFrame import ParallelTestingFrame
            self._switchToFrame(ParallelTestingFrame)
            
            
            
            
    
    