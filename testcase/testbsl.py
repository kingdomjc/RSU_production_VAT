#encoding:utf-8
'''
Created on 2014-10-9
试试BSL的东西
@author: user
'''

import os
import serial
import time
from msp430.bsl5.uart import *
from msp430.bsl5 import bsl5
from msp430 import memory
import sys

from hhplt.deviceresource.GS10PlateDevice import GS10PlateDevice



#file = "../hhplt/productsuite/gs10/versions/gs10_formal.txt"
psdFile = "obu-vat.txt"
print os.getcwd()
print os.path.exists(psdFile)

#download_data = memory.Memory() # prepare downloaded data        
#data = memory.load(file)
#download_data.merge(data)


g = GS10PlateDevice({"serialPortName":"com3"})
#------------------- 读MAC ---------------
#obuid = g.read_obu_id(None)
obuid = g.read_obu_id("../hhplt/productsuite/gs10/versions/obu-vat.txt")
print "MAC地址是:","".join(["%.2X"%i for i in obuid])

#------------------- 下版本  ---------------
#versionFile = "../hhplt/productsuite/gs10/versions/obu-vat.txt"
#g.downloadVersion(version_file = versionFile)

#------------------ 写MAC ----------------
#mac="F40055D9"
#macBytes =  bytearray([int(mac[i]+mac[i+1],16) for i in range(0,len(mac),2)])
#g.save_obu_id("../hhplt/productsuite/gs10/versions/obu-vat.txt",macBytes)
#g.save_obu_id(None,macBytes)

##------------------- 读MAC ---------------
#obuid = g.read_obu_id("../hhplt/productsuite/gs10/versions/obu-vat.txt")
#print "MAC地址是:","".join(["%.2X"%i for i in obuid])





