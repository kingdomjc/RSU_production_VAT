#encoding:utf-8
'''
Created on 2014-12-17
发货前的重复检测
@author: user
'''

import xlrd 
import codecs
OUTPUT_FILE = "output.txt"
TO_VALIDATE_TABLE = "toValidate.xls"

esamPool = set()
macPool = set()

toValidateItemList = []

def writeToOutput(info):
    print 'find duplidated:',info
    f = codecs.open(OUTPUT_FILE,'a','utf-8')
    f.write(info)
    f.write("\r\n")
    f.close()
    
def validate(item):
    '''校验一条是否重复，数据格式[镭雕条码  , MAC地址,合同序列号 , ESAM序号]'''
    if item[1] in macPool:
        return "\t".join(item)+u"\tMAC地址重复"
    elif item[2] in esamPool:
        return "\t".join(item)+u"\tESAM重复"
    else:
        macPool.add(item[1])
        esamPool.add(item[2])

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

def initPool():
    '''初始化样本池'''
    import os
    fileList = filter(lambda x:x.endswith(".xls") or x.endswith(".xlsx"),os.listdir(os.getcwd()))
    if len(fileList) == None:
        print "No xls files"
        return
    print 'Already existed table files:'
    for i in range(len(fileList)):
        print i,fileList[i]
    print "Which to be valiated ? Others are patterns for reference:"
    toValidateFileName = fileList[int(raw_input())]
    print 'to Validate %s'%toValidateFileName
    for f in fileList:
        if f == toValidateFileName:
            global toValidateItemList
            toValidateItemList = generateItemList(f)
        else:
            items = generateItemList(f)
            for item in items:
                macPool.add(item[1])
                esamPool.add(item[2])

if __name__ == '__main__':
    initPool()
    print u"sample amount mac=%d,esam=%d,to validate:%s"%(len(macPool),len(esamPool),len(toValidateItemList))
    print "start validating..."
    for item in toValidateItemList:
        validateResult = validate(item)
        if validateResult != None:
            writeToOutput(validateResult)
    print "finished! Please check file:%s"%OUTPUT_FILE
    raw_input()


