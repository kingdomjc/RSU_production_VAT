# encoding:utf-8
'''
Created on 2019-5-9
RD50C控制天线开关
'''
import socket
import struct

from hhplt.deviceresource import TestResourceInitException, TestResource
from hhplt.deviceresource.codec_ff import EtcCodec


class RSUTradeTest(TestResource):
    def __init__(self,BoardIp,BoardPort):
        self.ip = BoardIp
        self.port = BoardPort
        self.codec = EtcCodec()
        self.initResource()

    def initResource(self):
        try:
            self.fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.fd.settimeout(1)
            self.fd.connect((self.ip, self.port))
        except:
            raise TestResourceInitException(u'初始化RD50C控制板失败，请检查设置并重启软件')

    def sendFrame(self, data):
        raw_frame = self.codec.encode(data)
        self.fd.send(raw_frame)

    def recvFrame(self):
        raw_frame = self.fd.recv(1024)
        if raw_frame:
            data = self.codec.decode(raw_frame)
            if data:
                return data

    def open_ants(self):
        cmd = struct.pack("!BB", 0x80, 1)
        self.sendFrame(cmd)
        ack = self.recvFrame()
        if not ack or ack[0] != '\x90':
            raise TestResourceInitException(u'打开天线失败，请检查工装连接是否正常')
        return

    def close_ants(self):
        cmd = struct.pack("!BB", 0x80, 2)
        self.sendFrame(cmd)
        ack = self.recvFrame()
        if not ack or ack[0] != '\x90':
            raise TestResourceInitException(u'关闭天线失败，请检查工装连接是否正常')
        return

    def reboot(self):
        switch = struct.pack("!II", 100, 0)
        self.fd.send(switch)
        # response = self.fd.recv()
    def close(self):
        self.fd.close()
