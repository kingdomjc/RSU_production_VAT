#! /usr/bin/python
import Queue
import struct
import zmq
from PyQt4 import QtCore

class VmmThread(object):
    # vmmSignal = QtCore.pyqtSignal(str)

    def __init__(self):
        super(VmmThread, self).__init__()
        self.queue = Queue.Queue()


    def run(self):
        while True:
            cmd = self.queue.get()
            print cmd
            #head, path, ip = cmd.split(":",2)
            head = cmd[0:cmd.find(":")]
            path = cmd[cmd.find(":")+1:]
            try:
                if head == "sys":
                    self.m.downloadSysVersion(path)
                elif head == "app":
                    self.m.downloadAppVersion(path)
                elif head == "uboot":
                    pass
                else:
                    # self.vmmSignal.emit("error")
                    print "error"
            except Exception as e:
                print e
                # self.vmmSignal.emit("error")
                print "error"
            else:
                # self.vmmSignal.emit("end")
                print "end"

class VersionManagerException(Exception):
    pass


class VersionManager(object):
    def __init__(self,initParam):
        self.ip  = initParam["integratedVatBoardIp"]

    def initResource(self):
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.REQ)
        self.socket.connect("tcp://%s:10012" % self.ip)

    def queryVersion(self):
        self.socket.setsockopt(zmq.RCVTIMEO, 100)
        query = struct.pack("!II", 2, 0)
        self.socket.send(query, zmq.NOBLOCK, copy=False)
        response = self.socket.recv()
        id, result = struct.unpack("!II", response[0:8])
        if 0 != result:
            raise VersionManagerException()

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
        self.socket.setsockopt(zmq.RCVTIMEO, 600000)
        return ret

    def parseSysVersion(self, versionStr):
        start = versionStr.find("[") + 1
        end = versionStr.find("]")
        versionNum = versionStr[start:end]
        self.versionNum = versionNum
        versionStr = versionStr[end + 1:]
        start = versionStr.find("[") + 1
        end = versionStr.find("]")
        lsize = int(versionStr[start:end])
        self.lsize = lsize
        versionStr = versionStr[end + 1:]
        start = versionStr.find("[") + 1
        end = versionStr.find("]")
        rsize = int(versionStr[start:end])
        self.rsize = rsize
        versionStr = versionStr[end + 1:]
        start = versionStr.find("[") + 1
        end = versionStr.find("]")
        dsize = int(versionStr[start:end])
        self.dsize = dsize

    def sendVersionInfo(self, versionType, progress, versionStr):
        msgHead = struct.pack("!II", 1, 0)  # id, status
        headLen = struct.calcsize("!II") + struct.calcsize("!IIIII")
        versionInfo = struct.pack(
            "!IIIII", versionType, progress, 0, 0, len(versionStr) + headLen)
        self.socket.send(msgHead + versionInfo + versionStr)
        response = self.socket.recv()
        id, status = struct.unpack("!II", response[0:8])
        if status != 0:
            raise VersionManagerException()

    def sendContentFrame(self, versionType, progress, size):
        msgHead = struct.pack("!II", 1, 0)  # id, status
        headLen = struct.calcsize("!II") + struct.calcsize("!IIIII")

        for x in range(size / 1024):
            versionInfo = struct.pack(
                "!IIIII", versionType, progress, 1, self.num, 1024 + headLen)
            content = self.versionContent[self.versionPos: self.versionPos + 1024]
            self.socket.send(msgHead + versionInfo + content)
            self.num += 1
            self.versionPos += 1024
            response = self.socket.recv()
            id, status = struct.unpack("!II", response[0:8])
            if status != 0:
                raise VersionManagerException()

        tailLen = size % 1024
        if tailLen != 0:
            versionInfo = struct.pack(
                "!IIIII", versionType, progress, 1, self.num, tailLen + headLen)
            content = self.versionContent[self.versionPos: self.versionPos + tailLen]
            self.socket.send(msgHead + versionInfo + content)
            self.num += 1
            self.versionPos += tailLen
            response = self.socket.recv()
            id, status = struct.unpack("!II", response[0:8])
            if status != 0:
                raise VersionManagerException()

    def sendEndFrame(self, versionType, progress, size):
        msgHead = struct.pack("!II", 1, 0)  # id, status
        headLen = struct.calcsize("!II") + struct.calcsize("!IIIII")

        tailLen = size % 1024
        for x in range(size / 1024):
            if (tailLen == 0) and (x == size / 1024 - 1):
                versionInfo = struct.pack(
                    "!IIIII", versionType, progress, 2, self.num, 1024 + headLen)
            else:
                versionInfo = struct.pack(
                    "!IIIII", versionType, progress, 1, self.num, 1024 + headLen)
            content = self.versionContent[self.versionPos: self.versionPos + 1024]
            self.socket.send(msgHead + versionInfo + content)
            self.num += 1
            self.versionPos += 1024
            response = self.socket.recv()
            id, status = struct.unpack("!II", response[0:8])
            if status != 0:
                raise VersionManagerException()

        if tailLen != 0:
            versionInfo = struct.pack(
                "!IIIII", versionType, progress, 2, self.num, tailLen + headLen)
            content = self.versionContent[self.versionPos: self.versionPos + tailLen]
            self.versionPos += tailLen
            self.socket.send(msgHead + versionInfo + content)
            response = self.socket.recv()
            id, status = struct.unpack("!II", response[0:8])
            if status != 0:
                raise VersionManagerException()

    def downloadKernel(self):
        self.num = 0
        self.sendContentFrame(1, 1, self.lsize)

    def downloadRamdisk(self):
        self.sendContentFrame(1, 2, self.rsize)

    def downloadDtb(self):
        self.sendEndFrame(1, 3, self.dsize)

    def downloadSysVersion(self, filePath):
        '''
        msg head:
            int message id
            int result
        version info:
            int version type  0:app 1:system
            int downloadprogress 0:app 1:linux 2:ramdisk 3:dtb
            int frametype 0:version info 1:version content 2: end
            int num
            int length  msghead + versioninfo + framecontent
        '''
        fd = open(filePath, "rb")
        self.versionContent = fd.read()
        versionStr = self.versionContent[0:1024]
        self.versionPos = 1024
        self.parseSysVersion(versionStr)
        self.sendVersionInfo(1, 1, versionStr)
        print "start download kernel"
        self.downloadKernel()
        print "download kernel success"
        self.downloadRamdisk()
        print "download ramdisk success"
        self.downloadDtb()
        print "download dtb success"
        fd.close()

    def downloadAppVersion(self, filePath):
        self.fd = open(filePath, "rb")
        self.versionContent = self.fd.read()
        versionStr = self.versionContent[0:1024]
        self.versionPos = 1024
        self.sendVersionInfo(0, 0, versionStr)
        self.num = 1
        self.sendEndFrame(0, 0, len(self.versionContent) - 1024)
        self.fd.close()

    def downloadBootVersion(self, filePath):
        pass

    def switchVersion(self):
        switch = struct.pack("!II", 3, 0)
        self.socket.send(switch)
        response = self.socket.recv()
        id, result = struct.unpack("!II", response[0:8])
        if result != 0:
            raise VersionManagerException()

    def unswitchVersion(self):
        switch = struct.pack("!II", 4, 0)
        self.socket.send(switch)
        response = self.socket.recv()
        id, result = struct.unpack("!II", response[0:8])
        if result != 0:
            raise VersionManagerException()

    def rebootReader(self):
        switch = struct.pack("!II", 100, 0)
        self.socket.send(switch)
        response = self.socket.recv()

    def close(self):
        self.socket.close()
