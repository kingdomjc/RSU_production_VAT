#encoding:utf-8
'''
Created on 2015-11-8
GS11生产辅助工具
@author: user
'''
from Tkinter import *
import tkMessageBox
import thread
import time
import os

versionText = None
global versionText,sensiText

def __toHex(ba):
    return "".join(["%.2X"%(ord(x) if isinstance(x,str) else x) for x in ba])

def __nulinkCmd(cmd):
    '''执行NuLink指令'''
    fullCmd = "NuLink.exe " +cmd
    print u"执行NuLink指令:"+fullCmd
    r = os.popen(fullCmd)
    dr = r.read()
    print dr
    return dr.strip()

def __readInfo():
    TEMP_FILE = "infoData.bin"
    dr = __nulinkCmd("-r DATAROM %s"%TEMP_FILE)
    try:
        if "Write DATAROM to FILE: %s Finish"%TEMP_FILE in dr:
            f = open(TEMP_FILE,"rb")
            data = f.read(128)
            f.close()
            return __toHex(data)
        else:
            raise Exception(u"信息区读出失败:")
    finally:
        if os.path.isfile(TEMP_FILE):os.remove(TEMP_FILE)


def readInfo():
    try:
        oriData = __readInfo()
        print u'信息区:',oriData
    except Exception,e:
        print e.message
    
def __writeToInfo(CONFIG_BUILD_INFO,CONFIG_RF_PARA):
    '''写入信息区，入参是两个信息段，是HEX字符串'''
    toWriteFileInHex = CONFIG_BUILD_INFO+"ff"*48+CONFIG_RF_PARA
    toWriteFileInByte = bytearray([int(toWriteFileInHex[h:h+2],16) for h in range(0,len(toWriteFileInHex),2)])
    hxfile = open("infoData.bin","wb")
    hxfile.write(toWriteFileInByte)
    hxfile.close()
    #擦除Info区
    print u"开始擦除信息区"
    dr = __nulinkCmd("-e DATAROM")
    if "Erase DATAROM finish" in dr:
        print u"擦除信息区成功"
    else:
        raise Exception(u"信息区擦除失败")
    
    #写Info区
    print u"开始写入信息区内容"
    dr = __nulinkCmd("-w DATAROM infoData.bin")
    if "Write DATAROM finish" in dr:
        print u"信息区内容写入完成"
    else:
        raise Exception(u"信息区写入失败:")


def writeSensi():
    global sensiText
    try:
        sensi = sensiText.get()
        oriData = __readInfo()
        CONFIG_BUILD_INFO = oriData[:32]
        CONFIG_RF_PARA = oriData[128:154]
        CONFIG_RF_PARA = CONFIG_RF_PARA[:8]+ sensi + CONFIG_RF_PARA[16:]
        __writeToInfo(CONFIG_BUILD_INFO, CONFIG_RF_PARA)
    except Exception,e:
        print e.message

def __setDirect(directText):
    try:
        oriData = __readInfo()
        print u'原信息区',oriData
        CONFIG_BUILD_INFO = oriData[:32]
        CONFIG_RF_PARA = oriData[128:154]    
        CONFIG_BUILD_INFO = CONFIG_BUILD_INFO[:16]+directText+CONFIG_BUILD_INFO[18:]
        __writeToInfo(CONFIG_BUILD_INFO, CONFIG_RF_PARA)
    except Exception,e:
        print e.message

def setDirect00():
    __setDirect("00")

def setDirect01():
    __setDirect("01")

def __downloadVersion(versionPathName,verify=True):
    '''下载版本'''
    #擦除版本文件
    print u"开始擦除版本区"
    dr = __nulinkCmd("-e APROM")
    if "Erase APROM finish" in dr:
        print u"擦除版本区完成，开始写入版本"
    else:
        raise Exception(u"版本区擦除失败")
    #下载版本文件
    dr = __nulinkCmd("-w APROM %s"%versionPathName)
    if "Write APROM finish" in dr:
        print u"版本信息下载完成，开始校验"
    else:
        raise Exception(u"版本区写入失败")
    #校验版本下载
    if verify:
        dr = __nulinkCmd("-v APROM %s"%versionPathName)
        if "Verify APROM DATA success" in dr:
            print u"版本校验通过"
        else:
            raise Exception(u"版本区校验失败")

def downloadVersion():
    global versionText
    filename = versionText.get()
    softwareVersion = "".join(filename.split("-")[2].split(".")[:3])+"00"
    try:
        __downloadVersion(filename)
        print u'开始写入版本号:',softwareVersion
        oriData = __readInfo()
        CONFIG_BUILD_INFO = oriData[:32]
        CONFIG_RF_PARA = oriData[128:154]
        CONFIG_BUILD_INFO = CONFIG_BUILD_INFO[:18] + softwareVersion + CONFIG_BUILD_INFO[26:]
        __writeToInfo(CONFIG_BUILD_INFO,CONFIG_RF_PARA)
    except Exception,e:
        print e.message
    
def startMainWnd():
    top = Tk()
    top.wm_title(u"GS11生产辅助工具")
    
    Button(top,text=u'读出信息区',command = readInfo).pack()
    
    Button(top,text=u'显示方向设为00',command = setDirect00).pack()
    Button(top,text=u'显示方向设为01',command = setDirect01).pack()

    global versionText,sensiText
    versionText = Entry(top,width = 38)
    versionText.insert(0, u'在此处输入需要下载的版本文件名')
    versionText.pack()
    Button(top,text=u'下载版本',command = downloadVersion).pack()
    
    sensiText = Entry(top,width=38)
    sensiText.insert(0, u'在此处输入需要写入的灵敏度值')
    sensiText.pack()
    Button(top,text=u"写入灵敏度参数",command=writeSensi).pack()
    mainloop()

if __name__ == '__main__':
    startMainWnd()