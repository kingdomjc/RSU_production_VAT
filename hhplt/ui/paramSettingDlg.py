#encoding:utf-8
'''
Created on 2014-12-13
参数设置对话框
@author: user
'''
from PyQt4 import QtGui, QtCore, uic
from PyQt4.Qt import pyqtSlot
from PyQt4.QtGui import QMessageBox
import os,json
from hhplt.parameters import PARAM


class ParamSettingDlg(QtGui.QDialog):
    def __init__(self,parent):
        super(ParamSettingDlg,self).__init__(parent = parent)
        uic.loadUi( "hhplt/ui/paramSettingDlg.ui", self)
        self.__initUi()
        
    def __loadParamDescFromFile(self):
        if not os.path.exists(PARAM["PARAM_UI_FILENAME"]):
            return False
        try:
            f = file(PARAM["PARAM_UI_FILENAME"])
            self.paramList = json.load(f)
            return True
        except IOError,e:
            print e
        finally:
            f.close()
    
    def __initUi(self):
        if not self.__loadParamDescFromFile():
            QMessageBox.information(None,u"修改参数",u"没有可以配置的参数！")
            self.hide()

        for item in self.paramList:
            label = QtGui.QLabel(item["desc"])
            item["valueWidget"] = QtGui.QLineEdit(str(PARAM[item["name"]]))
            self.formLayout.addRow(label,item["valueWidget"])
        
    @pyqtSlot()
    def on_cancelButton_clicked(self):
        self.hide()
        
    @pyqtSlot()
    def on_saveButton_clicked(self):
        for item in self.paramList:
            value = item["valueWidget"].text().__str__()
            if item["type"] == "int":
                value = int(value)
            elif item["type"] == "float":
                value = float(value)
            PARAM[item["name"]] = value
        PARAM.dumpParameterToLocalFile()    
        QMessageBox.information(None,u"修改参数",u"参数修改完成！")
        self.hide()

