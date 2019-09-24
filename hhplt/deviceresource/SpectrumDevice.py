#encoding:utf-8
'''
频谱仪设备资源
'''
from hhplt.deviceresource import TestResource,AbortTestException

from ctypes import *
from msp430.bsl5.uart import *
from msp430.bsl5 import bsl5
import os

class SpectrumDevice(TestResource):
    def __init__(self):
        self.wdll = windll.LoadLibrary("dlls/visa32.dll")
        self.dll = cdll.LoadLibrary("dlls/visa32.dll")

    def open(self):
        self.defaultRM = c_int(0)
        self.N9020A = c_int(0)
        self.power = c_int(0)
        self.wdll.viOpenDefaultRM(byref(self.defaultRM))
        ret = self.wdll.viOpen(self.defaultRM, "TCPIP0::A-N9020A-20500.local.::5025::SOCKET", 0, 0, byref(self.N9020A))
        if 0 != ret:
            return False
        self.dll.viPrintf((self.N9020A), "*RST\n")
        self.dll.viPrintf((self.N9020A), ":CAL:AUTO ON\n")
        self.dll.viPrintf((self.N9020A), ":CAL:AUTO:MODE NRF\n")
        self.dll.viPrintf((self.N9020A), "*CLS;*WAI;\n")
        self.dll.viPrintf((self.N9020A), "*RST;*WAI;\n")
        self.dll.viPrintf((self.N9020A), ":INST:SEL SA\n")
        self.dll.viPrintf((self.N9020A), "BAND 2000000\n")
        self.dll.viPrintf((self.N9020A), ":SENS:FREQ:CENT 5840000000\n")
        self.dll.viPrintf((self.N9020A), ":SENS:FREQ:SPAN 10000000\n")
        self.dll.viPrintf((self.N9020A), "CALC:MARK:STAT ON\n")
        self.dll.viPrintf((self.N9020A), "CALC:MARK1:MAX\n")
        self.dll.viQueryf((self.N9020A), ":SENS:ACP:FREQ:SPAN\n", "%dMHz", byref(self.power))
        return True
    
    def close(self):
        self.wdll.viClose(self.N9020A)
        self.wdll.viClose(self.defaultRM)

