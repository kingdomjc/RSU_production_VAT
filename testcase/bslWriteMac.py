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

password = "hhplt/productsuite/gs10/versions/obu-formal.txt"

sc = GS10PlateDevice({"serialPortName":"com3","cableComsuption":1})
sc.initResource()

def save(info):
    txt = open("info.txt","a")
    for seg in info:
        segStr = "".join(["%.2x"%seg[i] for i in range(len(seg))])
        txt.write(segStr);
        txt.write('\r\n');
        print segStr
    txt.write('\r\n');
    txt.close()

while True:
    try:
        towrite = "24"
        
        sc.bslDevice.startBslWriting(password)
        sc.bslDevice.bslWriteData([[0x1884,__toBytesarray(towrite)]])
        save(sc.bslDevice.readWholeInfo())
    except Exception,e:
        print e
    finally:
        sc.bslDevice.finishBslWritten()
        
    a = raw_input(u"回车键继续")
    if a =='exit':
        break
sc.retrive()
    





