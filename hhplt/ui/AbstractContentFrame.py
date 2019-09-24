#encoding:utf-8
'''
Created on 2014-8-15
主体Frame从本类派生
@author: 张文硕
'''

from PyQt4 import QtCore, QtGui, uic
from PyQt4.Qt import pyqtSlot
from hhplt.parameters import GLOBAL

class AbstractContentFrame(QtGui.QFrame):
    def __init__(self,mainWnd):
        QtGui.QFrame.__init__(self,mainWnd.workingFrame)
        self.mainWnd = mainWnd
        uic.loadUi(self._ui(),self)
        self.logUi = GLOBAL["logUi"]
#        self._initUi()
        
    def _switchToFrame(self,newFrame):
        self.mainWnd.switchToFrame(newFrame)


    def show(self):
        QtGui.QFrame.show(self)
        self._initUi()

    def _initUi(self):
        pass
