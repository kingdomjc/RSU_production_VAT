# encoding:utf-8
'''
Created on 2019-6-21
查询版本号
'''
import struct
import zmq

from hhplt.deviceresource import TestResource, TestResourceInitException


class VersionManager(TestResource):

    def __init__(self, initParam):
        self.ip = initParam
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.REQ)
        self.socket.connect("tcp://%s:10012" % self.ip)
        self.socket.setsockopt(zmq.RCVTIMEO, 100)


    def queryVersion(self):
        query = struct.pack("!II", 2, 0)
        self.socket.send(query, zmq.NOBLOCK, copy=False)
        response = self.socket.recv()
        id, result = struct.unpack("!II", response[0:8])
        if 0 != result:
            raise TestResourceInitException(u'查询版本失败，请检查配置')

        sysRuning, switchStatus = struct.unpack("!II", response[8:16])
        appRuningVersionNum = struct.unpack("!BBBB", response[16:20])
        appDownloadVersionNum = struct.unpack("!BBBB", response[20:24])
        sys0Version = struct.unpack("!BBBB", response[24:28])
        sys1Version = struct.unpack("!BBBB", response[28:32])
        ret = {}
        ret["sysRuning"] = sysRuning
        ret["switchStatus"] = switchStatus
        appRuningVersionNum = "%d.%02d.%02d" % (
            appRuningVersionNum[0], appRuningVersionNum[1], appRuningVersionNum[2])
        appDownloadVersionNum = "%d.%02d.%02d" % (
            appDownloadVersionNum[0], appDownloadVersionNum[1], appDownloadVersionNum[2])
        sys0VersionNum = "%d.%02d.%02d" % (
            sys0Version[0], sys0Version[1], sys0Version[2])
        sys1VersionNum = "%d.%02d.%02d" % (
            sys1Version[0], sys1Version[1], sys1Version[2])
        ret["appRuningVersionNum"] = appRuningVersionNum
        ret["appDownloadVersionNum"] = appDownloadVersionNum
        ret["sys0VersionNum"] = sys0VersionNum
        ret["sys1VersionNum"] = sys1VersionNum
        return ret

    def rebootReader(self):
        switch = struct.pack("!II", 100, 0)
        self.socket.send(switch)
        response = self.socket.recv()


    def close(self):
        self.socket.close()