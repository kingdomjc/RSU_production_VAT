#encoding:utf-8
'''
Created on 2014-8-15

@author: 张文硕
'''
from PyQt4 import QtCore, QtGui, uic
from PyQt4.Qt import pyqtSlot
from hhplt.parameters import SESSION,PARAM
from hhplt.testengine.AsynServerTaskContainer import asynServerTaskContainer
from hhplt.ui.AbstractContentFrame import AbstractContentFrame
from hhplt.parameters import GLOBAL
import winsound

#from hhplt.testengine.AsynServerTaskContainer import asynServerTaskContainer
from hhplt.testengine.BufferedTestReportUploader import bufferedTestReportUploader

class FinishTestFrame(AbstractContentFrame):
    def _ui(self):
        return "hhplt/ui/finishTestFrame.ui"
    
    def _initUi(self):
        testingProduct = SESSION["testingProduct"]
        if not testingProduct.finishSmoothly:
            self.result.setText(u"<font color=gold>测试终止</font>");
            self.failReason.setText("\n".join(testingProduct.failReasonMessage))
            GLOBAL["mainWnd"].stat.addAbort()
            self.failReasonBox.show()
            self.__beepForFail()
        else:
            testingProductIdCode = testingProduct.getTestingProductIdCode() #正在测试的产品标识，可能空（复测）
            
            if testingProductIdCode is None and not SESSION["isMend"]:
                testingProduct.failReasonMessage.append(u"缺少绑定标识的结果(复测或维修)无法保存到数据库\n")
                            
            if SESSION["isMend"] or testingProductIdCode is None or self.__uploadReport(testingProductIdCode,SESSION["testingProduct"].toXml()):
                if testingProduct.testResult:
                    if testingProductIdCode is None and not SESSION["isMend"]:
                        #非维修测试，但缺少标识，给出提示，不能上传服务
                        self.result.setText(u"<font color=gold>成功</font>")
                        self.failReason.setText("\n".join(testingProduct.failReasonMessage))
                        self.failReasonBox.show()
                    else:
                        self.result.setText(u"<font color=green>成功</font>")
                        self.failReasonBox.hide()
                    GLOBAL["mainWnd"].stat.addSucc(testingProductIdCode)
                    self.__beepForSucc()
                else:
                    self.result.setText(u"<font color=red>失败</font>");
                    self.failReason.setText("\n".join(testingProduct.failReasonMessage))
                    self.failReasonBox.show()
                    GLOBAL["mainWnd"].stat.addFail(testingProductIdCode)
                    self.__beepForFail()
            else:
                self.result.setText(u"<font color=gold>测试终止</font>");
                self.failReason.setText(u"测试结果上传服务器失败，本次测试结果抛弃。")
                self.failReasonBox.show()
                self.logUi.log(u"产品[%s][%s]的测试结果上传服务器失败，本次测试结果抛弃。"%(testingProduct.productName,testingProduct.suite))
                GLOBAL["mainWnd"].stat.addAbort()
        self.finishButton.setFocus()
    
    def __beepForSucc(self):
        '''成功时蜂鸣器发声'''
        winsound.Beep(PARAM["beepFreq"],300)
        
    def __beepForFail(self):
        '''失败时蜂鸣器发声'''
        for i in range(3):
            winsound.Beep(PARAM["beepFreq"]-i*100,100)

    @pyqtSlot()
    def on_finishButton_clicked(self):
        from hhplt.ui.startTestFrame import StartTestFrame
        self._switchToFrame(StartTestFrame)

    def __uploadReport(self,idCode,report):
        asynServerTaskContainer.submitReportUpload(idCode, report)
        # bufferedTestReportUploader.submitReportUpload(idCode,report)
        return True
            
            
