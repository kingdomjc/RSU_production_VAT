#encoding:utf-8
'''
Created on 2016-7-5
并行测试框架界面
对于并行（不管是真正的并行，还是依次串行）的测试，通过槽号来进行标识，
同步显示一批次所有的测试进度。
@author: 张文硕
'''

from PyQt4 import QtCore, QtGui, uic
from PyQt4.Qt import pyqtSlot
from hhplt.ui.AbstractContentFrame import AbstractContentFrame
from hhplt.parameters import SESSION,PARAM
from slotTestingFrame import SlotTestingFrame
from parallelFinishTestFrame import ParallelFinishTestFrame
from hhplt.testengine.parallelTestcase import startParallelTest

class ParallelTestingFrame(AbstractContentFrame):
    def _ui(self):
        self.connect(self, QtCore.SIGNAL("LOG(QString)"), self.log)
        self.connect(self, QtCore.SIGNAL("START_ITEM(QString,QString)"), self.markItemStarting)
        self.connect(self, QtCore.SIGNAL("ITEM_FINISH(QString,QString,bool)"), self.markTestItemFinish)
        self.connect(self, QtCore.SIGNAL("FINISH_TEST(QString)"), self.switchToFinishTest)
        #上述3个信号绑定，相比TestFrame来说都增加了一个入参，作为产品槽号
        return "hhplt/ui/parallelTestingFrame.ui"
    
    def _initUi(self):
        if self.gridLayout.count() == 0:    #只建立一次界面
            self.slotFrames = {}
            si = 0
            locs = PARAM["productUiSlots"].split(";")
            for slot in PARAM["productSlots"].split(","):
                y,x = map(lambda p:int(p),locs[si].split(","))
                self.slotFrames[slot] = SlotTestingFrame(self)
                self.gridLayout.addWidget(self.slotFrames[slot],x,y)
                si += 1

        for f in self.slotFrames:
            self.slotFrames[f].initTestingUi(f)
        
        self.__startExecutingTest()

    def __startExecutingTest(self):
        self.mainWnd.logoutButton.setEnabled(False)
        self.mainWnd.suiteSelect.setEnabled(False)
        self.parallelTestResults = set()
        startParallelTest(self)

    ##########################################################################################
    
    def switchToFinishTest(self,slot):
        self.parallelTestResults.add(slot)
        if len(self.parallelTestResults) == self.gridLayout.count():
            #到这里，表示这一波已经完成测试了
            self._switchToFrame(ParallelFinishTestFrame)
            self.mainWnd.logoutButton.setEnabled(True)
            self.mainWnd.suiteSelect.setEnabled(True)
        
    def markItemStarting(self,slot,fun):
        self.slotFrames[unicode(slot)].markItemStarting(fun)
    
    def markTestItemFinish(self,slot,fun,succOrFail):
        self.slotFrames[unicode(slot)].markTestItemFinish(fun,succOrFail)

    def log(self,msg):
        self.logUi.log(msg)
    
    
    
    
    
    
        