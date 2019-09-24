#encoding:utf-8
'''
Created on 2014-11-8

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
import os
os.chdir("../")

def __toBytesarray(hexStr):
    '''从HEX符号转换成bytearray'''
    return bytearray([int(hexStr[i]+hexStr[i+1],16) for i in range(0,len(hexStr),2)])

password = "hhplt/productsuite/gs10/versions/obu-vat.txt"

sc = GS10PlateDevice({"serialPortName":"com3","cableComsuption":1})
sc.initResource()
#        obuid = sc.read_obu_id(password)

while True:
    try:
        towrite = "04000206"
        sc.bslDevice.startBslWriting(password)
        sc.bslDevice.bslWriteData([[0x1908,__toBytesarray(towrite)]])
    except Exception,e:
        print e
    finally:
        sc.bslDevice.finishBslWritten()
    a = raw_input(u"回车键继续")
    if a =='exit':
        break
sc.retrive()
    





