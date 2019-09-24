#encoding:utf-8
'''
Created on 2014-8-29
测试中途请求点神马东西
@author: 张文硕
'''

from PyQt4 import QtGui, QtCore, uic

from PyQt4.Qt import pyqtSlot
from PyQt4.QtGui import QMessageBox
from hhplt.utils import isEmptyString
from hhplt.deviceresource import askForResource,AutoBarScanner
from hhplt.parameters import PARAM
import thread
from PyQt4.QtCore import SIGNAL

autoCommit = True
class AskForSomethingDlg(QtGui.QDialog):
    def __init__(self,parent):
        super( AskForSomethingDlg, self ).__init__(parent=parent)
        uic.loadUi( "hhplt/ui/askForSomethingDlg.ui", self )
        self.connect(self,QtCore.SIGNAL("AUTO_SCANNER_RESULT(QString)"),self.__scannerResult)
    
    def __large(self,msg):
        return "<font size='30'>"+msg+"</font>"
    
    def setDefaultValue(self,defaultValue):
        self.something.setText(str(defaultValue))
        self.something.moveCursor(QtGui.QTextCursor.EndOfLine,QtGui.QTextCursor.MoveAnchor)
    
    def show(self,title,content):
        QtGui.QDialog.show(self)
        self.title = title;
        self.label.setText(self.__large(content))
        self.setWindowTitle(title)
#        self.setFixedSize(400,230)
        self.something.clear()
        self.something.setFocus()
        if autoCommit:
            self.__startAutoScanner()

    def __startAutoScanner(self):
        '''开始自动扫码'''
        def autoScanThread():
            barScannerDriverCls = None
            if PARAM["barScannerType"] == 'mindeo':
                barScannerDriverCls = AutoBarScanner.MindeoAutoBarScanner
            elif PARAM["barScannerType"] == 'keyence':
                barScannerDriverCls = AutoBarScanner.KeyenceAutoBarScanner
            sc = askForResource('AutoBarScanner', barScannerDriverCls,barScannerCom = PARAM["barScannerCom"])
            barCode = sc.scan()
            if barCode is not None:
                self.emit(SIGNAL("AUTO_SCANNER_RESULT(QString)"),barCode)
        thread.start_new_thread(autoScanThread,())
        
    def __scannerResult(self,barCode):
        self.something.setText(barCode)
        
    def closeEvent(self, event):
        '''拦截关闭事件，如果关闭，标示要退出本次测试'''
        event.ignore()
        self.on_exitTestButton_clicked()
    
    def keyPressEvent(self,event):
        '''拦截ESC按钮，触发关闭事件'''
        if event.key() == QtCore.Qt.Key_Escape:
            self.on_exitTestButton_clicked()
        else:
            QtGui.QDialog.keyPressEvent(self,event)
    
    @pyqtSlot()
    def on_something_textChanged(self):
        txt = self.something.toPlainText().__str__()
        if "\n" in txt: #在任意位置按回车都能提交
            self.something.setText(txt.__str__().replace("\n",""))
            self.on_okButton_clicked()
        
    @pyqtSlot()
    def on_okButton_clicked(self):
        if isEmptyString(self.something.toPlainText()):
            QMessageBox.warning(None, self.title, u"您没有填写任何内容", QMessageBox.Yes, QMessageBox.Yes);
            self.something.setFocus()
            return
        self.parent().manulSomething = self.something.toPlainText().__str__()
        self.parent().manulEvent.set()
        self.hide()
    
    @pyqtSlot()
    def on_exitTestButton_clicked(self):
        if QMessageBox.question(None, u"工装测试", u"真的要中止本次测试吗？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) \
            == QMessageBox.Yes:
            #中止，用这么个玩意来作为返回值，有点没溜
            self.parent().manulSomething ="#$%^&EXIT&^%$#"
            self.parent().manulEvent.set()
            self.hide()
        else:
            self.something.setFocus()
    