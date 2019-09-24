#encoding:utf-8
"""
模块:安的RD201驱动
用于测试标签清点情况

@author:zws
"""
import time

from hhplt.deviceresource import TestResource, TestResourceInitException
from ctypes import *

class RD201Driver(TestResource):

    def __init__(self,param):
        self.dll = None
        self.iso15693dll = None
        self.param = param
        self.setting = False

    def initResource(self):
        # 初始化资源
        try:
            self.dll = windll.LoadLibrary("rfidlib_reader.dll")
            self.iso15693dll = windll.LoadLibrary("rfidlib_aip_iso15693.dll")
            self.rfidHandle = c_void_p()
            ret = self.dll.RDR_LoadReaderDrivers(u"HrDrivers")
            deviceStr = u"RDType=RD201;CommType=COM;COMName=%s;BaudRate=38400;Frame=8E1;BusAddr=255"%self.param["readerCom"]
            iret = self.dll.RDR_Open(deviceStr ,byref(self.rfidHandle))
            if iret != 0:
                print "init reader ,ret=",iret
                raise TestResourceInitException(u"初始化阅读器失败:%d"%iret)
        except Exception,e:
            import traceback
            print traceback.format_exc()
            raise e

    def retrive(self):
        # 回收资源
        self.dll.RDR_Close(self.rfidHandle)

    def inventoryTags(self):
        # 清点标签，返回所有标签的Set
        resultSet = set()
        dnInvenParamList = self.dll.RDR_CreateInvenParamSpecList()
        if dnInvenParamList:
            self.iso15693dll.ISO15693_CreateInvenParam(dnInvenParamList,0,0,0,0)
        iret = self.dll.RDR_TagInventory(self.rfidHandle,1,0,None,dnInvenParamList)
        if iret == 0:   #读取成功，获取读到的卡片的序列号
            dnhReport = self.dll.RDR_GetTagDataReport(self.rfidHandle,1)    #RFID_SEEK_FIRST = 1
            while dnhReport != 0:   #RFID_HANDLE_NULL=0
                aipId,tagId,antId = c_int32(0),c_int32(0),c_int32(0)
                dsfid = c_byte()
                uid = create_string_buffer(8)
                iret = self.iso15693dll.ISO15693_ParseTagDataReport(dnhReport,byref(aipId),byref(tagId),byref(antId),byref(dsfid),byref(uid))
                if iret == 0: resultSet.add(uid.raw.encode("hex")) # 卡片号在UID中
                dnhReport = self.dll.RDR_GetTagDataReport(self.rfidHandle,2)    #RFID_SEEK_FIRST = 1
            if dnInvenParamList:self.dll.DNODE_Destroy(dnInvenParamList)
            return resultSet
        else:
            return resultSet

if __name__ == '__main__':
     rd201 = RD201Driver({"readerCom":"COM7"})
     rd201.initResource()
     while True:
         tags = rd201.inventoryTags()

     rd201.retrive()

