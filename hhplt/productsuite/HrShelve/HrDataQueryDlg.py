#encoding:utf-8
"""
模块: 数据查询

@author:zws
"""
from PyQt4 import QtCore

import xlsxwriter
from PyQt4 import QtGui
from PyQt4 import uic
from PyQt4.QtCore import pyqtSlot
from hhplt.testengine.localdb import queryFromLocalDb,queryFromLocalDbByTime


class HrDataQueryDlg(QtGui.QDialog):

    ITEM_PRODUCT_SELECT = [u"海尔-高频阅读器板",u"海尔-功分器",u"海尔-托盘天线",u"海尔-举例子玩"]
    ITEM_DB_SELECT = [u"hfReaderBoard.db",u"powerDivider.db",u"antenna.db",u"mockPr.db"]
    ITEM_OUTPUT_SELECT = [[u"发射功率"],
                          [u"端口1-S22回损",u"端口1-S21差损",u"端口2-S22回损",u"端口2-S21差损",u"端口3-S22回损",u"端口3-S21差损",u"端口4-S22回损",u"端口4-S21差损",
                           u"端口5-S22回损",u"端口5-S21差损",u"端口6-S22回损",u"端口6-S21差损",u"端口7-S11回损"],
                          [u"marker1-S11值",u"marker2-S11值",u"marker3-S11值",u"marker4-S11值",u"marker5-S11值",u"marker6-S11值",u"marker6-频率值"],
                          [u"端口1-S11回损"]]


    def __init__(self,parent):
        QtGui.QDialog.__init__(self,parent = parent)
        uic.loadUi( "hhplt/productsuite/HrShelve/hrDataQueryDlg.ui", self )
        self.setWindowTitle(u"海尔托盘数据查询")


    @pyqtSlot()
    def on_exportExcelBtn_clicked(self):
        fn = QtGui.QFileDialog.getSaveFileName(self, u"导出记录", "/", u"Excel文件(*.xlsx);;所有文件(*.*)")
        if fn == '':return
        workbook = xlsxwriter.Workbook(unicode(fn))
        headFormat = workbook.add_format({"bold": True, "bg_color": "#DBDBDB"})
        sheet = workbook.add_worksheet(unicode(self.boardSelect.currentText()))

        sheet.write_row("A1",[unicode(self.resTable.horizontalHeaderItem(i).text()) for i in range(self.resTable.columnCount())], headFormat)  # 填写表头

        row = 0
        while row < self.resTable.rowCount():
            sheet.write_row("A%d"%(row+2),[unicode(self.resTable.item(row,i).text()) for i in range(self.resTable.columnCount())])
            row += 1
        workbook.close()
        QtGui.QMessageBox.information(self,u"导出记录",u"导出记录完成")


    def __clearTable(self):
        for i in range(self.resTable.columnCount()):
            self.resTable.removeColumn(0)
        for i in range(self.resTable.rowCount()):
            self.resTable.removeRow(0)

    @pyqtSlot()
    def on_queryBtn_clicked(self):
        codeScope = (str(self.startBarCode.text()),str(self.endBarCode.text()))

        #codeScope = (str(self.startBarCode.text()).zfill(10),str(self.endBarCode.text()).zfill(10))
        #if int(codeScope[1]) - int(codeScope[0]) > 500:
        #    QtGui.QMessageBox.information(self,u"查询",u"请限制条码范围小于500个，否则查询速度挺慢的。")        
        #    return

        indx = self.boardSelect.currentIndex()
        productName = self.ITEM_PRODUCT_SELECT[indx]
        res = queryFromLocalDb(productName,u"单板条码",codeScope , self.ITEM_OUTPUT_SELECT[indx],None,self.ITEM_DB_SELECT[indx])

        self.__clearTable()


        head = [u"单板条码",u"测试时间",u"测试结论"]
        for i in range(3):
            self.resTable.insertColumn(i)
            self.resTable.setHorizontalHeaderItem(i,QtGui.QTableWidgetItem(head[i]))

        column = 3
        for title in self.ITEM_OUTPUT_SELECT[indx]:
            self.resTable.insertColumn(column)
            self.resTable.setHorizontalHeaderItem(column,QtGui.QTableWidgetItem(title))
            column += 1

        row = 0
        for record in res:
            self.resTable.insertRow(row)
            column = 0
            for r in record[1:]:
                self.resTable.setItem(row,column,QtGui.QTableWidgetItem(str(r)))
                column += 1

            # 测试结果标出来
            self.resTable.item(row,2).setBackgroundColor(QtCore.Qt.green if record[3] == "OK" else QtCore.Qt.red)

            row += 1
        # print res



    @pyqtSlot()
    def on_queryByTimeBtn_clicked(self):
        # 按时间查询

        indx = self.boardSelect.currentIndex()
        productName = self.ITEM_PRODUCT_SELECT[indx]

        startTime,endTime = str(self.startTestTime.text()),str(self.endTestTime.text())
        res = queryFromLocalDbByTime(productName,startTime,endTime, self.ITEM_OUTPUT_SELECT[indx],None,self.ITEM_DB_SELECT[indx])

        self.__clearTable()

        head = [u"单板条码",u"测试时间",u"测试结论"]
        for i in range(3):
            self.resTable.insertColumn(i)
            self.resTable.setHorizontalHeaderItem(i,QtGui.QTableWidgetItem(head[i]))

        column = 3
        for title in self.ITEM_OUTPUT_SELECT[indx]:
            self.resTable.insertColumn(column)
            self.resTable.setHorizontalHeaderItem(column,QtGui.QTableWidgetItem(title))
            column += 1

        row = 0
        for record in res:
            self.resTable.insertRow(row)
            column = 0
            for r in record:
                self.resTable.setItem(row,column,QtGui.QTableWidgetItem(str(r)))
                column += 1

            # 测试结果标出来
            self.resTable.item(row,2).setBackgroundColor(QtCore.Qt.green if record[2] == "OK" else QtCore.Qt.red)

            row += 1





