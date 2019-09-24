#encoding:utf-8
'''
Created on 2016-7-5
并行测试中的，槽测试面板
@author: 张文硕
'''

from PyQt4 import QtCore, QtGui, uic
from PyQt4.Qt import pyqtSlot
from hhplt.parameters import SESSION
from hhplt.testengine.product_manage import getTestItemList


class SlotTestingFrame(QtGui.QFrame):
    def __init__(self,parent):
        QtGui.QFrame.__init__(self,parent)
        uic.loadUi("hhplt/ui/slotTestingFrame.ui",self)
        
    def initTestingUi(self,slot):
        self.productSlot.setText(slot)
        self.testItemList = filter(lambda x:x["name"] in SESSION["seletedTestItemNameList"],
                                   getTestItemList(SESSION["product"],SESSION["testsuite"]))

        self.progressBar.setRange(0,len(self.testItemList))
        self.testItemTable.clearContents()
        self.testItemTable.setRowCount(len(self.testItemList))
        self.testItemTable.setColumnCount(3)
        self.testItemTable.setColumnWidth(0,80)
        self.testItemTable.setColumnWidth(1,200)
        for i in range(len(self.testItemList)):
            f = self.testItemList[i]
            self.testItemTable.setItem(i,0,QtGui.QTableWidgetItem(f["index"]))
            self.testItemTable.setItem(i,1,QtGui.QTableWidgetItem(f["name"]))
            self.testItemTable.setItem(i,2,QtGui.QTableWidgetItem(u"未测试"))
        self.progressBar.setValue(0)
      
    def __getItemIndex(self,fun):
        for i in range(len(self.testItemList)):
            if self.testItemList[i]["name"] == fun:
                return i  

    def markItemStarting(self,fun):
        i = self.__getItemIndex(fun)
        self.testItemTable.selectRow(i)
        self.testItemTable.setItem(i,2,QtGui.QTableWidgetItem(u"正在测试"))
    
    def markTestItemFinish(self,fun,succOrFail):
        i = self.__getItemIndex(fun)
        rs = QtGui.QTableWidgetItem(u"测试通过" if succOrFail else u"测试不通过")
        rs.setBackgroundColor(QtCore.Qt.green if succOrFail else QtCore.Qt.red)
        self.testItemTable.setItem(i,2,rs)
        self.testItemTable.item(i,1).setBackgroundColor(QtCore.Qt.green if succOrFail else QtCore.Qt.red)
        self.progressBar.setValue(i+1)
        self.testItemTable.scrollToItem(self.testItemTable.item(i,0))
