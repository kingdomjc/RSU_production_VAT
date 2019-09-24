#encoding:utf-8
'''
Created on 2016-7-5

并行测试完成一组
统一通知用户界面

@author: 张文硕
'''
from PyQt4 import QtCore, QtGui, uic
from PyQt4.Qt import pyqtSlot
from hhplt.parameters import SESSION,PARAM
from hhplt.ui.AbstractContentFrame import AbstractContentFrame
from hhplt.parameters import GLOBAL
from hhplt.testengine.AsynServerTaskContainer import asynServerTaskContainer


class SlotTestResultFrame(QtGui.QGroupBox):
    def __init__(self,parent):
        QtGui.QGroupBox.__init__(self,parent)
        uic.loadUi("hhplt/ui/slotTestResultFrame.ui",self)

class ParallelFinishTestFrame(AbstractContentFrame):
    def _ui(self):
        return "hhplt/ui/parallelFinishTestFrame.ui"

    def _______initUi(self):
        self.__clearTables()
        for slot in SESSION["testingProduct"]:
            tp = SESSION["testingProduct"][slot]
            if not tp.finishSmoothly:
                self.__showAsFinishUnsmoothly(tp)
                GLOBAL["mainWnd"].stat.addAbort()
            else:
                testingProductIdCode = tp.getTestingProductIdCode() #正在测试的产品标识，可能空（复测）
                if SESSION["isMend"] or testingProductIdCode is None or self.__uploadReport(testingProductIdCode,tp.toXml()):
                    if tp.testResult:
                        if testingProductIdCode is None and not SESSION["isMend"]:
                            self.__showAsSuccButNoId(tp)
                        else:
                            self.__showAsSucc(tp)
                        GLOBAL["mainWnd"].stat.addSucc(testingProductIdCode)
                    else:
                        if testingProductIdCode is None and not SESSION["isMend"]:
                            self.__showAsFailButNoId(tp)
                        else:
                            self.__showAsFail(tp)
                        GLOBAL["mainWnd"].stat.addFail(testingProductIdCode)
                else:
                    self.__showAsFinishButNoUpload(tp)
                    GLOBAL["mainWnd"].stat.addAbort()
        self.finishButton.setFocus()
        self.unpassTestResultTable.sortItems(0,QtCore.Qt.AscendingOrder)
        self.passTestResultTable.sortItems(0,QtCore.Qt.AscendingOrder)

    
    def __initTestResultSlots(self):
        slotPerLine = 3 if "productSlotsPerLine" not in PARAM else PARAM["productSlotsPerLine"]
        wholeWidth = self.testResultArea.window().width()
        eachWidth = wholeWidth / slotPerLine + 20

        self.slotFrames = {}
        si = 0
        locs = PARAM["productUiSlots"].split(";")
        for slot in PARAM["productSlots"].split(","):
            y,x = map(lambda p:int(p),locs[si].split(","))
            self.slotFrames[slot] = SlotTestResultFrame(self.testResultArea)
            self.slotFrames[slot].setMaximumWidth(eachWidth)
            self.resultGridLayout.addWidget(self.slotFrames[slot],x,y)
            si += 1
    
    def _initUi(self):
        if self.resultGridLayout.count() == 0:self.__initTestResultSlots()
        for slot in SESSION["testingProduct"]:
            tp = SESSION["testingProduct"][slot]
            if not tp.finishSmoothly:
                self.__showAsFinishUnsmoothly(tp)
                GLOBAL["mainWnd"].stat.addAbort()
            else:
                testingProductIdCode = tp.getTestingProductIdCode() #正在测试的产品标识，可能空（复测）
                if SESSION["isMend"] or testingProductIdCode is None or self.__uploadReport(testingProductIdCode,tp.toXml()):
                    if tp.testResult:
                        if testingProductIdCode is None and not SESSION["isMend"]:
                            self.__showAsSuccButNoId(tp)
                        else:
                            self.__showAsSucc(tp)
                        GLOBAL["mainWnd"].stat.addSucc(testingProductIdCode)
                    else:
                        if testingProductIdCode is None and not SESSION["isMend"]:
                            self.__showAsFailButNoId(tp)
                        else:
                            self.__showAsFail(tp)
                        GLOBAL["mainWnd"].stat.addFail(testingProductIdCode)
                else:
                    self.__showAsFinishButNoUpload(tp)
                    GLOBAL["mainWnd"].stat.addAbort()
        self.finishButton.setFocus()

    def __showResult(self,slot,result,msg,color):
        f = self.slotFrames[slot]
        f.setTitle(u"槽位【%s】测试结果"%slot)
        f.result.setText("<font color=%s>%s</font>"%(color,result))
        f.failReason.setText(msg)
        
    def __uploadReport(self,idCode,report):
        asynServerTaskContainer.submitReportUpload(idCode, report)
        return True
    
    def __showAsFinishUnsmoothly(self,tp):
        self.__showResult(tp.productSlot,u"测试终止","\n".join(tp.failReasonMessage),"orange")
    
    def __showAsSuccButNoId(self,tp):
        self.__showResult(tp.productSlot,u"测试通过",u"缺少绑定标识的结果(复测或维修)无法保存到数据库\n","blue")
    
    def __showAsSucc(self,tp):
        self.__showResult(tp.productSlot,u"测试通过","","green")
    
    def __showAsFailButNoId(self,tp):
        self.__showResult(tp.productSlot,u"NG",
                           "\n".join(tp.failReasonMessage)+u"\n缺少绑定标识的结果(复测或维修)无法保存到数据库"
                           ,"red")
    
    def __showAsFail(self,tp):
        self.__showResult(tp.productSlot,u"NG","\n".join(tp.failReasonMessage),"red")
        
    def __showAsFinishButNoUpload(self,tp):
        self.__showResult(tp.productSlot,u"测试终止",u"测试结果无法上传服务器，请检查网络","red")
        
    @pyqtSlot()
    def on_finishButton_clicked(self):
        from hhplt.ui.startTestFrame import StartTestFrame
        self._switchToFrame(StartTestFrame)
    



