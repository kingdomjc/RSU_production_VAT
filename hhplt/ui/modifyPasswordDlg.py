#encoding:utf-8
'''
Created on 2014-8-20
修改密码对话框
@author: 张文硕
'''

from PyQt4 import QtGui, QtCore, uic
from PyQt4.Qt import pyqtSlot
from PyQt4.QtGui import QMessageBox
from hhplt.utils import isEmptyString
from hhplt.testengine.server import ServerBusiness
from hhplt.parameters import SESSION
from hhplt.utils import encryPassword

class ModifyPasswordDlg(QtGui.QDialog):
    def __init__(self,parent):
        super( ModifyPasswordDlg, self ).__init__(parent=parent)
        uic.loadUi( "hhplt/ui/modifyPasswordDlg.ui", self )
        self.setFixedSize(233 ,125)

    @pyqtSlot()
    def on_submitButton_clicked(self):
        
        if isEmptyString(self.oldPassword.text()) or \
            isEmptyString(self.newPassword.text()) or \
            isEmptyString(self.reNewPassword.text()):
            QMessageBox.warning(None,u"修改密码",u"请正确填写参数！",QMessageBox.Ok)
            return
        
        if self.newPassword.text().__str__() != self.reNewPassword.text().__str__() :
            QMessageBox.warning(None,u"修改密码",u"两次输入的新密码不相同！",QMessageBox.Ok)
            return
        
        with ServerBusiness() as sb:
            sb.modifyPassword(username=SESSION["testor"],
                              oldpassword=encryPassword(self.oldPassword.text().__str__()),
                              newpassword=encryPassword(self.newPassword.text().__str__()))
            QMessageBox.information(None,u"修改密码",u"密码修改完成！")
            self.hide()
        pass

    @pyqtSlot()
    def on_cancelButton_clicked(self):
        self.hide()

    
    