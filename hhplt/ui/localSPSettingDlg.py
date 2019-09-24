#encoding:utf-8
'''
Created on 2015-11-5
临时应用参数设置窗口
对应SP工具中的参数
@author: user
'''

from PyQt4 import QtGui, QtCore, uic
from PyQt4.Qt import pyqtSlot
from PyQt4.QtGui import QMessageBox
from hhplt.testengine.server import SERVER_PARAM_CACHE


class LocalSPSettingDlg(QtGui.QDialog):
    def __init__(self,parent):
        super(LocalSPSettingDlg,self).__init__(parent = parent)
        uic.loadUi( "hhplt/ui/localSPSettingDlg.ui", self)
        self.paramEditMap = {}


    def show(self):
        QtGui.QDialog.show(self)
        self.__loadCurrentParams()
        
        
    def __loadCurrentParams(self):
        row = 0
        column = 0

        for p in sorted(SERVER_PARAM_CACHE.keys()):
            if p not in self.paramEditMap:
                label = QtGui.QLabel(p)
                edit = QtGui.QLineEdit(str(SERVER_PARAM_CACHE[p]))

                self.gridLayout.addWidget(label,row,column)
                self.gridLayout.addWidget(edit,row,column + 1)

                if column == 2:
                    column = 0
                    row += 1
                else:column += 2

                self.paramEditMap[p] = edit
            else:
                self.paramEditMap[p].setText(str(SERVER_PARAM_CACHE[p]))
    
    def __saveParams(self):
        for e in self.paramEditMap:
            SERVER_PARAM_CACHE[e] = str(self.paramEditMap[e].text())
    
      
    @pyqtSlot()
    def on_saveBtn_clicked(self):
        self.__saveParams()
        self.hide()
    
    @pyqtSlot()
    def on_cancelBtn_clicked(self):
        self.hide()
            
            
        
