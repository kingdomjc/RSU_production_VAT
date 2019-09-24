#encoding:utf-8
'''
Created on 2014-12-20
导入旧的ESAM数据到数据库中
@author: user
'''
import xlrd
from hhplt.productsuite.gs10.board_digital import __checkAndPersistEsamId
import os
from hhplt.parameters import SESSION,GLOBAL
import time

class _WndMock:
    def emit(self,*p):
        for msg in p:
            print msg
        
GLOBAL["mainWnd"]=_WndMock()
#SESSION["serverIp"] = "127.0.0.1"
SESSION["serverIp"] = "192.168.1.179"

XLS_PATH = u"D:/201412OBU生产发货/"

def generateItemList(xlsFileName):
    data = xlrd.open_workbook(xlsFileName)
    items = []
    for table in data.sheets():
        for i in range(table.nrows):
            row = table.row_values(i)
            if row[0] == u'镭雕条码':
                continue
            items.append(row)
    return items

def importItem(item):
    try:
        __checkAndPersistEsamId(item[1],item[3])
        time.sleep(0.1)
    except Exception,e:
        print 'error in importing:',e.message,item[1],item[3]


if __name__ == '__main__':
#    fileList = filter(lambda x:x.endswith(".xls") or x.endswith(".xlsx"),os.listdir(XLS_PATH))
    fileList = ['0-100 200-300.xlsx']
    if len(fileList) == None:
        print "No xls files"
    
    for f in fileList:
        itemList = generateItemList(XLS_PATH+f)
        i = 0
        print "start importing %s,with %d items..."%(f,len(itemList))
        for item in itemList:
            importItem(item)
            i = i+1
            if i % 100 == 0:
                print 'imported:%d'%i
    
    print 'finished,please check db'
    
