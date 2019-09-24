#encoding:utf-8
'''
Created on 2015-9-2
版本容器
用于与服务端交互获得版本，并提供版本文件
脚本文件在/versions下面
@author: user
'''
from ftplib import FTP
import os
from hhplt.parameters import PARAM,SESSION
from hhplt.testengine.manul import autoCloseAsynMessage
import thread
from hhplt.testengine.exceptions import AbortTestException


def __downloadFromServer(filename):
    '''从FTP上下载文件'''
    downloading = True
    def download():
        try:
            ftp = FTP()
            ftp.connect(PARAM["defaultServerIp"], PARAM["centerFtpPort"])
            ftp.login(PARAM["centerFtpUsername"],PARAM["centerFtpPassword"])
            f = open("fromftp.txt",'w')         # 打开要保存文件  
            filename = 'RETR %s'%filename   # 保存FTP文件  
            ftp.retrbinary(filename,f.write) # 保存FTP上的文件
            f.close()
            downloading = False
        finally:
            pass
    thread.start_new_thread(download,())
    autoCloseAsynMessage(u"版本下载",u"从中心服务下载版本:"+filename,lambda:not downloading,timeout = 10)

def getVersionFile(versionFileName):
    '''获得版本文件'''
    vf = "versions"+os.sep+versionFileName
    if os.path.exists(vf):
        return vf
    if SESSION["testor"] != u"单机":
        __downloadFromServer(versionFileName)
        if os.path.exists(vf):return vf
    raise AbortTestException(u"找不到版本文件，且无法下载:"+versionFileName)




