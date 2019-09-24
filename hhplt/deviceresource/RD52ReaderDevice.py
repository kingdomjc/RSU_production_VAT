#encoding:utf-8
'''
Created on 2019-2-25

RSU52 阅读器

@author: 刘琪
'''
import zmq
import time
import struct
from hhplt.testengine.server import serverParam as SP
from hhplt.deviceresource import TestResource

from threading import Thread,RLock
from hhplt.deviceresource import askForResource
from hhplt.testengine.autoTrigger import AbstractAutoTrigger
from hhplt.parameters import PARAM
from hhplt.util.Enum import Enum
from hhplt.exception.device.DeviceProxyException import DeviceProxyException

device_type = Enum(["default", "FPGA", "EEPROM", "PLL", "EPLD", "RTC", "SENSOR"])
fpga_action = Enum(["default", "INIT", "READ", "WRITE"])
pll_action = Enum(["default", "INIT", "READ", "WRITE"])
epld_action = Enum(["default", "INIT", "READ", "WRITE", "WRITE_FIFO"])
sensor_action = Enum(["default", "INIT", "SET_LOCAL_TEMPER", "SET_REMOTE_TEMPER", "GET_LOCAL_PARA_TEMPER",
                      "GET_REMOTE_PARA_TEMPER","GET_LOCAL_TEMPER", "GET_REMOTE_TEMPER", "GET_STATUS"])

class RD52ReaderDevice(TestResource):
    def __init__(self, param=None):
        self.ctx = zmq.Context()
        if param:
            self.req_socket = self.ctx.socket(zmq.REQ)
            self.req_socket.connect("tcp://%s:%d" % (param["ipaddr"],param["post"]))
            self.req_socket.setsockopt(zmq.LINGER, 0)
            self.req_socket.setsockopt(zmq.RCVTIMEO, 1000)
    def open(self, ipaddr,post):
        self.req_socket = self.ctx.socket(zmq.REQ)
        self.req_socket.connect("tcp://%s:%d" % (ipaddr,post))
        self.req_socket.setsockopt(zmq.LINGER, 0)
        self.req_socket.setsockopt(zmq.RCVTIMEO, 1000)

    def close(self):
        self.req_socket.close()

    def retrive(self):
        self.close()

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

    def _read_fpga_frame(self):
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
        #print "len is ", len(rep[8:])
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

    def _init_sensor(self):
        init_cmd = struct.pack("!II", device_type.SENSOR, sensor_action.INIT)
        self.req_socket.send(init_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status = struct.unpack("!I", rep)
        if status[0] != 0:
            raise DeviceProxyException("init sensor fail %d " %status)

    def _set_local_temper(self, low, high):
        read_cmd = struct.pack(
            "!iiii", device_type.SENSOR, sensor_action.SET_LOCAL_TEMPER, low, high)
        self.req_socket.send(read_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status = struct.unpack("!I", rep)
        if 0 != status[0]:
            raise DeviceProxyException("set local limit fail! ret : %d" %status)

    def _set_remote_temper(self, low, high):
        read_cmd = struct.pack(
            "!iiii", device_type.SENSOR, sensor_action.SET_REMOTE_TEMPER, low, high)
        self.req_socket.send(read_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status = struct.unpack("!I", rep)
        if 0 != status[0]:
            raise DeviceProxyException("set remote limit fail! ret : %d" %status)

    def _get_local_temper_para(self):
        read_cmd = struct.pack(
            "!II", device_type.SENSOR, sensor_action.GET_LOCAL_PARA_TEMPER)
        self.req_socket.send(read_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status,low,high = struct.unpack("!Iii", rep)
        if 0 != status:
            raise DeviceProxyException("get local temper para fail! ret : %d" %status)
        return low,high


    def _get_remote_temper_para(self):
        read_cmd = struct.pack(
            "!II", device_type.SENSOR, sensor_action.GET_REMOTE_PARA_TEMPER)
        self.req_socket.send(read_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status,low,high = struct.unpack("!Iii", rep)
        if 0 != status:
            raise DeviceProxyException("get remote temper para fail! ret : %d" %status)
        return low,high

    def _get_local_temper(self):
        read_cmd = struct.pack(
            "!II", device_type.SENSOR, sensor_action.GET_LOCAL_TEMPER)
        self.req_socket.send(read_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status,value = struct.unpack("!Ii", rep)
        if 0 != status:
            raise DeviceProxyException("get local temper fail! ret : %d" %status)
        return value

    def _get_remote_temper(self):
        read_cmd = struct.pack(
            "!II", device_type.SENSOR, sensor_action.GET_REMOTE_TEMPER)
        self.req_socket.send(read_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status,value = struct.unpack("!Ii", rep)
        if 0 != status:
            raise DeviceProxyException("get remote temper fail! ret : %d" %status)
        return value

    def _get_status(self):
        read_cmd = struct.pack(
            "!II", device_type.SENSOR, sensor_action.GET_STATUS)
        self.req_socket.send(read_cmd, zmq.NOBLOCK, copy=False)
        rep = self.req_socket.recv()
        status,value = struct.unpack("!II", rep)
        if 0 != status:
            raise DeviceProxyException("get sensor status fail! ret : %d" %status)
        return value

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

    def fpga_pll_config(self):
        pll_reg_map = [0x01, 0x00, 0xb4, 0x04, 0x02, 0x50, 0x0e,
                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        pll_reg_map1 = [0x00, 0x00, 0x00, 0x00, 0x4d, 0x02, 0x05,
                        0x00, 0x80, 0x02, 0x1b, 0x2a, 0x00, 0x40, 0x02]
        pll_reg_map2 = [0x00, 0x00, 0x00, 0x00, 0x6d, 0x02, 0x05,
                        0x05, 0xf3, 0xcc, 0x33, 0xcb, 0x00, 0x40, 0x02]
        self._write_pll_reg(0, pll_reg_map)
        self._write_pll_reg(16, pll_reg_map1)
        self._write_pll_reg(32, pll_reg_map2)
class TxPll(object):
    def __init__(self, proxy=None):
        self.proxy = proxy

    def _write_and_trig(self, value):
        self.proxy._write_fpga_reg(0x54, value)
        self.proxy._write_fpga_reg(0x55, 0x0000)
        self.proxy._write_fpga_reg(0x55, 0x0001)
        self.proxy._write_fpga_reg(0x55, 0x0000)

    def config(self, channel):
        if channel == 5830:
            #print "channel freq is %d " % 5830
            self._write_and_trig(0x0204)
            self._write_and_trig(0x0404)
            # self._write_and_trig(0x063e)
            self._write_and_trig(0x1030)
            self._write_and_trig(0x084d)
            self._write_and_trig(0x0a11)
            self._write_and_trig(0x0c08)
            self._write_and_trig(0x0e91)
            # self._write_and_trig(0x1030)
            self._write_and_trig(0x063e)
            self._write_and_trig(0x1200)
            self._write_and_trig(0x1400)
            self._write_and_trig(0x16b9)
            self._write_and_trig(0x180d)
            self._write_and_trig(0x1ac0)
        else:  # 5840
            #print "channel freq is %d " % 5840
            # proxy._write_fpga_reg(0x5c,01)
            self._write_and_trig(0x0204)
            self._write_and_trig(0x0404)
            self._write_and_trig(0x063f)
            # self._write_and_trig(0x1000)
            self._write_and_trig(0x084d)
            self._write_and_trig(0x0a11)
            self._write_and_trig(0x0c08)
            self._write_and_trig(0x0e92)
            self._write_and_trig(0x1000)
            # self._write_and_trig(0x063f)
            self._write_and_trig(0x1200)
            self._write_and_trig(0x1400)
            self._write_and_trig(0x16b9)
            self._write_and_trig(0x180d)
            self._write_and_trig(0x1ac0)
            # proxy._write_fpga_reg(0x5c,0x0001)

    def is_lock(self):
        if self.proxy._read_fpga_reg(0x34) == 1:
            return True
        else:
            return False

class RxPll(object):
    def __init__(self, proxy=None):
        self.proxy = proxy
    def _write_and_trig(self, value):
        self.proxy._write_fpga_reg(0x54, value)
        self.proxy._write_fpga_reg(0x55, 0x0000)
        self.proxy._write_fpga_reg(0x55, 0x0001)
        self.proxy._write_fpga_reg(0x55, 0x0000)

    def config(self, channel):
        if channel == 5720:
            print "channel freq is %d " % 5720
            self.proxy._write_and_trig(0x0204)
            self.proxy._write_and_trig(0x0404)
            # self._write_and_trig(0x063f)
            self.proxy._write_and_trig(0x063e)
            self.proxy._write_and_trig(0x084d)
            self.proxy._write_and_trig(0x0a11)
            self.proxy._write_and_trig(0x0c08)
            self.proxy._write_and_trig(0x0e8f)
            # self._write_and_trig(0x1000)
            # self._write_and_trig(0x1200)
            # self._write_and_trig(0x1400)
            self.proxy._write_and_trig(0x1003)
            self.proxy._write_and_trig(0x1233)
            self.proxy._write_and_trig(0x1430)
            self.proxy._write_and_trig(0x16b9)
            self.proxy._write_and_trig(0x180d)
            self.proxy._write_and_trig(0x1ac0)
        else:
            print "channel freq is %d " % 5730
            self.proxy._write_and_trig(0x0204)
            self.proxy._write_and_trig(0x0404)
            self.proxy._write_and_trig(0x063e)
            self.proxy._write_and_trig(0x084d)
            self.proxy._write_and_trig(0x0a11)
            self.proxy._write_and_trig(0x0c08)
            self.proxy._write_and_trig(0x0e8f)
            # self._write_and_trig(0x0e90)
            # self._write_and_trig(0x1010)
            # self._write_and_trig(0x1020)
            self.proxy._write_and_trig(0x1013)
            # self._write_and_trig(0x1200)
            self.proxy._write_and_trig(0x1233)
            # self._write_and_trig(0x1400)
            self.proxy._write_and_trig(0x1430)
            self.proxy._write_and_trig(0x16b9)
            self.proxy._write_and_trig(0x180d)
            self.proxy._write_and_trig(0x1ac0)

            # chang Freq 5722~5724MHz
            # self._write_and_trig(0x063e)
            # self._write_and_trig(0x1003)
            # self._write_and_trig(0x1233)
            # self._write_and_trig(0x1430)

    def config_pn9(self, channel):
        if channel == 5720:
            print "channel freq is %d " % 5720
            self.proxy._write_and_trig(0x0204)
            self.proxy._write_and_trig(0x0406)
            self.proxy._write_and_trig(0x063f)
            self.proxy._write_and_trig(0x084d)
            self.proxy._write_and_trig(0x0a11)
            self.proxy._write_and_trig(0x0c08)
            self.proxy._write_and_trig(0x0e8f)
            self.proxy._write_and_trig(0x1000)
            self.proxy._write_and_trig(0x1200)
            self.proxy._write_and_trig(0x1400)
            self.proxy._write_and_trig(0x16b9)
            # self._write_and_trig(0x16a1)
            self.proxy._write_and_trig(0x180d)
            self.proxy._write_and_trig(0x1ac0)
        else:
            print "channel freq is %d " % 5730
            self.proxy._write_and_trig(0x0204)
            self.proxy._write_and_trig(0x0406)
            self.proxy._write_and_trig(0x063e)
            self.proxy._write_and_trig(0x084d)
            self.proxy._write_and_trig(0x0a11)
            self.proxy._write_and_trig(0x0c08)
            self.proxy._write_and_trig(0x0e8f)
            self.proxy._write_and_trig(0x1010)
            self.proxy._write_and_trig(0x1200)
            self.proxy._write_and_trig(0x1400)
            self.proxy._write_and_trig(0x16b9)
            # self._write_and_trig(0x16a1)
            self.proxy._write_and_trig(0x180d)
            self.proxy._write_and_trig(0x1ac0)

    def is_lock(self):
        if self.proxy._read_fpga_reg(0xf4) == 1:
            return True
        else:
            return False
class MacCtrl(object):
    def __init__(self, proxy=None):
        self.proxy = proxy
    def send_test_frame(self, num, flag):
        self.proxy._write_fpga_reg(0x20, 0x0003) #FORWARD_FILT_EN
        self.proxy._write_fpga_reg(0x21, 0x7ffe) #FORWARD_PWADJ
        self.proxy._write_fpga_reg(0x22, 0x47e) #ask_high_val max:1f00
        self.proxy._write_fpga_reg(0x23, 0x7d0) #ask_low_val
        self.proxy._write_fpga_reg(0x24, 0x7d0) #ask_no_val
        self.proxy._write_fpga_reg(0x0e, 0x0003) #wake signal guard 0.5ms
        self.proxy._write_fpga_reg(0x44, 0x0005) #resend interval 20ms
        # self.proxy._write_fpga_reg(0x56, 0x0024)
        # self.proxy._write_fpga_reg(0x57, 0x0000)
        # self.proxy._write_fpga_reg(0x57, 0x0001)
        # self.proxy._write_fpga_reg(0x57, 0x0000)
        self.proxy._write_fpga_reg(0x45, num) #resend cnt
        self.proxy._write_fpga_reg(0x46, 0x0000) #
        '''
        proxy._write_fpga_reg(0x200, 0x0009)
        proxy._write_fpga_reg(0x201, 0x0200)
        proxy._write_fpga_reg(0x202, 0x7740)
        proxy._write_fpga_reg(0x203, 0x0599)
        proxy._write_fpga_reg(0x204, 0x0001)
        proxy._write_fpga_reg(0x205, 0x8014)
        proxy._write_fpga_reg(0x206, 0x0001)
        proxy._write_fpga_reg(0x207, 0x1000)
        proxy._write_fpga_reg(0x208, 0xca79)
        proxy._write_fpga_reg(0x209, 0xb25f)
        proxy._write_fpga_reg(0x20a, 0xcaa3)
        proxy._write_fpga_reg(0x20b, 0xf0fb)
        proxy._write_fpga_reg(0x20c, 0x0000)
        proxy._write_fpga_reg(0x20d, 0xb673)
        '''
        self.proxy._write_fpga_reg(0x200, 0xffff)
        self.proxy._write_fpga_reg(0x201, 0xffff)
        self.proxy._write_fpga_reg(0x202, 0x0350)
        self.proxy._write_fpga_reg(0x203, 0xc091)
        self.proxy._write_fpga_reg(0x204, 0x0009)
        self.proxy._write_fpga_reg(0x205, 0x9103)
        self.proxy._write_fpga_reg(0x206, 0x7b38)
        self.proxy._write_fpga_reg(0x207, 0x5359)
        self.proxy._write_fpga_reg(0x208, 0x0100)
        self.proxy._write_fpga_reg(0x209, 0x8141)
        self.proxy._write_fpga_reg(0x20a, 0xb129)
        self.proxy._write_fpga_reg(0x20b, 0x001a)
        self.proxy._write_fpga_reg(0x20c, 0x0000)
        self.proxy._write_fpga_reg(0x20d, 0x0000)
        self.proxy._write_fpga_reg(0x20e, 0x0000)
        self.proxy._write_fpga_reg(0x20f, 0x1913)
        self.proxy._write_fpga_reg(0x08, 0x0020)
        self.proxy._write_fpga_reg(0x09, 0x0000)
        time.sleep(0.1)
        if 1 == flag:
            self.proxy._write_fpga_reg(0x09, 0x0003)
            self.proxy._write_fpga_reg(0x23, 0x7d0) #ask_low_val
            self.proxy._write_fpga_reg(0x24, 0x7d0) #ask_no_val
            self.proxy._write_fpga_reg(0x0e, 0x0003) #wake signal guard 0.5ms
            self.proxy._write_fpga_reg(0x44, 0x003f) #resend interval 5ms
            self.proxy._write_fpga_reg(0x56, 0x0027)
            self.proxy._write_fpga_reg(0x57, 0x0000)
            self.proxy._write_fpga_reg(0x57, 0x0001)
            self.proxy._write_fpga_reg(0x57, 0x0000)
        else:
            self.proxy._write_fpga_reg(0x09, 0x0003)