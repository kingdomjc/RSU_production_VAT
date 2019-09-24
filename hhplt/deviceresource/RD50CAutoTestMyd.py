# encoding=utf8

import binascii
import struct
import time
import zmq
from hhplt.deviceresource import TestResourceInitException
from hhplt.exception.device.DeviceProxyException import DeviceProxyException

class Enum(tuple):
    __getattr__ = tuple.index

device_type = Enum(["default", "FPGA", "EEPROM", "PLL", "EPLD"])
fpga_action = Enum(["default", "INIT", "READ", "WRITE", "READ_FRAME"])
pll_action = Enum(["default", "INIT", "READ", "WRITE"])
epld_action = Enum(["default", "INIT", "READ", "WRITE", "WRITE_FIFO"])
eeprom_action = Enum(["default", "INIT", "READ", "WRITE"])

class PCIEProxy(object):
    def __init__(self,initParam):
        self.ip = initParam
        self.initResource()

    def initResource(self):
        self.ctx = zmq.Context()
        self.s = self.ctx.socket(zmq.REQ)
        self.s.setsockopt(zmq.RCVTIMEO, 100)
        self.s.connect("tcp://%s:1100" % self.ip)

    def sendPcie(self):
        self.s.send(binascii.unhexlify("0084000008"))
        ack = self.s.recv()
        return binascii.hexlify(ack)

    def close(self):
        self.s.close()

class MACProxy(object):
    def __init__(self,initParam):
        self.ip = initParam
        self.ctx = zmq.Context()
        self.initResource()

    def initResource(self):
        self.s = self.ctx.socket(zmq.REQ)
        self.s.setsockopt(zmq.RCVTIMEO, 100)
        self.s.connect("tcp://%s:5100" % self.ip)

    def readEeprom(self, offset, read_len):
        write_cmd = struct.pack(
            "!IIII", device_type.EEPROM, eeprom_action.READ, offset, read_len)
        self.s.send(write_cmd, zmq.NOBLOCK, copy=False)
        event = self.s.poll(2000, zmq.POLLIN)
        rep = self.s.recv()
        status, get_len = struct.unpack("!II", rep[0:8])
        if status != 0:
            raise DeviceProxyException(
                "readEeprom fail! ret : %d" % status)
        return rep[8:(8 + get_len)]

    def close(self):
        self.s.close()

    def writeEeprom(self, offset, data):
        write_cmd = struct.pack(
            "!IIII", device_type.EEPROM, eeprom_action.WRITE, offset, len(data))
        write_cmd += data
        self.s.send(write_cmd, zmq.NOBLOCK, copy=False)
        rep = self.s.recv()
        status = struct.unpack("!I", rep)
        if status[0] != 0:
            raise DeviceProxyException(
                "writeEeprom fail! ret : %d" % status)



class RTCProxy(object):
    def __init__(self,initParam):
        self.device_type = Enum(
            ["default", "FPGA", "EEPROM", "PLL", "EPLD", "RTC", "TSENSOR", "PSAM", "RF_EEPROM", "RF_SENSOR", "SPI"])
        self.rtc_action = Enum(["default", "INIT", "READ", "SET"])
        self.ip = initParam
        self.ctx = zmq.Context()
        self.s = self.ctx.socket(zmq.REQ)
        self.initResource()

    def initResource(self):
        self.s.setsockopt(zmq.RCVTIMEO, 100)
        self.s.connect("tcp://%s:%d" % (self.ip, 5100))


    def rtc_init(self):
        write_cmd = struct.pack("!II", self.device_type.RTC, self.rtc_action.INIT)
        self.s.send(write_cmd, zmq.NOBLOCK, copy=False)
        event = self.s.poll(2000, zmq.POLLIN)
        rep = self.s.recv()
        return rep

    def rtc_set(self, year, mon, day, wday, hour, mins, sec):
        write_cmd = struct.pack(
            "!IIIIIIIII", self.device_type.RTC, self.rtc_action.SET, sec, mins, hour, day, mon, year, wday)
        self.s.send(write_cmd, zmq.NOBLOCK, copy=False)
        event = self.s.poll(2000, zmq.POLLIN)
        rep = self.s.recv()

    def rtc_read(self):
        write_cmd = struct.pack("!II", self.device_type.RTC, self.rtc_action.READ)
        self.s.send(write_cmd, zmq.NOBLOCK, copy=False)
        event = self.s.poll(2000, zmq.POLLIN)
        rep = self.s.recv()
        return rep

    def close(self):
        self.s.close()


class PsamProxy(object):
    def __init__(self,initParam):
        self.ip = initParam
        self.ctx = zmq.Context()
        self.socks = []
        for x in range(4):
            s = self.ctx.socket(zmq.REQ)
            self.socks.append(s)
        self.initResource()

    def initResource(self):
        try:
            for x in range(4):
                self.socks[x].connect("tcp://%s:%d" % (self.ip, 7000 + x))
        except:
            raise TestResourceInitException(u'链接设备失败')

    def active(self, slot):
        s = self.socks[slot]
        s.send("\xf8")
        ack = s.recv()
        return binascii.hexlify(ack)

    def exchangeApdu(self, slot, command):
        s = self.socks[slot]
        commandlen = chr(len(command)/2)
        s.send("\xf9" + commandlen + binascii.unhexlify(command))
        ack = s.recv()
        return binascii.hexlify(ack)

    def close(self):
        for s in self.socks:
            s.close()





class DeviceProxy(object):

    def __init__(self, initParam):
        self.ctx = zmq.Context()
        self.ipaddr = initParam
        self.initResource()
        # if ipaddr:
        #     self.req_socket = self.ctx.socket(zmq.REQ)
        #     self.req_socket.connect("tcp://%s:5100" % ipaddr)
        #     self.req_socket.setsockopt(zmq.LINGER, 0)
        #     self.req_socket.setsockopt(zmq.RCVTIMEO, 1000)

    def initResource(self):
        self.req_socket = self.ctx.socket(zmq.REQ)
        self.req_socket.connect("tcp://%s:5100" % self.ipaddr)
        self.req_socket.setsockopt(zmq.LINGER, 0)
        self.req_socket.setsockopt(zmq.RCVTIMEO, 1000)

    def close(self):
        self.req_socket.close()

    def _init_fpga(self):
        init_cmd = struct.pack("!II", device_type.FPGA, fpga_action.INIT)
        self.req_socket.send(init_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status = struct.unpack("!I", rep)
        return status[0]

    def _read_fpga_reg(self, offset):
        offset |= 0x80000
        read_cmd = struct.pack(
            "!III", device_type.FPGA, fpga_action.READ, offset)
        self.req_socket.send(read_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status, value = struct.unpack("!IH", rep)
        if 0 != status:
            raise DeviceProxyException("read fpga reg fail! ret : %d" % status)
        return value

    def _read_fpga_frame(self):
        read_cmd = struct.pack(
            "!II", device_type.FPGA, fpga_action.READ_FRAME)
        self.req_socket.send(read_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status, frame_len = struct.unpack("!II", rep[0:8])
        print status, frame_len
        if 0 != status:
            raise DeviceProxyException("read fpga reg fail! ret : %d" % status)
        return rep[8:]


    def _write_fpga_reg(self, offset, value):
        offset |= 0x80000
        write_cmd = struct.pack(
            "!IIIH", device_type.FPGA, fpga_action.WRITE, offset, value)
        self.req_socket.send(write_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status = struct.unpack("!I", rep)
        if status[0] != 0:
            raise DeviceProxyException(
                "write fpga reg fail! ret : %d" % status)

    def _write_fpga_frame(self, frame):
        pass

    def _init_pll(self):
        init_cmd = struct.pack(
            "!II", device_type.PLL, pll_action.INIT)
        self.req_socket.send(init_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status = struct.unpack("!I", rep)
        print status
        if status[0] != 0:
            raise DeviceProxyException("init pll reg fail %d \n" % status[0])

    def _write_pll_reg(self, offset, value):
        value_len = len(value)
        write_cmd = struct.pack(
            "!IIII", device_type.PLL, pll_action.WRITE, offset, value_len)
        for v in value:
            write_cmd += struct.pack("!B", v)
        self.req_socket.send(write_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status, length = struct.unpack("!II", rep[0:8])
        if status != 0:
            raise DeviceProxyException("write_pll_reg reg fail %d \n" % status)

    def _read_pll_reg(self, offset, length):
        read_cmd = struct.pack(
            "!IIII", device_type.PLL, pll_action.READ, offset, length)
        self.req_socket.send(read_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status, length = struct.unpack("!II", rep[0:8])
        if status != 0:
            raise DeviceProxyException("read pll reg fail %d \n" % status)
        print "len is ", len(rep[8:])
        unpack_string = "!" + "B" * length
        reg_value = struct.unpack(unpack_string, rep[8:])
        return reg_value

    def _init_epld(self):
        init_cmd = struct.pack("!II", device_type.EPLD, epld_action.INIT)
        self.req_socket.send(init_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status = struct.unpack("!I", rep)
        if status[0] != 0:
            raise DeviceProxyException("init epld fail %d " % status[0])

    def _read_epld(self, offset):
        read_cmd = struct.pack(
            "!III", device_type.EPLD, epld_action.READ, offset)
        self.req_socket.send(read_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status, value = struct.unpack("!IH", rep)
        if 0 != status:
            raise DeviceProxyException("read epld reg fail! ret : %d" % status)
        return value

    def _write_epld(self, offset, value):
        write_cmd = struct.pack(
            "!IIIH", device_type.EPLD, epld_action.WRITE, offset, value)
        self.req_socket.send(write_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status = struct.unpack("!I", rep)
        if status[0] != 0:
            raise DeviceProxyException(
                "write epld reg fail! ret : %d" % status)

    def _write_epld_fifo(self, offset, value_str):
        str_len = len(value_str)
        write_cmd = struct.pack(
            "!IIII", device_type.EPLD, epld_action.WRITE_FIFO, offset, str_len)
        write_cmd += value_str
        self.req_socket.send(write_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status = struct.unpack("!I", rep)
        if status[0] != 0:
            raise DeviceProxyException(
                "write epld reg fail! ret : %d" % status)

    def _load_fpga(self, fpga_path):
        download_ctl = self._read_epld(0x92 * 2)
        download_ctl &= 0xfffffffe
        self._write_epld(0x92 * 2, download_ctl)

        cnt = 0
        while cnt < 1000:
            config_done = self._read_epld(0x92 * 2)
            config_done &= 0x4
            if config_done == 0:
                break
            cnt += 1
        if cnt == 1000:
            raise DeviceProxyException("load fpga fail at first step")

        time.sleep(0.1)

        download_ctl = self._read_epld(0x92 * 2)
        download_ctl |= 0x01
        self._write_epld(0x92 * 2, download_ctl)

        cnt = 0
        while cnt < 1000:
            config_done = self._read_epld(0x92 * 2)
            config_done &= 0x2
            if config_done == 0x2:
                break
            cnt += 1

        if cnt == 1000:
            raise DeviceProxyException("load fpga fail at second step")

        time.sleep(0.1)

        file_fd = open(fpga_path, "rb")
        file_content = file_fd.read()
        file_content += "\x00"
        total_len = len(file_content)
        sect_cnts = total_len / 8000
        tail_len = total_len % 8000

        for x in range(sect_cnts):
            self._write_epld_fifo(
                0x94 * 2, file_content[(x * 8000):(x * 8000 + 8000)])
        if tail_len != 0:
            self._write_epld_fifo(0x94 * 2, file_content[-tail_len:])

        self._write_epld(0x144,  0)
        time.sleep(0.1)
        self._write_epld(0x144,  1)
        file_fd.close()

