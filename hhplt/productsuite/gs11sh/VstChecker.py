#encoding:utf-8
"""
通过监听器检查BST的发射
@author:zws
"""
import binascii

import datetime
import time
from threading import Thread, Condition, RLock

from hhplt.deviceresource import TestResource, TestResourceInitException, askForResource
import ftd2xx





class VstChecker(TestResource,Thread):
    def __init__(self,initParam):
        Thread.__init__(self)
        self.monitor = None
        self.recvd = {}
        self.recvLock = RLock()

    def initResource(self):
        # 初始化资源
        usbDeviceList = ftd2xx.listDevices()
        print usbDeviceList
        if len(usbDeviceList) == 0: #未找到监听
            raise  TestResourceInitException(u"未找到监听设备")
        self.monitor = ftd2xx.openEx("TJKCHTBA")
        self.monitor.setTimeouts(10,10)
        self.start()

    def retrive(self):
        # 回收资源
        self.monitor.close()

    def prepareToTest(self):
        self.recvLock.acquire()
        self.recvd.clear()
        self.recvLock.release()
		
    def checkRecv(self,productSlot,recvTimes):
        for i in range(recvTimes):
            self.recvLock.acquire()
            if productSlot in self.recvd:
                self.recvLock.release()
                return True
            else:
                self.recvLock.release()
                time.sleep(0.2)
        return False

    def run(self):
        while True:
            try:
                dsrcData = self.__readFromMonitor()
                if dsrcData is None:continue
                else:
                    self.recvLock.acquire()
                    try:
                        self.recvd[dsrcData[7]] = dsrcData
                    finally:
                        self.recvLock.release()
            except Exception,e:
                print e
			

    def __readFromMonitor(self):
        try:
            result = self.monitor.read(1)
            if len(result) == 0:return
            if binascii.hexlify(result) == '55' and binascii.hexlify(self.monitor.read(1)) == 'aa':
                dsrc_length = self.monitor.read(1)
                dsrc_data = self.monitor.read(int(binascii.hexlify(dsrc_length), 16))
                dsrcHex = binascii.hexlify(dsrc_data)
                print dsrcHex
                return dsrcHex
        except ftd2xx.DeviceError,e:
            print e
            self.monitor.resetDevice()

def getVstChecker():
    # 获取集成工装板工具
    return askForResource("VstChecker",VstChecker)


if __name__ == '__main__':
    v = VstChecker()
    v.initResource()
    print 'vst checker'

    raw_input()

