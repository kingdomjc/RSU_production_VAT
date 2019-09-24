#encoding:utf-8
'''
Created on 2015-9-2
GS11 NuLink Flash写入工具
使用此资源，需要NuLink.exe和配套的4个.a文件都放置在HHPLT下面
因为TMD这个破玩意必须以它老巢当工作路径，才能执行成功。Path或指定绝对路径都TMD不好使。
@author: user
'''

from hhplt.deviceresource import TestResource,TestResourceInitException
from hhplt.deviceresource import AbortTestException,TestItemFailException
import time
from hhplt.testengine.testcase import uiLog,superUiLog
from hhplt.parameters import PARAM
import os
from hhplt import utils

class GS11NuLink(TestResource):
    def __init__(self,initParam):
        self.nulinkId = None
    
    def initResource(self):
        dr = self.__nulinkCmd("-l")
        print dr
        self.nulinkId = dr.split("\n")[0][-10:]
        superUiLog(u"获取NuLinkID:"+self.nulinkId)
    
    def retrive(self):
        pass
    
    def __nulinkCmd(self,cmd):
        '''执行NuLink指令'''
        if self.nulinkId is None:self.nulinkId=""
        fullCmd = "NuLink.exe "+self.nulinkId+ " " +cmd
        superUiLog(u"执行NuLink指令:"+fullCmd)
        r = os.popen(fullCmd)
        dr = r.read()
        print dr
        return dr.strip()
    
    def initCfg(self):
        '''初始化CFG'''
        dr = self.__nulinkCmd("-w CFG0 0xFFFFFFFE")
        if "Finish write to CFG0" in dr:uiLog(u"写config0成功")
        else:raise TestItemFailException(failWeight=10,message=u"初始化config0失败")
        dr = self.__nulinkCmd("-w CFG1 0x0000FE00")
        if "Finish write to CFG1" in dr:uiLog(u"写config1成功")
        else:raise TestItemFailException(failWeight=10,message=u"初始化config0失败")
    
    def downloadVersion(self,versionPathName,verify=True):
        '''下载版本'''
        #检查config
        uiLog(u"开始检查CFG")
        dr = self.__nulinkCmd("-r CFG0")
        if "0xFFFFFFFE" not in dr:
            self.initCfg()
        else:    
            dr = self.__nulinkCmd("-r CFG1")
            if "0x0000FE00" not in dr:
                self.initCfg()
        
        #擦除版本文件
        uiLog(u"开始擦除版本区")
        dr = self.__nulinkCmd("-e APROM")
        if "Erase APROM finish" in dr:
            uiLog(u"擦除版本区完成，开始写入版本")
        else:
            raise TestItemFailException(failWeight=10,message=u"版本区擦除失败")
        #下载版本文件
        dr = self.__nulinkCmd("-w APROM %s"%versionPathName)
        if "Write APROM finish" in dr:
            uiLog(u"版本信息下载完成，开始校验")
        else:
            raise TestItemFailException(failWeight=10,message=u"版本区写入失败")
        #校验版本下载
        if verify:
            dr = self.__nulinkCmd("-v APROM %s"%versionPathName)
            if "Verify APROM DATA success" in dr:
                uiLog(u"版本校验通过")
            else:
                raise TestItemFailException(failWeight=10,message=u"版本区校验失败")
    
    def writeToInfo(self,CONFIG_BUILD_INFO,CONFIG_RF_PARA):
        '''写入信息区，入参是两个信息段，是HEX字符串'''
        toWriteFileInHex = CONFIG_BUILD_INFO+"ff"*48+CONFIG_RF_PARA
        toWriteFileInByte = bytearray([int(toWriteFileInHex[h:h+2],16) for h in range(0,len(toWriteFileInHex),2)])
        hxfile = open("infoData.bin","wb")
        hxfile.write(toWriteFileInByte)
        hxfile.close()
        #擦除Info区
        uiLog(u"开始擦除信息区")
        dr = self.__nulinkCmd("-e DATAROM")
        if "Erase DATAROM finish" in dr:
            uiLog(u"擦除信息区成功")
        else:
            raise TestItemFailException(failWeight=10,message=u"信息区擦除失败")
        
        #写Info区
        uiLog(u"开始写入信息区内容")
        dr = self.__nulinkCmd("-w DATAROM infoData.bin")
        if "Write DATAROM finish" in dr:
            uiLog(u"信息区内容写入完成")
        else:
            raise TestItemFailException(failWeight=10,message=u"信息区写入失败:")
    
    def readInfo(self):
        '''读取信息区，返回整个信息区内容（128byte）的hex符号字符串，即256个字节'''
        TEMP_FILE = "infoData.bin"
        dr = self.__nulinkCmd("-r DATAROM %s"%TEMP_FILE)
        try:
            if "Write DATAROM to FILE: %s Finish"%TEMP_FILE in dr:
                f = open(TEMP_FILE,"rb")
                data = f.read(128)
                f.close()
                return utils.toHex(data)
            else:
                raise TestItemFailException(failWeight=10,message=u"信息区读出失败:")
        finally:
            if os.path.isfile(TEMP_FILE):os.remove(TEMP_FILE)
    
    def resetChip(self):
        '''复位芯片'''
        dr = self.__nulinkCmd("-reset")
        print dr
        if "Chip Reset finish" in dr:
            return
        else:
            raise TestItemFailException(failWeight=10,message=u"芯片复位失败")

        
    
    
    
    
