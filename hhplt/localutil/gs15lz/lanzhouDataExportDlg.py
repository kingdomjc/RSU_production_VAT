#encoding:utf-8
'''
Created on 2015-4-30
兰州数据导出的本地工具对话框

@author: user
'''

import time
from PyQt4 import QtGui, QtCore, uic
from PyQt4.Qt import pyqtSlot
from PyQt4.QtGui import QMessageBox

from hhplt.parameters import PARAM,SESSION,GLOBAL

from hhplt.utils import isEmptyString

from hhplt.testengine.localdb import queryFromLocalDb

class LanzhouDataExportDlg(QtGui.QDialog):
    '''兰州生产数据导出工具对话框'''
    def __init__(self,parent):
        super( LanzhouDataExportDlg, self ).__init__(parent=parent)
        uic.loadUi( "hhplt/localutil/gs15lz/lanzhouDataExport.ui", self )
        
    @pyqtSlot()
    def on_closeBtn_clicked(self):
        self.hide()
    
    def __getDefaultSaveFilename(self):
        filenameSerial = PARAM["exportCsvSerial"] + 1
        PARAM["exportCsvSerial"] = filenameSerial
        PARAM.dumpParameterToLocalFile()
        return "TagPreEnter_%s_%.3d.csv"%(time.strftime('%Y%m%d',time.localtime(time.time())),filenameSerial)
    
    def __getExportParam(self):
        '''生成导出参数，返回值：pidStart,pidEnd,保存文件名，如果失败，则返回None,None,None'''
        pidStart = self.pidStart.text()
        pidEnd = self.pidEnd.text()
        if isEmptyString(pidStart) or isEmptyString(pidEnd):
            QMessageBox.warning(None,u"数据导出",u"请输入PID的起止号段进行导出",u"确定")
        else:
            fn = QtGui.QFileDialog.getSaveFileName(self,u"保存记录","/"+self.__getDefaultSaveFilename(), u"CSV文件 (*.csv);;所有文件(*.*)")
            if fn != '':
                return pidStart,pidEnd,fn
        return None,None,None
                
    @pyqtSlot()
    def on_generateCsvBtn_clicked(self):    #不通过数据库，直接生成csv文件
        pidStart,pidEnd,fn = self.__getExportParam()
        if fn is None:return
        csvf = open(fn,'w')
        try:
            for pidnum in range(int(pidStart[2:]),int(pidEnd[2:])+1):
                pid = PARAM["manufacturerId"] + "%.6d"%pidnum
                epc = pid+"0"*(24-len(pid))
                boxId = PARAM["manufacturerId"] + "%.5d"%((pidnum-1)/20 + 1)
                itemStr = ",".join([epc,pid,"6C",boxId])
                csvf.write("%s\n"%itemStr)
        finally:
            csvf.close()
            QMessageBox.information(None,u"数据导出完成",u"数据导出完成，保存在%s"%fn,u"确定")
        
    @pyqtSlot()
    def on_exportBtn_clicked(self): #通过数据库生成CSV文件
        pidStart,pidEnd,fn = self.__getExportParam()
        if fn is None:return
        csvf = open(fn,'w')
        
        #增加缺失校验
        toExportWhole = [PARAM["manufacturerId"] + "%.6d"%pidnum for pidnum in range(int(pidStart[2:]),int(pidEnd[2:])+1)]
        
        def saveToCsvFile(item):
            boxId = PARAM["manufacturerId"] + "%.5d"%((int(item[0][2:])-1)/20 + 1)
            itemStr = ",".join([item[2],item[0],"6C",boxId])
            csvf.write("%s\n"%itemStr)
            toExportWhole.remove(item[0])

        self.exportBtn.setText(u"正在导出...")
        self.exportBtn.setDisabled(True)
        try:
            queryFromLocalDb(u"GS15 UHF卡兰州电子车牌", "PID", [pidStart,pidEnd], ["EPC"], saveToCsvFile)
            csvf.close()
            if len(toExportWhole) == 0:
                QMessageBox.information(None,u"数据导出完成",u"数据导出完成，保存在%s"%fn,u"确定")
            else:
                QMessageBox.warning(None,u"数据导出完成",u"数据导出完成，以下PID标签缺失:%s\n请检查"%(
                                            ",".join(toExportWhole)),u"确定")
        except Exception,e:
            print e
        finally:
            self.exportBtn.setText(u"导出CSV文件")
            self.exportBtn.setDisabled(False)



        