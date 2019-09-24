# coding=utf8

from ctypes import *
from os.path import abspath, dirname
import time
import os
import binascii
import random
import struct


class IS13Exception(Exception):

    def __init__(self, err_str):
        super(IS13Exception, self).__init__()
        self.err_str = err_str

    def __str__(self):
        return self.err_str


class IS13(object):

    def __init__(self):
        dll_path = abspath(dirname(__file__)) + os.sep + "libEtcRsuDll.dll"
        self.dll = windll.LoadLibrary(dll_path)
        self.fd = c_void_p()  ###### void *
        self.buffer = create_string_buffer(2048)

    def open(self, com_num):
        ret = self.dll.Ex_OpenReader(com_num, pointer(self.fd))
        if ret != 0x2710:
            raise IS13Exception("open device return " + str(ret))

    def close(self):
        ret = self.dll.Ex_close_reader(self.fd)
        if ret != 0x10000:
            raise IS13Exception("open device return " + str(ret))
        self.fd = None
        return ret

    def beep(self):
        beep_times = 10
        beep_voice = 7 # 0x01 --> 0x07   
        self.dll.Ex_Audio_Control(self.fd, beep_times, beep_voice)

    def resetPsam(self, PSAMSlot, baud):
        ret = self.dll.Ex_SelectIcSlot(self.fd, PSAMSlot, baud, byref(self.buffer))
        if ret != 0x1B58:
            raise IS13Exception("resetPsam error! " + str(ret))
        return ret

    def psamExchangeApdu(self, sockId, apduList, apdu):
        apduHex = binascii.unhexlify(apdu)
        ret = self.dll.PSAM_CHANNEL_rq(self.fd, sockId, apduList, apduHex, 1000)
        apduListRet = c_int(0)
        ret = self.dll.PSAM_CHANNEL_rs(self.fd, sockId, byref(apduListRet), byref(self.buffer), 2000)        
        ret = []
        pos = 0
        for x in range(apduListRet.value):
            apduLen = ord(self.buffer[pos])
            pos += 1
            ret.append(binascii.hexlify(self.buffer[pos:apduLen+pos]))
            pos += apduLen
        return ret

    def psamIS13ExchangeApdu(self, PSAMSlot, baud, protocol, apdu):
        ret = self.dll.Ex_sam_command_hnew(self.fd, PSAMSlot, baud, protocol, apdu, byref(self.buffer))
        if (ret != 0x1B58):
            raise IS13Exception("recv hf card inventory response " + str(ret))
        temp = []
        pos = 0
        while True:
            if self.buffer[pos] == '\0':
                break
            pos += 1
        temp.append(self.buffer[:pos])
        return temp

    def hfInvent(self):
        tmp = 0
        ret = self.dll.Ex_OpenCard(self.fd)
        if(ret == 0x30001):
            tmp = ret
        elif (ret != 0x30000):
            raise IS13Exception("recv hf card inventory response " + str(ret))
        return tmp

    def hfclose(self):
        ret = self.dll.Ex_closecard(self.fd)
        if ret != 0x40000:
            raise IS13Exception("recv hf card close response " + str(ret))

    def hfExchangeApdu(self, apdu):
        ret = self.dll.Ex_pro_command_h(self.fd, apdu, self.buffer)
        if(ret != 0x2328):
            raise IS13Exception("recv cpu card  response " + str(ret))
        ret = []
        pos = 0
        while True:
            if self.buffer[pos] == '\0':
                break
            pos += 1
        ret.append(self.buffer[:pos])
        return ret

    def M1CardAuth(self, mode, addr, key):
        keyHex = binascii.unhexlify(key)
        ret = self.dll.M1_Card_Auth_rq(self.fd, mode, addr, keyHex, 500)
        if ret != 0:
            raise IS13Exception("M1 Card send Auth fail " + str(ret))
        ret = self.dll.M1_Card_Auth_rs(self.fd, 500)
        if ret != 0:
            raise IS13Exception("M1 Card rcv Auth fail " + str(ret))

    def M1CardRead(self, addr):
        self.dll.M1_Card_Read_rq(self.fd, addr, 500)
        ret = self.dll.M1_Card_Read_rs(self.fd, self.buffer, 500)
        if ret != 0:
            raise IS13Exception("M1 Card read fail " + str(ret))
        return binascii.hexlify(self.buffer.raw[0:16])


    def M1CardWrite(self, addr, data):
        dataHex = binascii.unhexlify(data)
        self.dll.M1_Card_Write_rq(self.fd, addr, dataHex, 500)
        ret = self.dll.M1_Card_Write_rs(self.fd, 500)
        if ret != 0:
            raise IS13Exception("M1 Card write fail " + str(ret))

    def M1CardInc(self, addr, count):
        self.dll.M1_Card_Inc_rq(self.fd, addr, count, 500)
        ret = self.dll.M1_Card_Inc_rs(self.fd, 500)
        if ret != 0:
            raise IS13Exception("M1 Card inc fail " + str(ret))

    def M1CardDec(self, addr, count):
        self.dll.M1_Card_Dec_rq(self.fd, addr, count, 500)
        ret = self.dll.M1_Card_Dec_rs(self.fd, 500)
        if ret != 0:
            raise IS13Exception("M1 Card dec fail " + str(ret))

    def MIreadCardId(self):
        self.dll.MI_Read_CardId_rq(self.fd, 1000)
        ret = self.dll.MI_Read_CardId_rs(self.fd, byref(self.buffer), 1000)
        if ret != 0:
            raise IS13Exception("MI read CardId fail" + str(ret))
        return binascii.hexlify(self.buffer.raw[0:4])

    def MISetEnterMode(self, cpcid):
        self.dll.MI_enterSet_rq(self.fd, 2000, binascii.unhexlify(cpcid))
        ret = self.dll.MI_enterSet_rs(self.fd, 2000, byref(self.buffer))
        if ret != 0:
            raise IS13Exception("MISetEnterMode fail" + str(ret))
        (p, ) = struct.unpack("H", self.buffer.raw[0:2])
        ret = {}
        power = 579*3.3/(p-10)
        ret["power"] = power 
        ret["status"] = ord(self.buffer.raw[2])
        return ret


    def MISetExitMode(self, cpcid):
        self.dll.MI_exitSet_rq(self.fd, 1000, binascii.unhexlify(cpcid))
        ret = self.dll.MI_exitSet_rs(self.fd, 1000, byref(self.buffer))
        if ret != 0:
            raise IS13Exception("MISetExitMode fail" + str(ret))
        ret = {}
        (p, ) = struct.unpack("H", self.buffer.raw[0:2])
        power = 579*3.3/(p-10)
        ret["power"] = power 
        ret["status"] = ord(self.buffer.raw[2])
        return ret

    def MIShowCardStatus(self, cpcid):
        self.dll.MI_Show_CardStatus_rq(self.fd, 1000, binascii.unhexlify(cpcid))
        ret = self.dll.MI_Show_CardStatus_rs(self.fd, 1000, byref(self.buffer))
        if ret != 0:
            raise IS13Exception("MIShowCardStatus fail" + str(ret))

        ret = {}
        (p, ) = struct.unpack("H", self.buffer.raw[0:2])
        power = 579*3.3/(p-10)
        ret["power"] = power
        if ord(self.buffer.raw[2]) == 2:
            ret["mode"] = "onRoad"
        else:
            ret["mode"] = "sleep"
        return ret

    def MIGetCardData(self, cpcid):
        self.dll.MI_Get_CardData_rq(self.fd, 1000, binascii.unhexlify(cpcid))
        ret = self.dll.MI_Get_CardData_rs(self.fd, 1000, byref(self.buffer))
        if ret != 0:
            raise IS13Exception("MIGetCardData fail" + str(ret))
        print binascii.hexlify(self.buffer.raw[0:10])
        ret = {}
        ret["crypto"] = binascii.hexlify(self.buffer.raw[0:8])
        routeNum = ord(self.buffer.raw[8])
        ret["route"] = []
        for x in range(routeNum):
            ret["route"].append(binascii.hexlify(self.buffer.raw[9+x*2:11+x*2]))
        return ret

    def MIBoradcastRoute(self, route):
        self.dll.SendRsu_Data_rq(self.fd, 1000, binascii.unhexlify(route))
        self.dll.MI_Get_CardData_rs(self.fd, 1000, byref(self.buffer))
        return



















    




    



