#encoding:utf-8
u'''
从文件中读取变化EPC，镭雕
请构造CSV文件，文件中含有两列，第一列为镭雕号码，第二列为EPC码。系统将自动读取该文件并逐一写入
'''

suiteName = u'''6-成品-从文件中读取并写EPC镭雕'''
version = "1.0"
failWeightSum = 10  #整体不通过权值，当失败权值和超过此，判定测试不通过


import uhf_tag_board,uhf_tag_variableepc_without_carve,uhf_tag_fixepc_with_carve,uhf_tag_fixepc_without_carve
from hhplt.testengine.manul import askForSomething,showDashboardMessage,manulCheck
from hhplt.testengine.exceptions import TestItemFailException,AbortTestException
from hhplt.testengine.localdata import writeToLocalData
from hhplt.testengine.testcase import uiLog
import time
from hhplt.parameters import PARAM,SESSION,GLOBAL
import re

autoTrigger = uhf_tag_board.autoTrigger
setup = uhf_tag_board.setup
rollback = uhf_tag_board.rollback

oldTid = None

def rollback(product):
    '''回滚函数'''
    #增加一个逻辑，若操作不成功，则次数不累加，重新写此前累积的东西
    uhf_tag_variableepc_without_carve.rollback(product)
    uhf_tag_fixepc_with_carve.rollback(product)

def finalFun(product):
    #由于两层叠加次数，因此总次数会多出一倍，这里减一下
    uhf_tag_board.finalFun(product)
    
g_csvFile = None
currentLine = -1

def __loadCsvFile():
    from PyQt4 import QtCore, QtGui, uic
    fn = askForSomething(u"输入文件名路径",u"请输入您要读取的文件名",autoCommit=False)
    if fn == "":raise AbortTestException(message="用户取消了设置")
    uiLog(u"加载写码记录文件:"+fn)
    global g_csvFile
    g_csvFile = open(fn,'r')

def __readEpcAndCarveCodeFromFile():
    global g_csvFile,currentLine
    line = SESSION["currentLineInFile"] + 1
    SESSION["currentLineInFile"] = line
    dt = None
    if currentLine == -1:
        for i in range(line-2):
            g_csvFile.readline()
    currentLine = line
    dt = g_csvFile.readline().strip()
    if dt !="":
        return dt.split(",")
    else:
        del SESSION["configed"]
        g_csvFile.close()
        currentLine = -1
        raise AbortTestException("文件已读完，请重新开始并设值")
        
def T_01_paramSetting_M(product):
    u'''参数设置-首次运行进行参数设置'''
    if "configed" not in SESSION:
        SESSION["nowTimes"] = 0 
        SESSION["nowCarveTimes"] = 0
        __loadCsvFile()
        lineStart = askForSomething(u"从哪一行开始操作？",u"您需要从该文件的哪一行开始操作？",autoCommit=False,defaultValue='1')
        SESSION["currentLineInFile"] = int(lineStart)
        nn,ee = __readEpcAndCarveCodeFromFile()
        while not manulCheck(title=u"请确认即将开始的内容", content = u"镭雕码:%s\nEPC:%s\n是否确认"%(nn,ee)):
            global g_csvFile,currentLine
            g_csvFile.close()
            currentLine = -1
            __loadCsvFile()
            lineStart = askForSomething(u"从哪一行开始操作？",u"您需要从该文件的哪一行开始操作？",autoCommit=False,defaultValue='1')
            SESSION["currentLineInFile"] = int(lineStart)
            nn,ee = __readEpcAndCarveCodeFromFile()
            SESSION["nowVariableCarve"],SESSION["toWriteEpc"] = __readEpcAndCarveCodeFromFile()
        PARAM["repeatTimes"] = int(askForSomething(u"同EPC写入次数",u"同一EPC重复多少标签？例如4表示，待同一个EPC写够4个标签后，再进位到下一个EPC",autoCommit=False,defaultValue=PARAM["repeatTimes"]))
        PARAM["gs15userLength"] = int(askForSomething(u"USER区长度设置",u"请输入USER区长度，单位:字（WORD，1WORD = 2Byte = 16bit）",autoCommit=False,defaultValue=PARAM["gs15userLength"]))
        SESSION["nowTimes"] = 1
        PARAM.dumpParameterToLocalFile()
        
        SESSION["nowVariableCarve"],SESSION["toWriteEpc"] = nn,ee
        SESSION["configed"] = True
   
    if SESSION["nowTimes"] > PARAM["repeatTimes"]:
        SESSION["nowTimes"] = 1
        SESSION["nowVariableCarve"],SESSION["toWriteEpc"] = __readEpcAndCarveCodeFromFile()
    
    showDashboardMessage(u"即将写入EPC内容:%s\n    \
                    即将镭雕的内容:%s,第%d次/共%d次\n\
                    USER区长度:%d字"%  \
                         (SESSION["toWriteEpc"],
                          SESSION["nowVariableCarve"],
                          SESSION["nowTimes"],PARAM["repeatTimes"],
                          PARAM["gs15userLength"]))
    SESSION["nowTimes"] += 1 

T_02_inventoryTagAndTid_A = uhf_tag_variableepc_without_carve.T_02_inventoryTagAndTid_A
T_03_testWriteEpc_A = uhf_tag_variableepc_without_carve.T_03_testWriteEpc_A
T_04_testWriteUser_A = uhf_tag_variableepc_without_carve.T_04_testWriteUser_A
T_05_laserCarve_M = uhf_tag_fixepc_with_carve.T_05_laserCarve_M


